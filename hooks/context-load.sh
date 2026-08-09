#!/usr/bin/env bash
# Shared SessionStart context loader for every harness adapter.
#
# It injects the existing snapshot immediately and requests model-backed analysis only when the
# report is missing or Git drift proves that it is stale. The hook itself never writes context.

set -uo pipefail

KB_ROOT="${OMH_KB_ROOT:-$HOME/knowledge-base}"
MAX_BYTES="${OMH_CONTEXT_MAX_BYTES:-2500}"

# A lifecycle hook must never prevent the harness from starting.
quiet() { exit 0; }

git rev-parse --git-dir >/dev/null 2>&1 || quiet
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || quiet
[ -n "$REPO_ROOT" ] || quiet

# Keep this derivation byte-for-byte aligned with the explorer skill and context agents.
PROJECT=$(basename "$REPO_ROOT" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-\n' '-' | sed 's/--*/-/g; s/^-//; s/-$//')
[ -n "$PROJECT" ] || quiet

DOMAIN="work/projects/$PROJECT"
REPORT="$KB_ROOT/$DOMAIN/context.md"

if [ ! -f "$REPORT" ]; then
  cat <<EOF
# omh-managed: context
Projeto \`$PROJECT\` ainda não tem context report em \`$REPORT\`.
AÇÃO: invoque o agent \`context\` para rodar a skill \`explorer\` em modo **FULL**.
EOF
  exit 0
fi

fm_value() { sed -n "s/^$1: *//p" "$REPORT" 2>/dev/null | head -1 | tr -d '\r'; }
LAST_HASH=$(fm_value last_hash)
GENERATED=$(fm_value generated_at)

DRIFT=""
if [ -n "$LAST_HASH" ] && git cat-file -e "$LAST_HASH^{commit}" 2>/dev/null; then
  DRIFT=$(git rev-list --count "$LAST_HASH..HEAD" 2>/dev/null)
fi

SECTION=$(awk '/^## Current snapshot/{f=1} f' "$REPORT" 2>/dev/null)
if [ "$(printf '%s' "$SECTION" | wc -c | tr -d ' ')" -gt "$MAX_BYTES" ] 2>/dev/null; then
  HEAD_TEXT=$(printf '%s' "$SECTION" | head -c "$MAX_BYTES" | sed '$d')
  TRUNCATED=yes
else
  HEAD_TEXT="$SECTION"
  TRUNCATED=no
fi

[ "$(printf '%s' "$HEAD_TEXT" | wc -l | tr -d ' ')" -lt 1 ] && HEAD_TEXT=""
TOTAL_LINES=$(wc -l < "$REPORT" 2>/dev/null | tr -d ' ')

printf '# omh-managed: context\n'
printf 'Projeto `%s` · report gerado em %s · %s linhas em `%s`\n' \
  "$PROJECT" "${GENERATED:-?}" "${TOTAL_LINES:-?}" "$REPORT"

if [ -n "$DRIFT" ] && [ "$DRIFT" -gt 0 ] 2>/dev/null; then
  printf '\n**DRIFT: %s commits desde a última análise (`%s`).** O snapshot abaixo está desatualizado nesse tanto.\n' "$DRIFT" "$LAST_HASH"
  printf 'AÇÃO: invoque o agent `context` para rodar a skill `explorer` em modo **DELTA**.\n'
elif [ -z "$DRIFT" ]; then
  printf '\nDrift não calculável (`last_hash` ausente ou fora deste repo) — trate o snapshot como possivelmente velho.\n'
fi

if [ -n "$HEAD_TEXT" ]; then
  if [ "$TRUNCATED" = yes ]; then
    printf '\n--- snapshot (início; relatório completo no path acima) ---\n%s\n' "$HEAD_TEXT"
  else
    printf '\n--- snapshot ---\n%s\n' "$HEAD_TEXT"
  fi
fi

exit 0
