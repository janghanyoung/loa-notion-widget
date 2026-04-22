import json
from datetime import datetime
from pathlib import Path

def build_data():
    today = datetime.now().strftime("%Y-%m-%d")

    data = {
        "title": "아크라시아 일보",
        "date": today,
        "headline": f"{today} 오늘의 아크라시아 일정",
        "summary": "자동 생성된 테스트 데이터입니다.",

        "columns": [
            {
                "tag": "01 TODAY",
                "title": "오늘의 콘텐츠",
                "body": "자동 생성된 콘텐츠 영역입니다.\n이 부분은 나중에 로아 API로 교체됩니다.",
                "highlight": f"생성 시각: {datetime.now().strftime('%H:%M:%S')}"
            },
            {
                "tag": "02 COLLECTION",
                "title": "수집품",
                "stats": [
                    {"name": "모코코", "value": "1200 / 1300"},
                    {"name": "섬마", "value": "71 / 98"}
                ],
                "body": "현재는 더미 데이터"
            },
            {
                "tag": "03 MEMO",
                "title": "메모",
                "todos": [
                    "자동 업데이트 테스트",
                    "GitHub Actions 정상 작동 확인"
                ],
                "quote": "이건 자동 생성된 문장이다"
            }
        ],

        "footer": [
            f"UPDATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "AUTO GENERATED",
            "GITHUB ACTIONS"
        ]
    }

    Path("daily.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

if __name__ == "__main__":
    build_data()
