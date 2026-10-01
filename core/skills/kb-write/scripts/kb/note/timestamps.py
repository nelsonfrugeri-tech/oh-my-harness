from datetime import datetime, timedelta
import re


RFC3339 = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})')


def parse_timestamp(value: str, *, utc: bool = True) -> datetime | None:
    if not RFC3339.fullmatch(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    if utc and parsed.utcoffset() != timedelta(0):
        return None
    return parsed
