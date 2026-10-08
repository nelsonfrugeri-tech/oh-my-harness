"""Select the transcript adapter from observed records, never from path names."""
from kb.adapters.transcript_claude import ClaudeTranscriptSource
from kb.adapters.transcript_codex import ADMINISTRATIVE, CodexTranscriptSource, read_records
from kb.app.harvest import HarvestSourcePort
from kb.app.ports import TranscriptSourcePort
from kb.entities.model import Candidate


class TranscriptSource(TranscriptSourcePort, HarvestSourcePort):
    def load(self, path: str) -> str:
        return _adapter(path).load(path)

    def harvest_candidates(self, path: str) -> tuple[Candidate, ...]:
        return _adapter(path).harvest_candidates(path)


def _adapter(path: str) -> ClaudeTranscriptSource:
    records = read_records(path)
    codex_types = ADMINISTRATIVE | {'response_item', 'event_msg'}
    if any(record.get('type') in codex_types for record in records):
        return CodexTranscriptSource()
    return ClaudeTranscriptSource()
