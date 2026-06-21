"""Domain model for a knowledge-base note.

The note is the atomic unit of the system. Its canonical identity is the
immutable UUID `id`; the `slug` is a human-readable file-name component and
links between notes always reference the UUID, so a slug can be regenerated
or a file renamed without breaking relationships.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from oh_my_harness.kb.core.slug import generate_slug


class NoteType(StrEnum):
    DECISION = "decision"
    EVENT = "event"
    PROCEDURE = "procedure"
    REFERENCE = "reference"
    CONVERSATION = "conversation"


def _utc_now() -> datetime:
    return datetime.now(UTC)


# Input keys we understand — field names, their long-form aliases, and the
# legacy ``universe`` key. Anything else found in the front-matter is preserved
# verbatim in ``extra_meta`` (a tolerant reader keeps unknown keys, never drops
# them).
_RECOGNIZED_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "slug",
        "title",
        "type",
        "project",
        "kb_name",
        "universe",  # legacy alias for kb_name
        "created_at",
        "timestamp",  # long-form alias forcreated_at
        "entities",
        "tags",  # long-form alias forentities
        "links_out",
        "supersedes",
        "archived",
        "resource",
        "summary",
        "description",  # long-form alias forsummary
        "extra_meta",
        "body",
    }
)


class Note(BaseModel):
    # ``extra="ignore"`` (was ``forbid``): as a tolerant reader we must not
    # reject unknown front-matter keys. They are captured into ``extra_meta`` by
    # the ``before`` validator so nothing is lost on round-trip. The *producer*
    # stays strict via the field validators below.
    model_config = ConfigDict(
        validate_assignment=True,
        extra="ignore",
        populate_by_name=True,
    )

    id: UUID = Field(default_factory=uuid4, frozen=True)
    slug: str = ""
    title: str
    type: NoteType
    project: str
    kb_name: str
    created_at: datetime = Field(
        default_factory=_utc_now,
        validation_alias=AliasChoices("created_at", "timestamp"),
        serialization_alias="timestamp",
    )
    entities: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("entities", "tags"),
        serialization_alias="tags",
    )
    links_out: list[UUID] = Field(default_factory=list)
    supersedes: UUID | None = None
    archived: bool = False
    resource: str | None = None
    summary: str = Field(
        validation_alias=AliasChoices("summary", "description"),
        serialization_alias="description",
    )
    extra_meta: dict[str, Any] = Field(default_factory=dict)
    body: str = ""

    # Backward-compatible property for call sites that still read .universe.
    @property
    def universe(self) -> str:  # backward-compatible alias
        return self.kb_name

    @field_validator("title", "project", "kb_name", "summary")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty or whitespace")
        return value

    @field_validator("created_at")
    @classmethod
    def _require_tzaware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("must be timezone-aware")
        return value

    @field_validator("resource")
    @classmethod
    def _resource_non_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("resource must not be empty or whitespace when present")
        return value

    @model_validator(mode="before")
    @classmethod
    def _migrate_and_capture(cls, data: object) -> object:
        """Migrate the legacy ``universe`` key and capture unknown keys.

        Two responsibilities, both only meaningful for dict input (parsed
        front-matter):

        1. Map the legacy ``universe`` key to ``kb_name`` so existing .md files
           and Qdrant payloads deserialize without data migration.
        2. Preserve any front-matter key we don't recognize by moving it into
           ``extra_meta``. With ``extra="ignore"`` Pydantic would silently drop
           such keys; a tolerant reader preserves unknown keys, so we re-emit
           them verbatim on serialize.
        """
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "universe" in data and "kb_name" not in data:
            data["kb_name"] = data.pop("universe")
        extra: dict[str, Any] = dict(data.get("extra_meta") or {})
        for key in list(data.keys()):
            if key not in _RECOGNIZED_KEYS:
                extra[key] = data.pop(key)
        if extra:
            data["extra_meta"] = extra
        return data

    @model_validator(mode="after")
    def _ensure_slug(self) -> Note:
        if not self.slug:
            object.__setattr__(self, "slug", generate_slug(self.title, self.created_at))
        return self
