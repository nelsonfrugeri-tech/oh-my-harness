#!/usr/bin/env bash
# Commit quality gate — PreToolUse hook for `git commit`.
#
# Makes the CLAUDE.md commit rule executable: format -> lint -> typecheck -> test,
# with the command *discovered*, never hardcoded. Discovery ladder, first hit wins:
#
#   1. .claude/quality-gate.json in the repo   (explicit, per project)
#   2. Makefile targets of the same name
#   3. Language default, from the manifest present in the repo root
#
# A check with no discoverable command is skipped, not failed — a repo without a
# test suite must never be un-committable. If nothing is discovered, the gate allows.
#
# FAIL-OPEN BY CONSTRUCTION: every error path defers. A gate that blocks the user
# because of its own bug is worse than no gate, so `deny` is reachable only from a
# project command that actually exited non-zero.
#
# TRUST: every command it runs comes from the repository (Makefile targets, config
# strings, test suites). PreToolUse fires *before* the permission prompt, so running
# them automatically would execute repo-controlled code with no human approval. The
# gate therefore only engages in repos explicitly trusted by the user — see
# `trust_marker` below.
#
# Written for bash 3.2 (macOS default): no associative arrays, no mapfile.

set -uo pipefail

CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/omh-quality-gate"

# ---------------------------------------------------------------- hook plumbing

# Emit a decision and exit. $1 = allow|deny|ask, $2 = reason.
decide() {
  jq -n --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:$d,permissionDecisionReason:$r}}'
  exit 0
}

# Fall through to the normal permission flow. Used for every "not our business"
# and every internal error.
defer() { exit 0; }

INPUT=$(cat 2>/dev/null) || defer
command -v jq >/dev/null 2>&1 || defer

CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
TOOL_CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Self-filter. The shared plugin hook targets every Bash call because Codex does not
# support command-level `if` expressions, so this is the primary `git commit` filter.
# It also protects against any other harness configuration with a broader matcher.
printf '%s' "$TOOL_CMD" | grep -qE '(^|[;&|]|&&|\|\|)[[:space:]]*([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*git[[:space:]]+(-[^[:space:]]+[[:space:]]+)*commit([[:space:]]|$)' || defer

# Escape hatch. The prefix form (`OMH_GATE=off git commit …`) sets the variable on the
# *committing* process, which this hook never inherits — so read it off the command
# string too, not just our own environment.
# Anchored at the start on purpose: a commit *message* mentioning OMH_GATE=off must not
# grant the bypass.
if [ "${OMH_GATE:-}" = "off" ] || printf '%s' "$TOOL_CMD" | grep -qE '^[[:space:]]*OMH_GATE=off[[:space:]]'; then
  decide allow "Quality gate bypassed via OMH_GATE=off. This commit was NOT verified."
fi

[ -n "$CWD" ] && cd "$CWD" 2>/dev/null

# ---------------------------------------------------------------- preconditions

git rev-parse --git-dir >/dev/null 2>&1 || defer
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || defer
cd "$REPO_ROOT" 2>/dev/null || defer

# Digest of stdin, or empty if no hasher is available.
sha() { shasum -a 256 2>/dev/null | cut -d' ' -f1 || sha256sum 2>/dev/null | cut -d' ' -f1; }

# Identify the repository by its COMMON git dir, not by the checkout path: every
# `git worktree` of a repo shares it. Keying on the checkout would make each worktree
# a separate, untrusted repo — silently disabling the gate in the workflow the harness
# itself uses most.
GIT_COMMON=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
[ -z "$GIT_COMMON" ] && GIT_COMMON="$REPO_ROOT"
REPO_SIG=$(printf '%s' "$GIT_COMMON" | sha | cut -c1-12)
[ -z "$REPO_SIG" ] && defer

# Trust gate. Without an explicit opt-in we never execute anything from this repo.
TRUST_MARKER="$CACHE_DIR/trusted/$REPO_SIG"
if [ ! -f "$TRUST_MARKER" ]; then
  defer
fi

# Mid-merge or mid-rebase: the content was gated when authored; gating the merge
# commit again only blocks conflict resolution.
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null) || defer
if [ -e "$GIT_DIR/MERGE_HEAD" ] || [ -d "$GIT_DIR/rebase-merge" ] || [ -d "$GIT_DIR/rebase-apply" ]; then
  defer
fi

# `git commit -a` stages tracked changes itself, so an empty index does not mean an
# empty commit. Only treat "nothing staged" as "nothing to do" when -a is absent.
COMMIT_ALL=no
printf '%s' "$TOOL_CMD" | grep -qE '(^|[[:space:]])(-[a-zA-Z]*a[a-zA-Z]*|--all)([[:space:]]|$)' && COMMIT_ALL=yes
if [ "$COMMIT_ALL" = no ]; then
  git diff --cached --quiet 2>/dev/null && defer
fi

# ---------------------------------------------------------------- run cache

if [ "$COMMIT_ALL" = yes ]; then
  CONTENT_SIG=$(git diff HEAD --binary 2>/dev/null | sha)
else
  CONTENT_SIG=$(git diff --cached --binary 2>/dev/null | sha)
fi
HEAD_SIG=$(git rev-parse HEAD 2>/dev/null || echo "root")
CACHE_FILE="$CACHE_DIR/$REPO_SIG"

# An empty signature means hashing failed; never let that collapse into a key that
# matches everything.
if [ -n "$CONTENT_SIG" ] && [ -f "$CACHE_FILE" ]; then
  if [ "$(cat "$CACHE_FILE" 2>/dev/null)" = "$HEAD_SIG:$CONTENT_SIG" ]; then
    decide allow "Quality gate already passed for this exact content."
  fi
fi

# ---------------------------------------------------------------- discovery

CONFIG=".claude/quality-gate.json"

has_make_target() {
  for mf in Makefile makefile GNUmakefile; do
    [ -f "$mf" ] && grep -qE "^$1[[:space:]]*:" "$mf" 2>/dev/null && return 0
  done
  return 1
}

has_npm_script() {
  [ -f package.json ] || return 1
  jq -e --arg s "$1" '.scripts[$s] // empty' package.json >/dev/null 2>&1
}

# Is a Python tool actually runnable here, without touching the repo? Echoes the
# invocation, or nothing.
#
# Deliberately does NOT go through `uv run`: it creates `.venv/` in the working tree
# even with `--frozen --no-sync`, and a hook must never write inside the user's repo.
# An unsynced uv project therefore yields no command — which is the correct fail-open
# answer, not a failure.
py_cmd() {
  tool="$1"; args="$2"
  [ -x ".venv/bin/$tool" ] && { echo ".venv/bin/$tool $args"; return; }
  command -v "$tool" >/dev/null 2>&1 && echo "$tool $args"
}

# Only impose a Python default when the project actually configured that tool —
# otherwise the first commit is blocked by pre-existing debt the project never opted into.
py_configured() {
  [ -f pyproject.toml ] || return 1
  grep -qE "^\[tool\.$1" pyproject.toml 2>/dev/null
}

js_runner() {
  [ -f pnpm-lock.yaml ] && command -v pnpm >/dev/null 2>&1 && { echo "pnpm run"; return; }
  command -v npm >/dev/null 2>&1 && echo "npm run"
}

resolve() {
  kind="$1"

  if [ -f "$CONFIG" ]; then
    cmd=$(jq -r --arg k "$kind" '.[$k] // empty' "$CONFIG" 2>/dev/null)
    [ -n "$cmd" ] && { echo "$cmd"; return; }
  fi

  has_make_target "$kind" && { echo "make $kind"; return; }

  if [ -f pyproject.toml ] || [ -f setup.py ]; then
    case "$kind" in
      format)    py_configured ruff && py_cmd ruff "format --check ." ;;
      lint)      py_configured ruff && py_cmd ruff "check ." ;;
      typecheck) py_configured mypy && py_cmd mypy "." ;;
      # pytest exits 5 for "no tests ran". Having pytest installed must not make a repo
      # with no tests un-committable — that is the invariant this whole gate rests on.
      test)      base=$(py_cmd pytest "-q"); [ -n "$base" ] && \
                 echo "$base; rc=\$?; [ \"\$rc\" -eq 5 ] && exit 0; exit \$rc" ;;
    esac
    return
  fi

  if [ -f package.json ]; then
    r=$(js_runner); [ -z "$r" ] && return
    has_npm_script "$kind" && echo "$r $kind"
    return
  fi

  if [ -f go.mod ]; then
    command -v go >/dev/null 2>&1 || return
    # Same reasoning as the pytest case: a module with no .go files makes `go vet`
    # and `go test` fail with "matched no packages", which is not a quality failure.
    [ -n "$(find . -name '*.go' -not -path './vendor/*' -print -quit 2>/dev/null)" ] || return
    case "$kind" in
      format) echo 'test -z "$(gofmt -l .)"' ;;
      lint)   echo "go vet ./..." ;;
      test)   echo "go test ./..." ;;
    esac
    return
  fi

  if [ -f Cargo.toml ]; then
    command -v cargo >/dev/null 2>&1 || return
    case "$kind" in
      format) echo "cargo fmt --check" ;;
      lint)   echo "cargo clippy -- -D warnings" ;;
      test)   echo "cargo test" ;;
    esac
    return
  fi
}

# Run one project command in a clean shell. Our `set -uo pipefail` must not leak into
# it: a project command that legitimately uses an unset var or a failing pipe segment
# would otherwise "fail" and block the commit.
run_check() {
  bash -c "$1" 2>&1
}

# ---------------------------------------------------------------- run

RAN=""
for kind in format lint typecheck test; do
  cmd=$(resolve "$kind")
  [ -z "$cmd" ] && continue
  out=$(run_check "$cmd"); rc=$?
  if [ "$rc" -ne 0 ]; then
    decide deny "Quality gate FAILED at ${kind}: \`${cmd}\`

$(printf '%s' "$out" | tail -25)

Fix it, stage the fix, and commit again. Emergency bypass (commit is NOT verified): prefix the command with OMH_GATE=off"
  fi
  RAN="$RAN $kind"
done

if [ -f "$CONFIG" ]; then
  i=0
  while :; do
    cmd=$(jq -r --argjson i "$i" '.extra[$i] // empty' "$CONFIG" 2>/dev/null)
    [ -z "$cmd" ] && break
    out=$(run_check "$cmd"); rc=$?
    if [ "$rc" -ne 0 ]; then
      decide deny "Quality gate FAILED on a project check: \`${cmd}\`

$(printf '%s' "$out" | tail -25)"
    fi
    RAN="$RAN extra[$i]"
    i=$((i + 1))
  done
fi

if [ -z "$RAN" ]; then
  decide allow "Quality gate found no format/lint/typecheck/test command for this repo — nothing to verify."
fi

if [ -n "$CONTENT_SIG" ]; then
  mkdir -p "$CACHE_DIR" 2>/dev/null
  printf '%s' "$HEAD_SIG:$CONTENT_SIG" > "$CACHE_FILE" 2>/dev/null
fi

decide allow "Quality gate passed:${RAN}."
