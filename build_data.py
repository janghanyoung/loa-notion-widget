import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import quote

import requests


TIMEZONE = ZoneInfo("Asia/Seoul")

API_URL_PROFILE = "https://developer-lostark.game.onstove.com/characters/{name}/profiles"
API_URL_CALENDAR = "https://developer-lostark.game.onstove.com/gamecontents/calendar"


def safe_str(value, fallback="-") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def get_api_key() -> str:
    api_key = os.environ.get("LOA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("LOA_API_KEY 환경 변수가 비어 있습니다.")
    return api_key


def get_headers(api_key: str) -> dict:
    return {
        "Authorization": f"bearer {api_key}",
        "Accept": "application/json"
    }


def load_config() -> dict:
    path = Path("config.json")
    if not path.exists():
        raise RuntimeError("config.json 파일이 없습니다.")
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_profile(api_key: str, character_name: str) -> dict:
    encoded_name = quote(character_name)
    url = API_URL_PROFILE.format(name=encoded_name)

    response = requests.get(url, headers=get_headers(api_key), timeout=20)

    if response.status_code != 200:
        raise RuntimeError(
            f"캐릭터 프로필 API 실패: HTTP {response.status_code} / "
            f"캐릭터명={character_name} / 응답={response.text[:500]}"
        )

    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError(f"캐릭터 프로필 응답 형식 오류: {type(data)}")

    return data


def fetch_calendar(api_key: str) -> list:
    response = requests.get(API_URL_CALENDAR, headers=get_headers(api_key), timeout=20)

    if response.status_code != 200:
        raise RuntimeError(
            f"캘린더 API 실패: HTTP {response.status_code} / 응답={response.text[:500]}"
        )

    data = response.json()

    if not isinstance(data, list):
        raise RuntimeError(f"캘린더 응답 형식 오류: {type(data)}")

    return data


def unique_keep_order(items: list[str]) -> list[str]:
    seen = set()
    result = []

    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)

    return result


def parse_today_islands(calendar_data: list, today_str: str) -> list[str]:
    islands = []

    for item in calendar_data:
        start_times = item.get("StartTimes") or []
        if not isinstance(start_times, list):
            continue

        is_today = any(today_str in str(start_time) for start_time in start_times)
        if not is_today:
            continue

        name = safe_str(item.get("ContentsName"), "")
        if not name:
            continue

        if "섬" in name:
            islands.append(name)

    return unique_keep_order(islands)


def extract_stat_map(profile: dict) -> dict:
    result = {}
    stats = profile.get("Stats") or []

    if not isinstance(stats, list):
        return result

    for item in stats:
        stat_type = safe_str(item.get("Type"), "")
        stat_value = safe_str(item.get("Value"), "")
        if stat_type:
            result[stat_type] = stat_value

    return result


def extract_equipment_summary(profile: dict) -> dict:
    equipment = profile.get("Equipment") or []

    result = {
        "weapon": "-",
        "armor": "-",
        "accessory": "-"
    }

    if not isinstance(equipment, list):
        return result

    armor_count = 0
    accessory_count = 0

    for item in equipment:
        item_type = safe_str(item.get("Type"), "")
        item_name = safe_str(item.get("Name"), "-")

        if "무기" in item_type:
            result["weapon"] = item_name
        elif item_type in ["투구", "상의", "하의", "장갑", "어깨"]:
            armor_count += 1
        elif item_type in ["목걸이", "귀걸이", "반지", "어빌리티 스톤", "팔찌"]:
            accessory_count += 1

    if armor_count:
        result["armor"] = f"{armor_count}부위 장착"
    if accessory_count:
        result["accessory"] = f"{accessory_count}개 장착"

    return result


def build_profile_stats(profile: dict) -> list[dict]:
    stat_map = extract_stat_map(profile)

    return [
        {"label": "아이템 레벨", "value": safe_str(profile.get("ItemAvgLevel"))},
        {"label": "전투 레벨", "value": safe_str(profile.get("CharacterLevel"))},
        {"label": "원정대 레벨", "value": safe_str(profile.get("ExpeditionLevel"))},
        {"label": "PVP 등급", "value": safe_str(profile.get("PvpGradeName"))},
        {"label": "공격력", "value": stat_map.get("공격력", "-")},
        {"label": "최대 생명력", "value": stat_map.get("최대 생명력", "-")},
        {"label": "치명", "value": stat_map.get("치명", "-")},
        {"label": "특화", "value": stat_map.get("특화", "-")},
        {"label": "제압", "value": stat_map.get("제압", "-")},
        {"label": "신속", "value": stat_map.get("신속", "-")},
        {"label": "인내", "value": stat_map.get("인내", "-")},
        {"label": "숙련", "value": stat_map.get("숙련", "-")}
    ]


def build_equipment_stats(profile: dict) -> list[dict]:
    stat_map = extract_stat_map(profile)
    equipment = extract_equipment_summary(profile)

    return [
        {"label": "직업", "value": safe_str(profile.get("CharacterClassName"))},
        {"label": "서버", "value": safe_str(profile.get("ServerName"))},
        {"label": "길드", "value": safe_str(profile.get("GuildName"))},
        {"label": "칭호", "value": safe_str(profile.get("Title"))},
        {"label": "무기", "value": equipment["weapon"]},
        {"label": "방어구", "value": equipment["armor"]},
        {"label": "장신구", "value": equipment["accessory"]},
        {"label": "투력", "value": stat_map.get("공격력", "-")},
        {"label": "아크 그리드", "value": "-"},
        {"label": "보석", "value": "-"},
        {"label": "카드", "value": "-"},
        {"label": "아크 패시브", "value": "-"}
    ]


def build_meta(now: datetime, config: dict) -> tuple[str, str, str]:
    weekday_en = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][now.weekday()]
    weekday_ko = "월화수목금토일"[now.weekday()]

    meta_left = f"VOL. {now.strftime('%Y-%m-%d')} {weekday_en}"
    meta_center = safe_str(config.get("metaCenter"), "발행처 | 아크라시아 연합 정보국")
    meta_right = f"발행일 | {now.strftime('%Y.%m.%d')} ({weekday_ko})"

    return meta_left, meta_center, meta_right


def build_error_payload(error: Exception) -> dict:
    now = datetime.now(TIMEZONE)
    error_text = str(error)

    return {
        "paperTitle": "예스이호이테 일보",
        "metaLeft": f"VOL. {now.strftime('%Y-%m-%d')} ERROR",
        "metaCenter": "발행처 | 오류 상태",
        "metaRight": f"발행일 | {now.strftime('%Y.%m.%d')}",
        "mainHeadline": "오늘의 신문을 정상적으로 불러오지 못했습니다.",
        "sideHeadline": "[속보] 데이터 로딩 실패",
        "character": {
            "image": "https://placehold.co/420x560?text=ERROR",
            "nameplate": "오류 상태",
            "subplate": error_text
        },
        "profileStats": [
            {"label": "ERROR", "value": error_text}
        ],
        "equipmentStats": [
            {"label": "확인 1", "value": "LOA_API_KEY Secret 이름"},
            {"label": "확인 2", "value": "config.json characterName"},
            {"label": "확인 3", "value": "GitHub Actions 로그"},
            {"label": "확인 4", "value": "캐릭터명 URL 인코딩 여부"}
        ],
        "lookbook": [],
        "islandArticle": {
            "image": "https://placehold.co/520x260?text=ERROR",
            "todayIslands": [
                error_text
            ],
            "remainingRaids": [
                "Actions 로그에서 daily.json 생성 단계 확인"
            ],
            "quote": error_text
        },
        "market": {
            "island": [
                "오류 발생",
                error_text
            ],
            "events": [
                "LOA_API_KEY / characterName / API 응답 확인"
            ],
            "guild": [
                "config.json과 update.yml을 확인하세요"
            ]
        }
    }


def build_payload() -> dict:
    now = datetime.now(TIMEZONE)
    today_str = now.strftime("%Y-%m-%d")

    api_key = get_api_key()
    config = load_config()

    character_name = safe_str(config.get("characterName"), "")
    if not character_name:
        raise RuntimeError("config.json의 characterName이 비어 있습니다.")

    paper_title = safe_str(config.get("paperTitle"), "예스이호이테 일보")

    profile = fetch_profile(api_key, character_name)
    calendar = fetch_calendar(api_key)
    islands = parse_today_islands(calendar, today_str)

    meta_left, meta_center, meta_right = build_meta(now, config)

    actual_name = safe_str(profile.get("CharacterName"), character_name)
    server = safe_str(profile.get("ServerName"))
    class_name = safe_str(profile.get("CharacterClassName"))
    level = safe_str(profile.get("CharacterLevel"))

    return {
        "paperTitle": paper_title,
        "metaLeft": meta_left,
        "metaCenter": meta_center,
        "metaRight": meta_right,
        "mainHeadline": f"이제 칭호도 스타일이다! 대신 {actual_name}",
        "sideHeadline": "[단독] 식목일 맞이! 오늘의 모험섬 핫이슈",
        "character": {
            "image": safe_str(config.get("characterImage"), "https://placehold.co/420x560?text=Character"),
            "nameplate": actual_name,
            "subplate": f"{server} | {class_name} | Lv.{level}"
        },
        "profileStats": build_profile_stats(profile),
        "equipmentStats": build_equipment_stats(profile),
        "lookbook": config.get("lookbook", []),
        "islandArticle": {
            "image": safe_str(config.get("islandImage"), "https://placehold.co/520x260?text=Island"),
            "todayIslands": islands if islands else ["오늘 표시된 모험섬 없음"],
            "remainingRaids": config.get("remainingRaids", []),
            "quote": "모험은 아직 끝나지 않았다.\n아직 가보지 않은 곳이\n아크라시아의 절반이다."
        },
        "market": {
            "island": config.get("marketIslandNews", []),
            "events": config.get("marketEventNews", []),
            "guild": config.get("guildAdNews", [])
        }
    }


def main() -> None:
    try:
        payload = build_payload()
    except Exception as error:
        payload = build_error_payload(error)

    output_path = Path("daily.json")
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"saved: {output_path.resolve()}")
    print(f"headline: {payload.get('mainHeadline')}")
    print(f"character: {payload.get('character', {}).get('nameplate')}")
    print(f"subplate: {payload.get('character', {}).get('subplate')}")


if __name__ == "__main__":
    main()
