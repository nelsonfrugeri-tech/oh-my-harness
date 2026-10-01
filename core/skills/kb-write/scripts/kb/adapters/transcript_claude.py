import json
from pathlib import Path
import re
import shlex

from kb.app.errors import TranscriptFailure
from kb.app.harvest import HarvestSourcePort
from kb.app.ports import TranscriptSourcePort
from kb.entities.extraction import extract
from kb.entities.kinds import EntityKind
from kb.entities.model import Candidate
from kb.entities.normalization import normalize
from kb.entities.secrets import find_secrets


class ClaudeTranscriptSource(TranscriptSourcePort, HarvestSourcePort):
    def load(self, path: str) -> str:
        return '\n'.join(text for record in _records(path) for text in _strings(record))

    def harvest_candidates(self, path: str) -> tuple[Candidate, ...]:
        records = _records(path)
        candidates: list[Candidate] = []
        blocks = [block for record in records for block in _blocks(record)]
        for record in records:
            for text in _harvest_strings(record):
                candidates.extend(extract(_safe_text(text)))
        for block in blocks:
            if block.get('type') == 'tool_use':
                candidates.extend(_tool_candidates(block))
        candidates.extend(_remote_results(blocks))
        return tuple(dict.fromkeys(candidate for candidate in candidates
                                   if candidate.value and not find_secrets(candidate.value)))


def _records(path: str) -> tuple[object, ...]:
    source = Path(path).resolve(strict=True)
    root = source.parent / source.stem
    files = [source]
    for name in ('subagents', 'tool-results'):
        directory = root / name
        if directory.is_dir():
            files.extend(item for item in directory.rglob('*') if item.is_file()
                         and not item.is_symlink() and item.resolve().is_relative_to(root.resolve()))
    records: list[object] = []
    for file in files:
        if file != source and file.suffix.lower() in {'.pdf', '.png', '.jpg', '.jpeg', '.gif',
                                                     '.webp', '.mp3', '.mp4', '.wav', '.zip'}:
            continue  # Binary tool artifacts are not transcript text evidence.
        try:
            content = file.read_text(encoding='utf-8')
        except UnicodeDecodeError as error:
            raise TranscriptFailure('Transcript text artifact is not valid UTF-8') from error
        if file != source and file.suffix != '.jsonl':
            records.append(content)
            continue
        try:
            parsed = [json.loads(line) for line in content.splitlines() if line.strip()]
        except json.JSONDecodeError as error:
            raise TranscriptFailure('Transcript contains invalid JSON') from error
        if not parsed:
            raise TranscriptFailure('Empty transcript')
        supported = 0
        for record in parsed:
            if not isinstance(record, dict):
                raise TranscriptFailure('Transcript records must be JSON objects')
            if record.get('type') in ('session_meta', 'response_item', 'turn_context', 'event_msg'):
                raise TranscriptFailure('Codex transcript proof is unsupported; use approved degraded mode')
            if record.get('type') in ('user', 'assistant', 'system', 'summary'):
                before = len(records)
                message = record.get('message')
                if isinstance(message, dict) and 'content' in message:
                    records.append(message['content'])
                elif isinstance(record.get('content'), (str, list)):
                    records.append(record['content'])
                elif record.get('type') == 'summary' and isinstance(record.get('summary'), str):
                    records.append(record['summary'])
                if len(records) == before:
                    if record.get('type') in ('user', 'assistant'):
                        raise TranscriptFailure('Unsupported message content shape')
                else:
                    supported += 1
        if file == source and not supported:
            raise TranscriptFailure('Transcript contains no supported message content')
    return tuple(records)


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return []


def _harvest_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for key, item in value.items()
                if key not in ('file_path', 'path', 'cwd', 'command')
                and not re.search(r'password|passwd|secret|token|authorization|api.?key|private.?key', key, re.I)
                for text in _harvest_strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _harvest_strings(item)]
    return []


def _blocks(value: object) -> list[dict[str, object]]:
    if isinstance(value, dict):
        return [value] + [block for item in value.values() for block in _blocks(item)]
    if isinstance(value, list):
        return [block for item in value for block in _blocks(item)]
    return []


def _safe_text(text: str) -> str:
    for finding in sorted(find_secrets(text), key=lambda item: item.start, reverse=True):
        text = text[:finding.start] + ' ' * (finding.end - finding.start) + text[finding.end:]
    return text


def _tool_candidates(block: dict[str, object]) -> list[Candidate]:
    name, arguments = block.get('name'), block.get('input')
    if not isinstance(name, str) or not isinstance(arguments, dict):
        return []
    candidates: list[Candidate] = []
    if name in ('Read', 'Write', 'Edit', 'Grep', 'Glob'):
        for field in ('file_path', 'path'):
            value = arguments.get(field)
            if isinstance(value, str) and value and not find_secrets(value):
                candidates.append(Candidate(EntityKind.PATHS, value))
    if name == 'Bash' and isinstance(arguments.get('command'), str):
        command = _safe_text(arguments['command'])
        try:
            tokens = shlex.split(command)
        except ValueError:
            tokens = []
        for token in tokens:
            if token.startswith(('/', '~/', './', '../')):
                candidates.append(Candidate(EntityKind.PATHS, token.rstrip(';')))
            else:
                candidates.extend(extract(token))
    if 'request_access' in name:
        for field in ('app', 'apps', 'application', 'application_name', 'app_name', 'bundle_id'):
            for value in _harvest_strings(arguments.get(field)):
                if value and not find_secrets(value):
                    candidates.append(Candidate(EntityKind.APPS, normalize(EntityKind.APPS, value)))
    return candidates


def _remote_results(blocks: list[dict[str, object]]) -> list[Candidate]:
    remote_ids = set()
    for block in blocks:
        arguments = block.get('input')
        if block.get('name') == 'Bash' and isinstance(arguments, dict):
            command = arguments.get('command')
            if isinstance(command, str) and re.search(r'\bgit\b[^\n]*\bremote\b', command):
                remote_ids.add(block.get('id'))
    candidates = []
    for block in blocks:
        if block.get('type') != 'tool_result' or block.get('tool_use_id') not in remote_ids:
            continue
        for text in _strings(block.get('content')):
            for candidate in extract(_safe_text(text)):
                if candidate.kind in (EntityKind.URLS, EntityKind.REPOS):
                    candidates.append(Candidate(EntityKind.REPOS, candidate.value))
    return candidates
