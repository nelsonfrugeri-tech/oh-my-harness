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
# An unconfigured OMH_KB_ROOT (resolver exit 3) means no bundle to guard: fail open, as the
# pointer does. Any other resolver failure is a broken configuration: the bundle is unknown, so
# every Markdown write is denied with the resolver's reason, and other files — including the
# config file that fixes it — stay writable.
RESOLVED="$(python3 "$(dirname "${BASH_SOURCE[0]}")/../skills/kb-write/scripts/kb/adapters/paths.py" OMH_KB_ROOT 2>&1)"
STATUS=$?
[ "$STATUS" -eq 3 ] && exit 0
# The config destination comes only from the resolver; empty when HOME/XDG cannot locate it.
CONFIG="$(python3 "$(dirname "${BASH_SOURCE[0]}")/../skills/kb-write/scripts/kb/adapters/paths.py" --config-file 2>/dev/null)"
# Which layer supplied the bad value, also from the resolver: environment, config, or none.
SOURCE="$(python3 "$(dirname "${BASH_SOURCE[0]}")/../skills/kb-write/scripts/kb/adapters/paths.py" --source OMH_KB_ROOT 2>/dev/null)"
python3 - "$STATUS" "$RESOLVED" "$PWD" "$CONFIG" "$SOURCE" 3<&0 <<'PY'
import json
import os
from pathlib import Path
import sys


def deny(reason):
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
          'permissionDecision': 'deny', 'permissionDecisionReason': reason}}, ensure_ascii=False))


def is_markdown(*paths):
    return any(path.suffix.casefold() == '.md' for path in paths)


def unresolved(error, config, origin, lexical, canonical):
    located = Path(config) if config else None
    if located in (lexical, canonical) or not is_markdown(lexical, canonical):
        return
    reason = (error.strip().splitlines() or ['erro desconhecido'])[-1]
    if origin == 'environment':
        fix = ('corrija ou remova a variável de ambiente OMH_KB_ROOT; ela vence o arquivo de config, '
               'então editar o arquivo não resolve')
    elif located:
        fix = f'corrija a linha de OMH_KB_ROOT em {located}'
    else:
        fix = 'corrija HOME ou XDG_CONFIG_HOME para que o arquivo de config possa ser localizado'
    deny(f'Não foi possível resolver OMH_KB_ROOT ({reason}); {fix}. '
         'Escritas de Markdown ficam bloqueadas até lá.')


def main():
    payload = json.load(os.fdopen(3))
    if payload.get('tool_name') not in ('Write', 'Edit'):
        return
    raw = payload.get('tool_input', {}).get('file_path')
    if not isinstance(raw, str) or not raw.strip():
        deny('Não foi possível validar o destino da escrita.')
        return
    cwd = Path(payload.get('cwd') or sys.argv[3])
    target = Path(raw).expanduser()
    if not target.is_absolute():
        target = cwd / target
    lexical = Path(os.path.abspath(target))
    canonical = target.resolve()
    if sys.argv[1] != '0':
        unresolved(sys.argv[2], sys.argv[4], sys.argv[5], lexical, canonical)
        return
    root = Path(os.path.abspath(Path(sys.argv[2]).expanduser()))
    protected = lexical.is_relative_to(root) or canonical.is_relative_to(root.resolve())
    if not protected and root.exists():
        protected = any(ancestor.exists() and ancestor.samefile(root)
                        for ancestor in (target, *target.parents))
    if protected and is_markdown(lexical, canonical):
        deny('Escrita direta de Markdown na knowledge base recusada. Use o agent knowledge-base '
             'e o CLI kb.py para validar, propor e aprovar a nota.')


try:
    main()
except (OSError, ValueError, TypeError, AttributeError, RuntimeError):
    deny('Não foi possível validar o destino da escrita. Use o CLI kb.py.')
PY
