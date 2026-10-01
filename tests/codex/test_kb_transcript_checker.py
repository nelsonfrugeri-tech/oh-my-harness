from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_CHECKER = _ROOT / 'core/evals/knowledge-base/check_transcript.py'


def event(kind: str, **fields: object) -> dict[str, object]:
    return {'kind': kind, 'source': 'fixture:1', **fields}


def approval() -> list[dict[str, object]]:
    return [
        event('pending', note='a', revision='v1', content='Entire note', update=False),
        event('present', note='a', revision='v1', actor='main', content='Entire note',
              path_shown=True, candidates_shown=True),
        event('ask', note='a', revision='v1', actor='main', asks_path=True),
        event('consent', note='a', revision='v1', actor='user', approved=True),
        event('approve', note='a', revision='v1'),
    ]


def check(events: list[dict[str, object]], **options: object) -> dict[str, object]:
    payload = {'complete': True, 'events': events, **options}
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'trace.json'
        path.write_text(json.dumps(payload), encoding='utf-8')
        result = subprocess.run([sys.executable, str(_CHECKER), str(path)],
                                capture_output=True, text=True, check=False)
        if not result.stdout:
            raise AssertionError(result.stderr)
        return json.loads(result.stdout)


class ApprovalCheckerTest(unittest.TestCase):
    def test_review_then_specific_consent_passes(self) -> None:
        self.assertEqual('pass', check(approval())['verdict'])

    def test_missing_or_misbound_review_and_consent_fail(self) -> None:
        for index, field, value in [
            (1, 'actor', 'subagent'), (1, 'content', 'summary'),
            (1, 'path_shown', False), (1, 'candidates_shown', False),
            (2, 'asks_path', False), (3, 'actor', 'tool'),
            (3, 'note', 'other'), (3, 'approved', False),
            (4, 'revision', 'v2'),
        ]:
            events = approval()
            events[index][field] = value
            with self.subTest(index=index, field=field):
                self.assertEqual('fail', check(events)['verdict'])

    def test_early_and_reused_consent_fail(self) -> None:
        events = approval()
        events[2], events[3] = events[3], events[2]
        self.assertEqual('fail', check(events)['verdict'])
        events = approval()
        events.append(events[-1])
        self.assertEqual('fail', check(events)['verdict'])


class TranscriptCoverageTest(unittest.TestCase):
    def test_navigation_and_current_state_access_are_checked(self) -> None:
        events = [event('nav')] * 3
        self.assertEqual('fail', check(events, navigation=True)['verdict'])
        for path in ['work/a/.history/x.md', 'backup/work/a.md']:
            self.assertEqual('fail', check([event('read', path=path)],
                                          current_state=True)['verdict'])
        self.assertEqual('pass', check([event('nav'), event('read', path='work/a.md')],
                                      navigation=True, current_state=True)['verdict'])

    def test_session_writes_and_incomplete_traces_do_not_pass(self) -> None:
        self.assertEqual('fail', check([event('write', path='sessions/abc.json')])['verdict'])
        self.assertEqual('unexercised', check(approval(), complete=False)['verdict'])
        self.assertEqual('unexercised', check([])['verdict'])

    def test_updates_show_diff_and_do_not_ask_path(self) -> None:
        events = approval()
        events[0]['update'] = True
        events[0]['content'] = '-old\n+new'
        events[1]['content'] = '-old\n+new'
        events[2]['asks_path'] = False
        self.assertEqual('pass', check(events)['verdict'])
        events[2]['asks_path'] = True
        self.assertEqual('fail', check(events)['verdict'])


class LegacyAndInputTest(unittest.TestCase):
    def test_legacy_instruction_precedes_other_backup_reads(self) -> None:
        instruction = event('read', path='backup/INSTRUCTION.md')
        note = event('read', path='backup/work/note.md')
        self.assertEqual('pass', check([instruction, note], legacy_read=True)['verdict'])
        self.assertEqual('fail', check([note, instruction], legacy_read=True)['verdict'])
        self.assertEqual('fail', check([note], legacy_read=True)['verdict'])

    def test_malformed_events_are_unexercised(self) -> None:
        for bad in [event('unknown'), event('nav', source=''),
                    event('read'), event('approve'), event('nav', approved='yes'),
                    event('nav', unexpected=True)]:
            with self.subTest(event=bad):
                self.assertEqual('unexercised', check([bad])['verdict'])
        self.assertEqual('unexercised', check(approval(), complete='yes')['verdict'])

    def test_missing_navigation_or_recall_is_not_pass(self) -> None:
        self.assertEqual('unexercised', check(approval(), navigation=True)['verdict'])
        self.assertEqual('fail', check(approval(), session_recall=True)['verdict'])
        self.assertEqual('pass', check([event('session_memory')], session_recall=True)['verdict'])


if __name__ == '__main__':
    unittest.main()
