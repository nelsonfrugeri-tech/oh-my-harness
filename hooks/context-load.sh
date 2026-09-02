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
O projeto \`$PROJECT\` ainda não possui um context report em \`$REPORT\`.
AÇÃO: Execute a skill \`explorer\` em modo **FULL**. Quando o adapter global estiver instalado, o
agent customizado \`context\` poderá orquestrar essa skill.
EOF
  exit 0
fi

fm_value() { sed -n "s/^$1: *//p" "$REPORT" 2>/dev/null | head -1 | tr -d '\r'; }
remote_identity() {
  REMOTE_VALUE=$1
  REMOTE_BASE=$2
  REMOTE_VALUE=$(printf '%s\n' "$REMOTE_VALUE" | sed -e 's/^"\(.*\)"$/\1/' -e "s/^'\\(.*\\)'$/\\1/")
  if [ -z "$REMOTE_VALUE" ] || [ "$REMOTE_VALUE" = null ]; then
    printf 'null\n'
    return
  fi
  REMOTE_SCHEME=
  case "$REMOTE_VALUE" in
    *://*) REMOTE_SCHEME=$(printf '%s' "${REMOTE_VALUE%%://*}" | tr '[:upper:]' '[:lower:]') ;;
  esac
  case "$REMOTE_VALUE" in
    file://localhost/*) REMOTE_VALUE=${REMOTE_VALUE#file://localhost} ;;
    file:///*) REMOTE_VALUE=${REMOTE_VALUE#file://} ;;
  esac
  case "$REMOTE_VALUE" in
    *://*|*:*|/*) ;;
    *) REMOTE_VALUE="$REMOTE_BASE/$REMOTE_VALUE" ;;
  esac
  REMOTE_ID=$(printf '%s\n' "$REMOTE_VALUE" |
    sed -E \
      -e 's#^[[:alpha:]][[:alnum:]+.-]*://([^/@]+@)?#//#' \
      -e 's#^([^/@]+@)?([^/:]+):#//\2/#' \
      -e 's#^//([^/]+)/#\1/#' \
      -e 's#[?#].*$##' \
      -e 's#/*$##' \
      -e 's#\.git$##')
  case "$REMOTE_ID" in
    /*) printf '%s\n' "$REMOTE_ID" ;;
    */*)
      REMOTE_HOST=${REMOTE_ID%%/*}
      REMOTE_PATH=${REMOTE_ID#*/}
      case "$REMOTE_SCHEME:$REMOTE_HOST" in
        ssh:*:22) REMOTE_HOST=${REMOTE_HOST%:22} ;;
        https:*:443) REMOTE_HOST=${REMOTE_HOST%:443} ;;
        http:*:80) REMOTE_HOST=${REMOTE_HOST%:80} ;;
        git:*:9418) REMOTE_HOST=${REMOTE_HOST%:9418} ;;
      esac
      printf '%s/%s\n' "$(printf '%s' "$REMOTE_HOST" | tr '[:upper:]' '[:lower:]')" "$REMOTE_PATH"
      ;;
    *) printf '%s\n' "$REMOTE_ID" | tr '[:upper:]' '[:lower:]' ;;
  esac
}
REPORT_REPO=$(sed -n 's/^> Repository: *//p' "$REPORT" 2>/dev/null | head -1 | tr -d '\r')
REPORT_REMOTE=$(fm_value remote_url)
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || true)
if [ -n "$REPORT_REPO" ] && [ -d "$REPORT_REPO" ]; then
  REPORT_REPO=$(cd "$REPORT_REPO" 2>/dev/null && pwd -P)
fi
REPO_ROOT=$(cd "$REPO_ROOT" 2>/dev/null && pwd -P) || quiet
REPORT_REMOTE_ID=$(remote_identity "$REPORT_REMOTE" "$REPORT_REPO")
CURRENT_REMOTE_ID=$(remote_identity "$CURRENT_REMOTE" "$REPO_ROOT")

SAME_REPOSITORY=no
if [ -n "$REPORT_REMOTE" ] && [ "$REPORT_REMOTE" != null ] && [ -n "$CURRENT_REMOTE" ]; then
  [ "$REPORT_REMOTE_ID" = "$CURRENT_REMOTE_ID" ] && SAME_REPOSITORY=yes
elif [ -n "$REPORT_REPO" ] && [ "$REPORT_REPO" = "$REPO_ROOT" ]; then
  SAME_REPOSITORY=yes
fi

if [ "$SAME_REPOSITORY" != yes ]; then
  printf '# omh-managed: context collision\n'
  printf 'O domain `%s` já pertence a outra identidade ou não possui identidade verificável.\n' "$DOMAIN"
  printf 'Esperado: remote identity `%s`, raiz `%s`; encontrado: remote identity `%s`, raiz `%s`.\n' \
    "${CURRENT_REMOTE_ID:-null}" "$REPO_ROOT" "${REPORT_REMOTE_ID:-null}" "${REPORT_REPO:-null}"
  printf 'AÇÃO: não carregue nem escreva neste domain até existir um resolver persistente compartilhado.\n'
  exit 0
fi

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
  COMMIT_WORD=commit
  [ "$DRIFT" -eq 1 ] || COMMIT_WORD=commits
  printf '\n**DRIFT: %s %s desde a última análise (`%s`).** O snapshot abaixo está desatualizado nessa medida.\n' \
    "$DRIFT" "$COMMIT_WORD" "$LAST_HASH"
  printf 'AÇÃO: Execute a skill `explorer` em modo **DELTA**. O agent customizado opcional `context` pode orquestrá-la.\n'
elif [ -z "$DRIFT" ]; then
  printf '\nNão foi possível calcular o drift (`last_hash` ausente ou fora deste repositório); trate o snapshot como potencialmente desatualizado.\n'
fi

if [ -n "$HEAD_TEXT" ]; then
  if [ "$TRUNCATED" = yes ]; then
    printf '\n--- snapshot (início; report completo no path acima) ---\n%s\n' "$HEAD_TEXT"
  else
    printf '\n--- snapshot ---\n%s\n' "$HEAD_TEXT"
  fi
fi

exit 0
