import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


TIMEZONE = ZoneInfo("Asia/Seoul")

API_URL_PROFILE = "https://developer-lostark.game.onstove.com/characters/{name}/profiles"
API_URL_CALENDAR = "https://developer-lostark.game.onstove.com/gamecontents/calendar"


def get_api_key() -> str:
    api_key = os.environ.get("LOA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("LOA_API_KEY 환경 변수가 비어 있습니다.")
    return api_key


def get_headers(api_key: str) -> dict:
    return {
        "Authorization": f"bearer {api_key}",
        "Accept": "application/json",
    }


def load_config() -> dict:
    config_path = Path("config.json")
    if not config_path.exists():
        raise RuntimeError("config.json 파일이 없습니다.")
    return json.loads(config_path.read_text(encoding="utf-8"))


def fetch_profile(api_key: str, character_name: str) -> dict:
    url = API_URL_PROFILE.format(name=character_name)
    response = requests.get(url, headers=get_headers(api_key), timeout=20)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError("캐릭터 프로필 응답 형식이 예상과 다릅니다.")

    return data


def fetch_calendar(api_key: str) -> list:
    response = requests.get(API_URL_CALENDAR, headers=get_headers(api_key), timeout=20)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        raise RuntimeError("캘린더 응답 형식이 예상과 다릅니다.")

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
    islands: list[str] = []

    for item in calendar_data:
        start_times = item.get("StartTimes") or []
        if not isinstance(start_times, list):
            continue

        is_today = any(today_str in str(start_time) for start_time in start_times)
        if not is_today:
            continue

        name = str(item.get("ContentsName", "")).strip()
        if not name:
            continue

        if "섬" in name:
            islands.append(name)

    return unique_keep_order(islands)


def safe_str(value, fallback="-") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def extract_stat_map(profile_data: dict) -> dict:
    result = {}
    stats = profile_data.get("Stats") or []

    if not isinstance(stats, list):
        return result

    for item in stats:
        stat_type = safe_str(item.get("Type"), "")
        stat_value = safe_str(item.get("Value"), "")
        if stat_type:
            result[stat_type] = stat_value

    return result


def extract_equipment_summary(profile_data: dict) -> dict:
    equipment = profile_data.get("Equipment") or []

    summary = {
        "weapon": "-",
        "armor": "-",
        "accessory": "-",
    }

    if not isinstance(equipment, list):
        return summary

    weapons = []
    armors = []
    accessories = []

    for item in equipment:
        part_type = safe_str(item.get("Type"), "")
        item_name = safe_str(item.get("Name"), "-")

        if "무기" in part_type:
            weapons.append(item_name)
        elif part_type in {"투구", "상의", "하의", "장갑", "어깨"}:
            armors.append(item_name)
        elif part_type in {"목걸이", "귀걸이", "반지", "어빌리티 스톤", "팔찌"}:
            accessories.append(item_name)

    if weapons:
        summary["weapon"] = weapons[0]
    if armors:
        summary["armor"] = f"{len(armors)}부위 장착"
    if accessories:
        summary["accessory"] = f"{len(accessories)}개 장착"

    return summary


def build_profile_stats(profile_data: dict) -> list[dict]:
    stat_map = extract_stat_map(profile_data)

    return [
        {"label": "아이템 레벨", "value": safe_str(profile_data.get("ItemAvgLevel"))},
        {"label": "전투 레벨", "value": safe_str(profile_data.get("CharacterLevel"))},
        {"label": "원정대 레벨", "value": safe_str(profile_data.get("ExpeditionLevel"))},
        {"label": "PVP 등급", "value": safe_str(profile_data.get("PvpGradeName"))},
        {"label": "공격력", "value": stat_map.get("공격력", "-")},
        {"label": "최대 생명력", "value": stat_map.get("최대 생명력", "-")},
        {"label": "치명", "value": stat_map.get("치명", "-")},
        {"label": "특화", "value": stat_map.get("특화", "-")},
        {"label": "제압", "value": stat_map.get("제압", "-")},
        {"label": "신속", "value": stat_map.get("신속", "-")},
        {"label": "인내", "value": stat_map.get("인내", "-")},
        {"label": "숙련", "value": stat_map.get("숙련", "-")}
    ]


def build_equipment_stats(profile_data: dict) -> list[dict]:
    stat_map = extract_stat_map(profile_data)
    eq = extract_equipment_summary(profile_data)

    return [
        {"label": "직업", "value": safe_str(profile_data.get("CharacterClassName"))},
        {"label": "서버", "value": safe_str(profile_data.get("ServerName"))},
        {"label": "길드", "value": safe_str(profile_data.get("GuildName"))},
        {"label": "칭호", "value": safe_str(profile_data.get("Title"))},
        {"label": "무기", "value": eq["weapon"]},
        {"label": "방어구", "value": eq["armor"]},
        {"label": "장신구", "value": eq["accessory"]},
        {"label": "아크 그리드", "value": "-"},
        {"label": "투력", "value": stat_map.get("공격력", "-")},
        {"label": "실링", "value": safe_str(profile_data.get("UsingSkillPoint"), "-")},
        {"label": "골드", "value": "-"},
        {"label": "원정대 영지", "value": safe_str(profile_data.get("TownLevel"))}
    ]


def build_meta(today: datetime, config: dict) -> tuple[str, str, str]:
    weekday_map = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    weekday = weekday_map[today.weekday()]

    meta_left = f"VOL. {today.strftime('%Y-%m-%d')} {weekday}"
    meta_center = safe_str(config.get("metaCenter"), "발행처 | 아크라시아 연합 정보국")
    meta_right = f"발행일 | {today.strftime('%Y.%m.%d')} ({'월화수목금토일'[today.weekday()]})"

    return meta_left, meta_center, meta_right


def build_payload() -> dict:
    now = datetime.now(TIMEZONE)
    today_str = now.strftime("%Y-%m-%d")

    try:
        api_key = get_api_key()
        config = load_config()

        paper_title = safe_str(config.get("paperTitle"), "예스이호이테 일보")
        character_name = safe_str(config.get("characterName"), "")
        if character_name == "":
            raise RuntimeError("config.json의 characterName이 비어 있습니다.")

        profile_data = fetch_profile(api_key, character_name)
        calendar_data = fetch_calendar(api_key)
        today_islands = parse_today_islands(calendar_data, today_str)

        meta_left, meta_center, meta_right = build_meta(now, config)

        char_class = safe_str(profile_data.get("CharacterClassName"))
        server_name = safe_str(profile_data.get("ServerName"))
        char_level = safe_str(profile_data.get("CharacterLevel"))

        payload = {
            "paperTitle": paper_title,
            "metaLeft": meta_left,
            "metaCenter": meta_center,
            "metaRight": meta_right,
            "mainHeadline": f"이제 칭호도 스타일이다! 대신 {character_name}",
            "sideHeadline": "[단독] 식목일 맞이! 오늘의 모험섬 핫이슈",
            "character": {
                "image": safe_str(config.get("characterImage"), "https://placehold.co/420x560?text=Character"),
                "nameplate": character_name,
                "subplate": f"{server_name} | {char_class} | Lv.{char_level}"
            },
            "profileStats": build_profile_stats(profile_data),
            "equipmentStats": build_equipment_stats(profile_data),
            "lookbook": config.get("lookbook", []),
            "islandArticle": {
                "image": safe_str(config.get("islandImage"), "https://placehold.co/520x260?text=Island"),
                "todayIslands": today_islands if today_islands else ["오늘 표시된 모험섬 없음"],
                "remainingRaids": config.get("remainingRaids", []),
                "quote": "모험은 아직 끝나지 않았다.\n아직 가보지 않은 곳이\n아크라시아의 절반이다."
            },
            "market": {
                "island": config.get("marketIslandNews", []),
                "events": config.get("marketEventNews", []),
                "guild": config.get("guildAdNews", [])
            }
        }

        return payload

    except Exception as exc:
        return {
            "paperTitle": "예스이호이테 일보",
            "metaLeft": f"VOL. {today_str}",
            "metaCenter": "발행처 | 오류 상태",
            "metaRight": f"발행일 | {today_str}",
            "mainHeadline": "오늘의 신문을 정상적으로 불러오지 못했습니다.",
            "sideHeadline": "[속보] 데이터 로딩 실패",
            "character": {
                "image": "https://placehold.co/420x560?text=Error",
                "nameplate": "오류 상태",
                "subplate": "Actions 로그를 확인하세요"
            },
            "profileStats": [
                {"label": "오류", "value": safe_str(exc)}
            ],
            "equipmentStats": [
                {"label": "확인할 것", "value": "LOA_API_KEY / characterName / API 응답"}
            ],
            "lookbook": [],
            "islandArticle": {
                "image": "https://placehold.co/520x260?text=Error",
                "todayIslands": ["오늘의 모험섬 데이터를 불러오지 못했습니다."],
                "remainingRaids": ["config.json 및 Actions 로그를 확인하세요."],
                "quote": "오류가 나도 위젯은 죽지 않고\n실패 상태를 보여준다."
            },
            "market": {
                "island": ["오류 발생"],
                "events": ["Actions 로그 확인 필요"],
                "guild": ["시크릿 및 설정값 점검"]
            }
        }


def main() -> None:
    payload = build_payload()
    output_path = Path("daily.json")
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"saved: {output_path.resolve()}")


if __name__ == "__main__":
    main()
