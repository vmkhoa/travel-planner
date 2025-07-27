import re

def extract_plan_info(text):
    day_match = re.search(r"day\s*(\d+)", text, re.IGNORECASE)
    time_match = re.search(r"(\d{1,2}:\d{2})", text)
    title_match = re.search(r"(?:visit|go to|see|explore|lunch at|dinner at|eat at)\s+(.+)", text, re.IGNORECASE)

    if not (day_match and time_match and title_match):
        return None

    return {
        "day": int(day_match.group(1)),
        "time": time_match.group(1),
        "title": title_match.group(1).strip().rstrip("."),
    }
