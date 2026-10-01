from datetime import datetime, timezone

from kb.app.ports import ClockPort


class SystemClock(ClockPort):
    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
