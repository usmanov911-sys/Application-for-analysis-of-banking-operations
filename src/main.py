import json

from src.views import events_page, main_page

if __name__ == "__main__":
    result = main_page("2026-08-20 14:00:00")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    events_result = events_page("2026-08-20", "M")
    print(json.dumps(events_result, ensure_ascii=False, indent=2))
