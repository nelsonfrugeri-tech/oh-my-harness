from dataclasses import dataclass
from types import MappingProxyType

from .vocabulary import NoteType


@dataclass(frozen=True)
class SectionSchema:
    required: tuple[str, ...]
    optional: tuple[str, ...]


SCHEMAS = MappingProxyType({
    NoteType.DECISION: SectionSchema(
        ("Decision", "Context", "Options", "Consequences", "How to apply"),
        ("Drivers", "Confirmation")),
    NoteType.EVENT: SectionSchema(
        ("What happened", "Timeline", "Outcome"),
        ("Impact", "Causes", "Resolution", "Lessons", "Follow-ups")),
    NoteType.PROCEDURE: SectionSchema(
        ("Goal", "When to use", "Prerequisites", "Steps", "Verification"),
        ("Rollback", "Pitfalls")),
    NoteType.REFERENCE: SectionSchema(("Facts", "Scope"),
                                    ("Examples", "Caveats", "Where to find more")),
    NoteType.CONVERSATION: SectionSchema(("Participants", "Key facts", "Outcome"),
                                       ("Discussion", "Action items", "Open questions")),
})
CONDITIONAL_SECTIONS = ("Entities", "Dates", "Figures")
COMMON_OPTIONAL = ("Sources",)


def required_sections(note_type: NoteType, *, has_entities: bool = False,
                      has_dates: bool = False, has_figures: bool = False) -> tuple[str, ...]:
    conditions = (has_entities, has_dates, has_figures)
    return SCHEMAS[note_type].required + tuple(
        heading for heading, enabled in zip(CONDITIONAL_SECTIONS, conditions) if enabled)
