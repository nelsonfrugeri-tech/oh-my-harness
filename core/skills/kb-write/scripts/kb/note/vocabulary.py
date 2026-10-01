from enum import StrEnum


class NoteType(StrEnum):
    DECISION = "decision"
    EVENT = "event"
    PROCEDURE = "procedure"
    REFERENCE = "reference"
    CONVERSATION = "conversation"


class Status(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class Harness(StrEnum):
    CLAUDE_CODE = "claude-code"
    CODEX = "codex"
    CURSOR = "cursor"


class Scope(StrEnum):
    WORK = "work"
    PERSON = "person"


TITLE_LIMITS = (10, 70)
DESCRIPTION_LIMITS = (120, 300)
SUMMARY_LIMITS = (600, 1500)
REASON_LIMITS = (30, 500)


def is_published(status: Status) -> bool:
    return status is Status.ACTIVE
