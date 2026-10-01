"""Validated evaluator annotations; these are not candidate self-reports."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Kind(str, Enum):
    PENDING = 'pending'
    PRESENT = 'present'
    ASK = 'ask'
    CONSENT = 'consent'
    APPROVE = 'approve'
    NAV = 'nav'
    READ = 'read'
    WRITE = 'write'
    SESSION_MEMORY = 'session_memory'


@dataclass(frozen=True)
class Event:
    kind: Kind
    source: str
    note: str = ''
    revision: str = ''
    actor: str = ''
    content: str = ''
    path: str = ''
    update: bool = False
    path_shown: bool = False
    candidates_shown: bool = False
    asks_path: bool = False
    approved: bool = False
    session_record: bool = False


def parse_event(raw: object) -> Event:
    if not isinstance(raw, dict):
        raise ValueError('event must be an object')
    values = dict(raw)
    try:
        values['kind'] = Kind(values.get('kind'))
    except (TypeError, ValueError) as error:
        raise ValueError('unknown event kind') from error
    for name, field in Event.__dataclass_fields__.items():
        if name == 'kind':
            continue
        expected = bool if field.type == 'bool' else str
        if name in values and type(values[name]) is not expected:
            raise ValueError(f'{name} has invalid type')
    try:
        event = Event(**values)
    except TypeError as error:
        raise ValueError('missing or unknown event fields') from error
    if not event.source:
        raise ValueError('every event needs an original transcript locator')
    if event.kind in {Kind.PENDING, Kind.PRESENT, Kind.ASK, Kind.CONSENT, Kind.APPROVE}:
        if not event.note or not event.revision:
            raise ValueError('note events need note and revision')
    if event.kind == Kind.WRITE and 'session_record' not in values:
        raise ValueError('write events need an observed session_record classification')
    if event.kind in {Kind.READ, Kind.WRITE} and not event.path:
        raise ValueError('file events need a path')
    return event
