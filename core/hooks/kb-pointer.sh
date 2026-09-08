#!/usr/bin/env bash
# One-line KB pointer — SessionStart hook.
#
# Replaces the old context.md snapshot injected on every session open (removed by
# #133) with a single line pointing at the knowledge base, so the agent consults it
# just-in-time (see CLAUDE.md/AGENTS.md, "Antes de responder") instead of reading a
# stale full dump at startup.
#
# CONTRACT
#   - `OMH_RUNTIME=1` exits silently before anything else runs — a non-interactive
#     runtime never needs the pointer.
#   - KB root: `${OMH_KB_ROOT:-$HOME/knowledge-base}`. `OMH_KB_ROOT` exists only to
#     make this hook testable against a temporary knowledge base; production runs
#     read the real `$HOME/knowledge-base`.
#   - Project resolution reads `.cwd` from the SessionStart JSON on stdin (via `jq`
#     when available; otherwise `$PWD`, ignoring the provided `.cwd` — a project
#     cannot be resolved from a payload this script cannot parse), resolves the Git
#     root, then:
#       1. looks for an active `knowledge_type: project` note under
#          `work/projects/*/identity/*.md` whose `repository_path` equals the Git
#          root, or whose `name`/`aliases` matches the repository basename;
#       2. DECISION (not in the issue text): if no note exists, falls back to the
#          conventional `work/projects/<basename>/` directory when it exists. The
#          issue only says "resolve the project through the project note"; without
#          this fallback the hook would print "Sem KB" for this very repository on
#          this machine, because the lazy migration from #133 has not created a
#          note here yet. Documented here and in the PR description. This fallback
#          is a concern of this hook only — no skill (`explorer`, `kb-retrieval`,
#          `kb-write`) mirrors or describes it, to avoid recreating the byte-level
#          coupling between the hook and the skills that #133 just removed.
#   - Never reads the legacy `work/projects/*/context.md` snapshot: that file is
#     evidence for the `knowledge-base` agent's one-shot migration (#133), not for
#     this hook.
#   - No project resolved -> `Sem KB para este projeto; o \`explorer\` cria uma sob
#     demanda`.
#   - Project resolved -> counts `*.md` files under the project directory, excluding
#     `index.md`, `log.md`, and the legacy `context.md`, and finds the newest
#     `created_at` (frontmatter value normalized by stripping surrounding quotes and
#     keeping only the `YYYY-MM-DD` date) -> one pt-BR line under 200 characters. The
#     line names how the project was resolved, so it never silently implies an
#     identity note that does not exist:
#       - resolved from the project note: `KB deste projeto: N notas, última em
#         <YYYY-MM-DD>; consulte pelo agent \`knowledge-base\``.
#       - resolved from the directory fallback: `KB deste projeto (por diretório,
#         sem nota de identidade): N notas, última em <YYYY-MM-DD>; consulte pelo
#         agent \`knowledge-base\``.
#   - Never prints an absolute machine path or a Git remote.
#
# FAIL-OPEN BY CONSTRUCTION: every error path exits 0 with no output. A pointer hook
# that breaks a session start is worse than a missing pointer, so nothing here ever
# blocks or throws — see `quiet` below.
#
# Written for bash 3.2 (macOS default): no associative arrays, no mapfile.

set -uo pipefail

quiet() { exit 0; }

[ "${OMH_RUNTIME:-}" = "1" ] && quiet

KB_ROOT="${OMH_KB_ROOT:-$HOME/knowledge-base}"

INPUT=$(cat 2>/dev/null) || quiet

CWD=""
if command -v jq >/dev/null 2>&1; then
  CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null) || CWD=""
fi
[ -n "$CWD" ] || CWD="$PWD"

GIT_ROOT=$(cd "$CWD" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null) || quiet
[ -n "$GIT_ROOT" ] || quiet

BASENAME=$(basename "$GIT_ROOT")

# Read the first YAML frontmatter block (between the first two `---` lines) of $1.
frontmatter() {
  awk 'BEGIN{c=0} /^---[[:space:]]*$/{c++; next} c==1{print} c>=2{exit}' "$1" 2>/dev/null
}

# Read frontmatter field $2 out of frontmatter text $1, first match, trimmed.
fm_field() {
  printf '%s\n' "$1" | sed -n "s/^${2}:[[:space:]]*//p" | head -1
}

PROJECT_DIR=""
RESOLVED_BY=""

shopt -s nullglob
for identity_file in "$KB_ROOT"/work/projects/*/identity/*.md; do
  fm=$(frontmatter "$identity_file")
  [ "$(fm_field "$fm" "knowledge_type")" = "project" ] || continue
  repository_path=$(fm_field "$fm" "repository_path")
  name=$(fm_field "$fm" "name")
  aliases=$(fm_field "$fm" "aliases")
  if [ "$repository_path" = "$GIT_ROOT" ] || [ "$name" = "$BASENAME" ] \
    || printf '%s' "$aliases" | grep -qF "$BASENAME"; then
    PROJECT_DIR=$(dirname "$(dirname "$identity_file")")
    RESOLVED_BY="note"
    break
  fi
done
shopt -u nullglob

if [ -z "$PROJECT_DIR" ] && [ -d "$KB_ROOT/work/projects/$BASENAME" ]; then
  PROJECT_DIR="$KB_ROOT/work/projects/$BASENAME"
  RESOLVED_BY="directory"
fi

if [ -z "$PROJECT_DIR" ]; then
  printf 'Sem KB para este projeto; o `explorer` cria uma sob demanda\n'
  exit 0
fi

COUNT=0
LATEST=""

while IFS= read -r -d '' note_file; do
  case "$(basename "$note_file")" in
    index.md | log.md | context.md) continue ;;
  esac
  COUNT=$((COUNT + 1))
  note_fm=$(frontmatter "$note_file")
  raw_date=$(fm_field "$note_fm" "created_at")
  clean_date=$(printf '%s' "$raw_date" | sed -e "s/^'//" -e "s/'\$//" -e 's/^"//' -e 's/"$//')
  short_date="${clean_date:0:10}"
  if [ -n "$short_date" ] && { [ -z "$LATEST" ] || [[ "$short_date" > "$LATEST" ]]; }; then
    LATEST="$short_date"
  fi
done < <(find "$PROJECT_DIR" -type f -name '*.md' -print0 2>/dev/null)

if [ "$COUNT" -eq 0 ]; then
  printf 'Sem KB para este projeto; o `explorer` cria uma sob demanda\n'
  exit 0
fi

[ -n "$LATEST" ] || LATEST="data desconhecida"

if [ "$RESOLVED_BY" = "directory" ]; then
  printf 'KB deste projeto (por diretório, sem nota de identidade): %s notas, última em %s; consulte pelo agent `knowledge-base`\n' \
    "$COUNT" "$LATEST"
else
  printf 'KB deste projeto: %s notas, última em %s; consulte pelo agent `knowledge-base`\n' \
    "$COUNT" "$LATEST"
fi
exit 0
