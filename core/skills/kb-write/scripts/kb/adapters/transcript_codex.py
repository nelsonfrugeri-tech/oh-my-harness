"""Codex JSONL evidence, normalized to the existing text/tool harvest contract."""
import json
from pathlib import Path
import re

from kb.adapters.transcript_claude import ClaudeTranscriptSource, _safe_text
from kb.app.errors import TranscriptFailure
from kb.entities.secrets import is_secret_field

ADMINISTRATIVE = frozenset({'session_meta', 'turn_context', 'world_state', 'compacted',
                           'token_usage_record', 'inter_agent_communication_metadata'})
EVENTS = frozenset({'item_completed', 'token_count', 'task_started', 'task_complete',
                    'thread_settings_applied', 'turn_aborted', 'agent_reasoning',
                    'context_compacted', 'warning', 'error'})
CALLS = frozenset({'function_call', 'custom_tool_call'})
OUTPUTS = frozenset({'function_call_output', 'custom_tool_call_output'})


class CodexTranscriptSource(ClaudeTranscriptSource):
    def load(self, path: str) -> str:
        return '\n'.join(_safe_text(text) for record in self._records(path)
                         for text in _evidence_strings(record))

    def _records(self, path: str) -> tuple[object, ...]:
        records = read_records(path)
        calls = _calls(records)
        content = []
        messages = {text for r in records if r.get('type') == 'response_item'
                    and isinstance(r.get('payload'), dict)
                    and r['payload'].get('type') == 'message'
                    and r['payload'].get('role') in {'user', 'assistant'}
                    for text in _message_content(r['payload'].get('content'))}
        for record in records:
            content.extend(_record_content(record, calls, messages))
        if not content:
            raise TranscriptFailure('Transcript contains no supported message content')
        return tuple(content)

def _evidence_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for key, item in value.items()
                if not is_secret_field(key)
                for text in _evidence_strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _evidence_strings(item)]
    return []


def _calls(records: tuple[dict, ...]) -> dict:
    calls = {}
    for record in records:
        payload = record.get('payload')
        if record.get('type') != 'response_item' or not isinstance(payload, dict):
            continue
        if payload.get('type') not in CALLS:
            continue
        identifier = payload.get('call_id')
        if not isinstance(identifier, str) or identifier in calls:
            raise TranscriptFailure('Codex tool call identity is missing or duplicated')
        calls[identifier] = payload
    return calls


def read_records(path: str) -> tuple[dict, ...]:
    try:
        with Path(path).open(encoding='utf-8') as stream:
            records = tuple(json.loads(line) for line in stream if line.strip())
    except UnicodeDecodeError as error:
        raise TranscriptFailure('Transcript text artifact is not valid UTF-8') from error
    except json.JSONDecodeError as error:
        raise TranscriptFailure('Transcript contains invalid JSON') from error
    if not records:
        raise TranscriptFailure('Empty transcript')
    if any(not isinstance(record, dict) for record in records):
        raise TranscriptFailure('Transcript records must be JSON objects')
    return records


def _record_content(record: dict, calls: dict, messages: set[str]) -> list[object]:
    kind = record.get('type')
    if kind in ADMINISTRATIVE:
        return []
    payload = record.get('payload')
    if not isinstance(payload, dict):
        raise TranscriptFailure('Unsupported Codex record shape')
    if kind == 'response_item':
        return _response_content(payload, calls)
    if kind == 'event_msg':
        event = payload.get('type')
        if event in EVENTS:
            return []
        if event in {'user_message', 'agent_message'}:
            text = payload.get('message')
            if not isinstance(text, str):
                raise TranscriptFailure('Unsupported Codex event message shape')
            return [] if text in messages else [text]
    raise TranscriptFailure('Unsupported Codex record type')


def _response_content(payload: dict, calls: dict) -> list[object]:
    kind = payload.get('type')
    if kind == 'reasoning':
        return []
    if kind in {'message', 'agent_message'}:
        if kind == 'message' and payload.get('role') in {'system', 'developer'}:
            return []  # Harness instructions are not conversation evidence.
        if kind == 'message' and payload.get('role') not in {'user', 'assistant'}:
            raise TranscriptFailure('Unsupported Codex message role')
        return _message_content(payload.get('content'))
    if kind in CALLS:
        return [_call_block(payload)]
    if kind in OUTPUTS:
        identifier = payload.get('call_id')
        if not isinstance(identifier, str) or identifier not in calls:
            raise TranscriptFailure('Codex tool output has no matching call')
        output = payload.get('output')
        if not isinstance(output, (str, list, dict)):
            raise TranscriptFailure('Unsupported Codex tool output shape')
        return [{'type': 'tool_result', 'tool_use_id': identifier, 'content': output}]
    raise TranscriptFailure('Unsupported Codex response item type')


def _message_content(content: object) -> list[str]:
    if not isinstance(content, list):
        raise TranscriptFailure('Unsupported Codex message content shape')
    texts = []
    for block in content:
        if not isinstance(block, dict):
            raise TranscriptFailure('Unsupported Codex message block shape')
        kind = block.get('type')
        if kind in {'input_text', 'output_text'} and isinstance(block.get('text'), str):
            texts.append(block['text'])
        elif kind not in {'input_image', 'output_image', 'encrypted_content'}:
            raise TranscriptFailure('Unsupported Codex message content type')
    return texts


def _call_block(payload: dict) -> dict:
    name, identifier = payload.get('name'), payload.get('call_id')
    if not isinstance(name, str) or not isinstance(identifier, str):
        raise TranscriptFailure('Unsupported Codex tool call shape')
    raw = payload.get('arguments') if payload['type'] == 'function_call' else payload.get('input')
    if not isinstance(raw, str):
        raise TranscriptFailure('Unsupported Codex tool arguments shape')
    if payload['type'] == 'function_call':
        try:
            arguments = json.loads(raw)
        except json.JSONDecodeError as error:
            raise TranscriptFailure('Codex tool arguments contain invalid JSON') from error
        if not isinstance(arguments, dict):
            raise TranscriptFailure('Codex tool arguments must be a JSON object')
    else:
        arguments = {'text': raw}
    if name == 'exec_command':
        name, arguments = 'Bash', {'command': arguments.get('cmd')}
    if name == 'apply_patch':
        paths = re.findall(r'^\*\*\* (?:Add|Update|Delete) File: (.+)$', raw, re.M)
        arguments = {'text': raw, 'paths': paths}
    return {'type': 'tool_use', 'id': identifier, 'name': name, 'input': arguments}
