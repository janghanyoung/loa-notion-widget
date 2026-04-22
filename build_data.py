import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import requests


API_URL_CALENDAR = "https://developer-lostark.game.onstove.com/gamecontents/calendar"
API_URL_PROFILE = "https://developer-lostark.game.onstove.com/characters/{name}/profiles"
TIMEZONE = ZoneInfo("Asia/Seoul")


def get_api_key() -> str:
    api_key = os.environ.get("LOA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("LOA_API_KEY 환경 변수가 비어 있습니다.")
    return api_key


def load_config() -> dict:
    config_path = Path("config.json")
    if not config_path.exists():
        raise RuntimeError("config.json 파일이 없습니다.")
    return json.loads(config_path.read_text(encoding="utf-8"))


def get_headers(api_key: str) -> dict:
    return {
        "Authorization": f"bearer {api_key}",
        "Accept": "application/json",
    }


def fetch_calendar(api_key: str) -> list:
    response = requests.get(API_URL_CALENDAR, headers=get_headers(api_key), timeout=20)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        raise RuntimeError("캘린더 응답 형식이 예상과 다릅니다.")

    return data


def fetch_profile(api_key: str, character_name: str) -> dict:
    url = API_URL_PROFILE.format(name=character_name)
    response = requests.get(url, headers=get_headers(api_key), timeout=20)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError(f"{character_name} 프로필 응답 형식이 예상과 다릅니다.")

    return data


def parse_today_items(calendar_data: list, today_str: str) -> tuple[list[str], list[str]]:
    islands = []
    events = []

    for item in calendar_data:
        start_times = item.get("StartTimes") or []
        if not isinstance(start_times, list):
            continue

        is_today = any(today_str in str(start_time) for start_time in start_times)
        if not is_today:
            continue

        name = str(item.get("ContentsName", "이름 없는 콘텐츠")).strip() or "이름 없는 콘텐츠"

        if "섬" in name:
            islands.append(name)
        else:
            events.append(name)

    return unique_keep_order(islands), unique_keep_order(events)


def unique_keep_order(items: list[str]) -> list[str]:
    seen = set()
    result = []

    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)

    return result


def build_character_stats(profile: dict) -> list[dict]:
    return [
        {"name": "이름", "value": str(profile.get("CharacterName", "-"))},
        {"name": "직업", "value": str(profile.get("CharacterClassName", "-"))},
        {"name": "서버", "value": str(profile.get("ServerName", "-"))},
        {"name": "아이템레벨", "value": str(profile.get("ItemAvgLevel", "-"))},
    ]


def build_payload() -> dict:
    now = datetime.now(TIMEZONE)
    today_str = now.strftime("%Y-%m-%d")

    try:
        api_key = get_api_key()
        config = load_config()

        widget_title = str(config.get("widget_title", "아크라시아 일보"))
        subhead = str(config.get("subhead", "모험 · 일정 · 캐릭터"))
        characters = config.get("characters", [])

        if not characters:
            raise RuntimeError("config.json의 characters가 비어 있습니다.")

        main_character = str(characters[0]).strip()
        if not main_character:
            raise RuntimeError("대표 캐릭터명이 비어 있습니다.")

        calendar_data = fetch_calendar(api_key)
        profile_data = fetch_profile(api_key, main_character)

        islands, events = parse_today_items(calendar_data, today_str)

        island_text = "\n".join(islands) if islands else "오늘 표시된 섬 콘텐츠 없음"
        event_text = "\n".join(events[:8]) if events else "오늘 표시된 주요 이벤트 없음"
        character_stats = build_character_stats(profile_data)

        briefs = []
        briefs.append(f"대표 캐릭터: {profile_data.get('CharacterName', '-')}")
        briefs.append(f"오늘 섬 콘텐츠 {len(islands)}건")
        briefs.append(f"기타 이벤트 {len(events)}건")

        return {
            "title": widget_title,
            "date": today_str,
            "subhead": subhead,
            "headline": f"{today_str} 오늘의 아크라시아 일정과 개인 기록",
            "summary": "공식 캘린더 API와 대표 캐릭터 프로필 기준으로 오늘 볼 정보를 정리합니다.",
            "briefs": briefs,
            "columns": [
                {
                    "tag": "01 TODAY",
                    "title": "오늘의 콘텐츠",
                    "body": island_text,
                    "highlight": "공식 캘린더 API 기준"
                },
                {
                    "tag": "02 CHARACTER",
                    "title": "대표 캐릭터",
                    "stats": character_stats,
                    "extra_body": event_text
                },
                {
                    "tag": "03 MEMO",
                    "title": "메모",
                    "quote": "기록은 곧 통제력이다.",
                    "todos": [
                        "대표 캐릭터 상태 확인",
                        "오늘 섬 콘텐츠 체크",
                        "주요 이벤트 우선순위 정리"
                    ]
                }
            ]
        }

    except Exception as exc:
        return {
            "title": "아크라시아 일보",
            "date": today_str,
            "subhead": "오류 상태",
            "headline": "오늘의 데이터를 불러오지 못했습니다.",
            "summary": "API 키, config.json, 캐릭터명, 또는 Actions 실행 상태를 확인해야 합니다.",
            "briefs": [
                "자동 생성 실패",
                "Actions 로그 확인 필요",
                "오류 상태 fallback 표시 중"
            ],
            "columns": [
                {
                    "tag": "01 ERROR",
                    "title": "오류 메시지",
                    "body": str(exc)
                },
                {
                    "tag": "02 CHECK",
                    "title": "확인할 것",
                    "todos": [
                        "LOA_API_KEY 시크릿 등록 여부",
                        "config.json characters 값 확인",
                        "캐릭터명 오탈자 확인"
                    ]
                },
                {
                    "tag": "03 STATUS",
                    "title": "현재 상태",
                    "quote": "오류가 나도 위젯은 죽지 않고 실패 상태를 보여줍니다."
                }
            ]
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
