class EnvironmentFailure(RuntimeError):
    """An unavailable or inconsistent runtime requires operator action, not note edits."""


class TranscriptFailure(ValueError):
    """A safe diagnostic without transcript contents or arbitrary input values."""
