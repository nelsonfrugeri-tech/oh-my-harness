from dataclasses import dataclass

from kb.app.ports import ClockPort, EmbedderPort, NoteStorePort, SearchIndexPort


@dataclass(frozen=True)
class Context:
    store: NoteStorePort
    clock: ClockPort
    machine_id: str
    index: SearchIndexPort | None = None
    embedder: EmbedderPort | None = None
