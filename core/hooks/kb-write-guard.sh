#!/usr/bin/env bash
# PreToolUse guard for Write/Edit Markdown destinations in the knowledge bundle.
# Both lexical and canonical paths are protected, including symlink aliases.
# This is a workflow reminder, not a filesystem security boundary: Bash, CLI and
# other tools are outside the Write|Edit matcher. kb.py owns validation/publishing.
# Parsing failures deny instead of making an unverified write appear permitted.
set -uo pipefail
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Não foi possível validar o destino da escrita: Python 3 indisponível."}}'
  exit 0
fi
python3 - "${OMH_KB_ROOT:-$HOME/knowledge-base}" "$PWD" 3<&0 <<'PY'
import json
import os
from pathlib import Path
import sys


def deny(reason):
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
          'permissionDecision': 'deny', 'permissionDecisionReason': reason}}, ensure_ascii=False))


def main():
    payload = json.load(os.fdopen(3))
    if payload.get('tool_name') not in ('Write', 'Edit'):
        return
    raw = payload.get('tool_input', {}).get('file_path')
    if not isinstance(raw, str) or not raw.strip():
        deny('Não foi possível validar o destino da escrita.')
        return
    cwd = Path(payload.get('cwd') or sys.argv[2])
    target = Path(raw).expanduser()
    if not target.is_absolute():
        target = cwd / target
    lexical = Path(os.path.abspath(target))
    root = Path(os.path.abspath(Path(sys.argv[1]).expanduser()))
    canonical = target.resolve()
    protected = lexical.is_relative_to(root) or canonical.is_relative_to(root.resolve())
    if protected and (lexical.suffix.casefold() == '.md' or canonical.suffix.casefold() == '.md'):
        deny('Escrita direta de Markdown na knowledge base recusada. Use o agent knowledge-base '
             'e o CLI kb.py para validar, propor e aprovar a nota.')


try:
    main()
except (OSError, ValueError, TypeError, AttributeError, RuntimeError):
    deny('Não foi possível validar o destino da escrita. Use o CLI kb.py.')
PY
