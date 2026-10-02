#!/usr/bin/env bash
# Content-free SessionStart pointer. Only active notes in the new layout count.
# Resolve work|person/<domain>/identity/identity.md by canonical repository_path,
# then the unique domain directory matching the Git basename. Ambiguity never
# chooses a project. Read-only; never follows nested symlinks, history or backup.
# Pending notes are reported separately, including updates inside .pending/.
# Errors fail open silently: a missing pointer must not block session startup.
set -uo pipefail
[ "${OMH_RUNTIME:-}" = "1" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0
# An unconfigured OMH_KB_ROOT (exit 3) is a missing pointer, not a startup failure. A broken
# configuration (any other failure) gets one warning line so it is never silent; startup continues.
KB_ROOT="$(python3 "$(dirname "${BASH_SOURCE[0]}")/../skills/kb-write/scripts/kb/adapters/paths.py" OMH_KB_ROOT 2>&1)"
STATUS=$?
[ "$STATUS" -eq 3 ] && exit 0
if [ "$STATUS" -ne 0 ]; then
  printf 'Configuração de paths do omh inválida: %s\n' "$(printf '%s\n' "$KB_ROOT" | tail -1)"
  exit 0
fi
python3 - "$KB_ROOT" "$PWD" 3<&0 <<'PY'
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

EXCLUDED = {'.history', 'backup', '.obsidian', '.trash'}
RESERVED = {'index.md', 'INSTRUCTION.md'}
NO_KB = 'Sem KB para este projeto; o `explorer` mapeia um sob demanda'


def frontmatter(path):
    result = {}
    with path.open(encoding='utf-8') as stream:
        if stream.readline().strip() != '---':
            return result
        size = 0
        for line in stream:
            size += len(line)
            if size > 65536 or line.strip() == '---':
                break
            if not line or line[0].isspace() or ':' not in line:
                continue
            key, value = line.split(':', 1)
            value = value.strip()
            if value.startswith('"'):
                value = json.loads(value)
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1].replace("''", "'")
            result[key] = value
    return result


def resolve_project(root, repository):
    matches = set()
    for scope in ('work', 'person'):
        for identity in (root / scope).glob('*/identity/identity.md'):
            if identity.is_symlink():
                continue
            data = frontmatter(identity)
            if data.get('status') != 'active' or data.get('type') != 'reference':
                continue
            declared = data.get('repository_path')
            if declared and Path(declared).is_absolute() and Path(declared).resolve() == repository:
                matches.add(identity.parent.parent)
    if len(matches) == 1:
        return matches.pop(), False
    directories = [root / scope / repository.name for scope in ('work', 'person')
                   if (root / scope / repository.name).is_dir()]
    if len(directories) == 1:
        return directories[0], True
    return None, False


def count_notes(project):
    active, pending, latest = 0, 0, ''
    for directory, folders, filenames in os.walk(project, followlinks=False):
        folders[:] = [name for name in folders if name not in EXCLUDED]
        for name in filenames:
            path = Path(directory) / name
            if name in RESERVED or path.is_symlink() or not name.endswith('.md'):
                continue
            parent_name = path.parent.parent.name if path.parent.name == '.pending' else path.parent.name
            if name != parent_name + '.md':
                continue
            data = frontmatter(path)
            if data.get('status') == 'pending':
                pending += 1
            elif data.get('status') == 'active' and '.pending' not in path.parts:
                active += 1
                try:
                    date = datetime.date.fromisoformat(str(data.get('created_at', ''))[:10])
                    latest = max(latest, date.isoformat())
                except ValueError:
                    pass
    return active, pending, latest or 'data desconhecida'


def main():
    payload = json.load(os.fdopen(3))
    cwd = payload.get('cwd') or sys.argv[2]
    result = subprocess.run(['git', '-C', cwd, 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True, timeout=1)
    if result.returncode:
        return
    repository = Path(result.stdout.strip()).resolve()
    project, fallback = resolve_project(Path(sys.argv[1]).expanduser(), repository)
    if project is None:
        print(NO_KB)
        return
    active, pending, latest = count_notes(project)
    if not active and not pending:
        print(NO_KB)
        return
    origin = ' (por diretório, sem nota de identidade)' if fallback else ''
    warning = f'; {pending} notas pendentes de revisão' if pending else ''
    print(f'KB deste projeto{origin}: {active} notas, última em {latest}{warning}; '
          'consulte a knowledge base antes de responder')


try:
    main()
except (OSError, ValueError, TypeError, AttributeError, subprocess.TimeoutExpired):
    pass
PY
exit 0
