#!/usr/bin/env bash
# Project context loader — SessionStart hook.
#
# Replaces a hook that only printed a reminder ("go run the context agent"), which cost a
# subagent spawn per session to essentially `cat` a file, and which was silently ignored:
# the context report for this very repository sat 14 commits and 20 days stale while the
# reminder fired every session.
#
# This one DELIVERS instead of asking. Deterministically, with no model in the loop, it:
#
#   1. injects the head of the existing snapshot, so the session starts with the project's
#      identity and stack already in context;
#   2. computes drift by comparing HEAD against the `last_hash` the report was generated
#      from, and asks for a DELTA run only when there is something to update.
#
# What it deliberately does NOT do is the analysis itself — that needs a model reading the
# repository, which is the `explorer` skill's job. So the ask survives, but scoped: it fires
# only on real drift, and it carries the number.
#
# Fully silent only outside a git repo (or when the project name cannot be derived). Without
# a report it prints the FULL ask; with no drift it still injects the snapshot — that is the
# point — but asks for nothing.
#
# Written for bash 3.2 (macOS default).

set -uo pipefail

KB_ROOT="${OMH_KB_ROOT:-$HOME/knowledge-base}"
MAX_BYTES="${OMH_CONTEXT_MAX_BYTES:-2500}"   # cap on the injected snapshot head

# Never let this hook disturb a session: any problem means say nothing.
quiet() { exit 0; }

git rev-parse --git-dir >/dev/null 2>&1 || quiet
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || quiet
[ -n "$REPO_ROOT" ] || quiet

# Same derivation the explorer skill uses: leaf directory name, lowercase-kebab.
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

# --- frontmatter ---------------------------------------------------------------
fm_value() { sed -n "s/^$1: *//p" "$REPORT" 2>/dev/null | head -1 | tr -d '\r'; }
LAST_HASH=$(fm_value last_hash)
GENERATED=$(fm_value generated_at)

# --- drift ---------------------------------------------------------------------
DRIFT=""
if [ -n "$LAST_HASH" ] && git cat-file -e "$LAST_HASH^{commit}" 2>/dev/null; then
  DRIFT=$(git rev-list --count "$LAST_HASH..HEAD" 2>/dev/null)
fi

# --- snapshot head -------------------------------------------------------------
# Everything from the living snapshot down. Only trim when the cap actually bites:
# dropping the trailing line unconditionally would amputate every snapshot small enough
# to fit. When it does bite, the trim also removes the line the byte cut landed inside,
# which is what keeps a multibyte character from being split into invalid UTF-8.
SECTION=$(awk '/^## Current snapshot/{f=1} f' "$REPORT" 2>/dev/null)
if [ "$(printf '%s' "$SECTION" | wc -c | tr -d ' ')" -gt "$MAX_BYTES" ] 2>/dev/null; then
  HEAD_TEXT=$(printf '%s' "$SECTION" | head -c "$MAX_BYTES" | sed '$d')
  TRUNCATED=yes
else
  HEAD_TEXT="$SECTION"
  TRUNCATED=no
fi

# A cap smaller than the first content line leaves nothing but the heading — print no block
# at all rather than an empty one. `wc -l` counts newlines, so heading-only is 0.
[ "$(printf '%s' "$HEAD_TEXT" | wc -l | tr -d ' ')" -lt 1 ] && HEAD_TEXT=""

TOTAL_LINES=$(wc -l < "$REPORT" 2>/dev/null | tr -d ' ')

# --- output --------------------------------------------------------------------
# No drift and nothing worth saying beyond the snapshot? Still inject the snapshot — it is
# the whole point — but say nothing that asks for work.
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
