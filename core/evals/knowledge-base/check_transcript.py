"""Check ordered, independently annotated transcript events; fail closed on gaps."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from transcript_events import Event, Kind, parse_event


@dataclass(frozen=True)
class Review:
    content: str
    update: bool
    stage: int = 0


def advance(event: Event, review: Review) -> Review:
    stage = review.stage
    if event.kind == Kind.PRESENT:
        valid = event.actor == 'main' and event.content == review.content
        valid = valid and bool(review.content)
        valid = valid and (review.update or (event.path_shown and event.candidates_shown))
        stage = 1 if valid else 0
    elif event.kind == Kind.ASK:
        valid = event.actor == 'main' and event.asks_path != review.update
        stage = 2 if stage == 1 and valid else 0
    elif event.kind == Kind.CONSENT:
        valid = event.actor == 'user' and event.approved
        stage = 3 if stage == 2 and valid else 0
    return Review(review.content, review.update, stage)


def approval_failures(events: tuple[Event, ...]) -> list[str]:
    reviews: dict[tuple[str, str], Review] = {}
    failures: list[str] = []
    for event in events:
        key = (event.note, event.revision)
        if event.kind == Kind.PENDING:
            reviews = {k: v for k, v in reviews.items() if k[0] != event.note}
            reviews[key] = Review(event.content, event.update)
        elif event.kind == Kind.APPROVE:
            review = reviews.pop(key, None)
            if review is None or review.stage != 3:
                failures.append(f'{event.source}: approval without review and specific consent')
        elif key in reviews:
            reviews[key] = advance(event, reviews[key])
    return failures


def check(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict) or not isinstance(raw.get('events'), list):
        raise ValueError('expected an object containing events')
    for flag in ('complete', 'navigation', 'current_state', 'session_recall', 'legacy_read'):
        if flag in raw and type(raw[flag]) is not bool:
            raise ValueError(f'{flag} must be boolean')
    events = tuple(parse_event(item) for item in raw['events'])
    failures = approval_failures(events)
    nav_calls = sum(event.kind == Kind.NAV for event in events)
    if raw.get('navigation') and nav_calls > 2:
        failures.append('navigation exceeds two calls')
    for event in events:
        parts = PurePosixPath(event.path).parts
        if raw.get('current_state') and event.kind == Kind.READ:
            if '.history' in parts or 'backup' in parts:
                failures.append(f'{event.source}: current-state read opened historical data')
        if event.kind == Kind.WRITE and 'sessions' in parts and event.path.endswith('.json'):
            failures.append(f'{event.source}: session record written')
    if raw.get('legacy_read'):
        failures.extend(legacy_failures(events))
    missing = []
    if raw.get('complete') is not True or not events:
        missing.append('complete observed transcript required')
    if raw.get('navigation') and not nav_calls:
        missing.append('navigation was not exercised')
    if raw.get('session_recall') and not any(e.kind == Kind.SESSION_MEMORY for e in events):
        failures.append('session recall did not use session-memory')
    verdict = 'fail' if failures else 'unexercised' if missing else 'pass'
    return {'verdict': verdict, 'failures': failures, 'unexercised': missing,
            'nav_calls': nav_calls, 'approval_calls': sum(e.kind == Kind.APPROVE for e in events)}


def legacy_failures(events: tuple[Event, ...]) -> list[str]:
    instruction_seen = False
    failures: list[str] = []
    for event in events:
        parts = PurePosixPath(event.path).parts
        if event.kind != Kind.READ or 'backup' not in parts:
            continue
        relative = parts[parts.index('backup') + 1:]
        if relative == ('INSTRUCTION.md',):
            instruction_seen = True
        elif not instruction_seen:
            failures.append(f'{event.source}: backup read before backup/INSTRUCTION.md')
    if not instruction_seen:
        failures.append('legacy access did not read backup/INSTRUCTION.md')
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('transcript', type=Path)
    args = parser.parse_args()
    try:
        result = check(json.loads(args.transcript.read_text(encoding='utf-8')))
    except (OSError, ValueError) as error:
        result = {'verdict': 'unexercised', 'reason': str(error)}
    print(json.dumps(result, ensure_ascii=False))
    return {'pass': 0, 'fail': 1, 'unexercised': 2}[result['verdict']]


if __name__ == '__main__':
    raise SystemExit(main())
