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
#       1. scans `work/projects/*/identity/*.md` for ACTIVE `knowledge_type: project`
#          notes — a note carrying `status: deprecated` is skipped — and sorts the
#          matches into three precedence layers: `repository_path` equal to the Git
#          root (both sides canonicalized with `pwd -P`, so /var and /private/var on
#          macOS are the same directory), then `name` equal to the repository
#          basename, then an `aliases` entry equal to it. Scalars are compared after
#          stripping one layer of surrounding quotes, `aliases` is read in both the
#          inline (`[a, b]`) and block (`- a`) YAML forms, and every comparison is
#          whole-value: an alias never matches as a substring.
#          The first non-empty layer decides. Two DISTINCT projects inside that
#          layer are an ambiguity, and the pointer refuses to resolve from a note
#          rather than guessing which project the user meant; it falls through to
#          the directory convention below, whose line says it came from a directory.
#       2. DECISION (not in the issue text): if no note resolves, falls back to the
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
#   - No project resolved -> `Sem KB para este projeto; o \`explorer\` mapeia um sob
#     demanda`.
#   - Project resolved -> counts `*.md` files under the project directory, excluding
#     `index.md`, `log.md`, and the legacy `context.md`, and finds the newest
#     `created_at` (frontmatter value normalized by stripping surrounding quotes and
#     keeping only the `YYYY-MM-DD` date) -> one pt-BR line under 200 characters. The
#     line names how the project was resolved, so it never silently implies an
#     identity note that does not exist:
#       - resolved from the project note: `KB deste projeto: N notas, última em
#         <YYYY-MM-DD>; …`.
#       - resolved from the directory fallback: `KB deste projeto (por diretório,
#         sem nota de identidade): N notas, última em <YYYY-MM-DD>; …`.
#   - Traversal uses `find -H`: follow a symlink only when the resolved project
#     directory itself is the command-line root. Never follow nested symlinks into
#     external trees or cycles. This deliberately omits notes in symlinked topic
#     directories; preserving the KB containment boundary is safer than complete
#     traversal of externally located topics.
#   - The printed line names the knowledge base, never a mechanical interface. The
#     Codex native plugin packages skills and this hook but NO custom agents (see
#     `.codex-plugin/plugin.json` and README "Codex custom agents … are not plugin
#     components"), so naming the `knowledge-base` agent here would emit a call to
#     an interface that does not exist in a plugin-only Codex installation. How to
#     consult belongs to CLAUDE.md/AGENTS.md, which are installed exactly on the
#     surfaces where that agent exists. `explorer` stays nameable: it is a shared
#     skill on both surfaces. This deliberately diverges from the literal text of
#     issue #134 ("consulte pelo agent `knowledge-base`"); see the PR description.
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

# Strip surrounding blanks and one layer of matching single or double quotes from $1.
unquote() {
  printf '%s' "$1" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
    -e "s/^'\(.*\)'\$/\1/" -e 's/^"\(.*\)"$/\1/'
}

# Read scalar frontmatter field $2 out of frontmatter text $1, unquoted.
fm_field() {
  unquote "$(printf '%s\n' "$1" | sed -n "s/^${2}:[[:space:]]*//p" | head -1)"
}

# Emit the `aliases` of frontmatter text $1, one unquoted alias per line. Handles
# the inline form (`aliases: [a, b]`) and the block form (`aliases:` then `  - a`).
fm_aliases() {
  local fm inline item
  fm="$1"
  inline=$(printf '%s\n' "$fm" |
    sed -n 's/^aliases:[[:space:]]*\[\(.*\)\][[:space:]]*$/\1/p' | head -1)
  if [ -n "$inline" ]; then
    # `printf '%s\n'`, not `%s`: `read` drops a trailing line with no newline, which
    # would silently swallow a single-element list and the last item of every list.
    printf '%s\n' "$inline" | tr ',' '\n' | while IFS= read -r item; do
      item=$(unquote "$item")
      [ -n "$item" ] && printf '%s\n' "$item"
    done
    return
  fi
  printf '%s\n' "$fm" | awk '
    /^aliases:[[:space:]]*$/ { inblock = 1; next }
    inblock && /^[[:space:]]+-[[:space:]]*/ { sub(/^[[:space:]]*-[[:space:]]*/, ""); print; next }
    inblock { exit }
  ' | while IFS= read -r item; do
    item=$(unquote "$item")
    [ -n "$item" ] && printf '%s\n' "$item"
  done
}

# Canonical absolute path of $1 (symlinks resolved), or empty when it does not resolve.
canonical() {
  [ -n "$1" ] || return 0
  (cd "$1" 2>/dev/null && pwd -P) 2>/dev/null
}

# Parse every identity note in one awk process. A record uses ASCII file
# separator (0x1c), which cannot occur in a valid YAML scalar here. The
# single-pass parser keeps SessionStart inside its two-second budget.
scan_identities() {
  awk -v basename="$BASENAME" '
    function trim(value) {
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      return value
    }
    function unquote(value, first, last) {
      value = trim(value)
      first = substr(value, 1, 1)
      last = substr(value, length(value), 1)
      if (length(value) >= 2 && ((first == "\"" && last == "\"") ||
          (first == "\047" && last == "\047"))) {
        return substr(value, 2, length(value) - 2)
      }
      return value
    }
    function reset_note() {
      boundary = 0
      knowledge_type = ""
      status = ""
      name = ""
      repository_path = ""
      alias_match = 0
      alias_block = 0
    }
    function finish_note(file, project_dir) {
      if (file == "" || knowledge_type != "project" || status == "deprecated") return
      project_dir = file
      sub("/identity/[^/]+$", "", project_dir)
      printf "%s%c%s%c%d%c%d\n", project_dir, 28, repository_path, 28,
        (name == basename), 28, alias_match
    }
    FNR == 1 {
      if (previous_file != "") finish_note(previous_file)
      previous_file = FILENAME
      reset_note()
    }
    /^---[[:space:]]*$/ { boundary++; alias_block = 0; next }
    boundary != 1 { next }
    alias_block && /^[[:space:]]+-[[:space:]]*/ {
      value = $0
      sub(/^[[:space:]]*-[[:space:]]*/, "", value)
      if (unquote(value) == basename) alias_match = 1
      next
    }
    alias_block { alias_block = 0 }
    /^knowledge_type:[[:space:]]*/ {
      value = $0; sub(/^knowledge_type:[[:space:]]*/, "", value)
      knowledge_type = unquote(value); next
    }
    /^status:[[:space:]]*/ {
      value = $0; sub(/^status:[[:space:]]*/, "", value)
      status = unquote(value); next
    }
    /^name:[[:space:]]*/ {
      value = $0; sub(/^name:[[:space:]]*/, "", value)
      name = unquote(value); next
    }
    /^repository_path:[[:space:]]*/ {
      value = $0; sub(/^repository_path:[[:space:]]*/, "", value)
      repository_path = unquote(value); next
    }
    /^aliases:[[:space:]]*/ {
      value = $0; sub(/^aliases:[[:space:]]*/, "", value)
      value = trim(value)
      if (value == "") { alias_block = 1; next }
      if (value ~ /^\[.*\]$/) {
        value = substr(value, 2, length(value) - 2)
        count = split(value, aliases, ",")
        for (alias_index = 1; alias_index <= count; alias_index++) {
          if (unquote(aliases[alias_index]) == basename) alias_match = 1
        }
      }
      next
    }
    END { finish_note(previous_file) }
  ' "$@" 2>/dev/null
}

GIT_ROOT_REAL=$(canonical "$GIT_ROOT")
[ -n "$GIT_ROOT_REAL" ] || GIT_ROOT_REAL="$GIT_ROOT"

BY_PATH=""
BY_NAME=""
BY_ALIAS=""

shopt -s nullglob
while IFS=$'\034' read -r project_dir repository_path name_match alias_match; do
  path_match=0
  if [ -n "$repository_path" ]; then
    if [ "$repository_path" = "$GIT_ROOT" ] || [ "$repository_path" = "$GIT_ROOT_REAL" ]; then
      path_match=1
    else
      repository_real=$(canonical "$repository_path")
      [ -n "$repository_real" ] && [ "$repository_real" = "$GIT_ROOT_REAL" ] && path_match=1
    fi
  fi

  if [ "$path_match" -eq 1 ]; then
    BY_PATH="$BY_PATH$project_dir
"
  elif [ "$name_match" -eq 1 ]; then
    BY_NAME="$BY_NAME$project_dir
"
  elif [ "$alias_match" -eq 1 ]; then
    BY_ALIAS="$BY_ALIAS$project_dir
"
  fi
done < <(scan_identities "$KB_ROOT"/work/projects/*/identity/*.md)
shopt -u nullglob

PROJECT_DIR=""
RESOLVED_BY=""

# The first non-empty layer decides; more than one distinct project in it is an
# ambiguity that must not be guessed, so the note path is abandoned entirely.
for layer in "$BY_PATH" "$BY_NAME" "$BY_ALIAS"; do
  [ -n "$layer" ] || continue
  unique=$(printf '%s' "$layer" | grep -v '^$' | sort -u)
  if [ "$(printf '%s\n' "$unique" | grep -c .)" -eq 1 ]; then
    PROJECT_DIR="$unique"
    RESOLVED_BY="note"
  fi
  break
done

if [ -z "$PROJECT_DIR" ] && [ -d "$KB_ROOT/work/projects/$BASENAME" ]; then
  PROJECT_DIR="$KB_ROOT/work/projects/$BASENAME"
  RESOLVED_BY="directory"
fi

if [ -z "$PROJECT_DIR" ]; then
  printf 'Sem KB para este projeto; o `explorer` mapeia um sob demanda\n'
  exit 0
fi

COUNT=0
LATEST=""

valid_date() {
  local value year month day max_day
  value="$1"
  [[ "$value" =~ ^([0-9]{4})-([0-9]{2})-([0-9]{2})$ ]] || return 1
  year=$((10#${BASH_REMATCH[1]}))
  month=$((10#${BASH_REMATCH[2]}))
  day=$((10#${BASH_REMATCH[3]}))
  [ "$month" -ge 1 ] && [ "$month" -le 12 ] || return 1
  case "$month" in
    1 | 3 | 5 | 7 | 8 | 10 | 12) max_day=31 ;;
    4 | 6 | 9 | 11) max_day=30 ;;
    2)
      max_day=28
      if { [ $((year % 4)) -eq 0 ] && [ $((year % 100)) -ne 0 ]; } ||
        [ $((year % 400)) -eq 0 ]; then
        max_day=29
      fi
      ;;
  esac
  [ "$day" -ge 1 ] && [ "$day" -le "$max_day" ]
}
while IFS= read -r -d '' note_file; do
  case "$(basename "$note_file")" in
    index.md | log.md | context.md) continue ;;
  esac
  COUNT=$((COUNT + 1))
  note_fm=$(frontmatter "$note_file")
  clean_date=$(fm_field "$note_fm" "created_at")
  short_date="${clean_date:0:10}"
  if valid_date "$short_date" && { [ -z "$LATEST" ] || [[ "$short_date" > "$LATEST" ]]; }; then
    LATEST="$short_date"
  fi
done < <(find -H "$PROJECT_DIR" -type f -name '*.md' -print0 2>/dev/null)

if [ "$COUNT" -eq 0 ]; then
  printf 'Sem KB para este projeto; o `explorer` mapeia um sob demanda\n'
  exit 0
fi

[ -n "$LATEST" ] || LATEST="data desconhecida"

if [ "$RESOLVED_BY" = "directory" ]; then
  printf 'KB deste projeto (por diretório, sem nota de identidade): %s notas, última em %s; consulte a knowledge base antes de responder sobre este projeto\n' \
    "$COUNT" "$LATEST"
else
  printf 'KB deste projeto: %s notas, última em %s; consulte a knowledge base antes de responder sobre este projeto\n' \
    "$COUNT" "$LATEST"
fi
exit 0
