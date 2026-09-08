#!/usr/bin/env bash
# PR quality gate — PreToolUse hook for opening a pull request.
#
# Makes the CLAUDE.md/AGENTS.md PR rule executable: format -> lint -> typecheck -> test,
# with the command *discovered*, never hardcoded, run against the exact content HEAD
# will send to the pull request. Discovery ladder, first hit wins:
#
#   1. .claude/quality-gate.json in the repo   (explicit, per project)
#   2. Makefile targets of the same name
#   3. Language default, from the manifest present in the repo root
#
# A check with no discoverable command is skipped, not failed — a repo without a
# test suite must never be un-PR-able. If nothing is discovered, the gate allows.
#
# FAIL-OPEN BY CONSTRUCTION: every error path defers. A gate that blocks the user
# because of its own bug is worse than no gate, so no internal failure ever produces
# a decision: `deny` is reachable only from a project command that exited non-zero or
# from a precondition the gate positively observed (dirty tree, unpushed or foreign
# head, mismatched target repository, divergent or unverifiable remote).
#
# WHY `deny` AND NOT `ask`: the two harnesses do not agree on `ask`. Codex documents
# that `permissionDecision: "ask"` is "parsed but not supported yet. Codex marks the
# hook run as failed, reports the error, and continues the tool call" — so on Codex an
# `ask` guard opens the pull request anyway. Claude Code prompts the user for `ask`,
# and in `claude -p` without a permission host there is nobody to answer, while the
# Agent SDK with `canUseTool` or `--permission-prompt-tool` routes the prompt and
# waits. `deny` is the only value whose blocking behaviour is supported and documented
# in both harnesses, and the two descriptors are byte-identical, so every guard uses
# it and states in its reason exactly what to do. The explicit emergency bypass
# remains the way through.
#
# TRUST: every command it runs comes from the repository (Makefile targets, config
# strings, test suites). PreToolUse fires *before* the permission prompt, so running
# them automatically would execute repo-controlled code with no human approval. The
# gate therefore only engages in repos explicitly trusted by the user — see
# `trust_marker` below.
#
# TRIGGER: fires on `gh pr create` (Bash) and on the GitHub MCP server's PR-creation
# tool (`mcp__github__create_pull_request`) — the two ways this harness opens a pull
# request. Commit and push are free: the gate no longer runs on `git commit`. A PR
# opened from the GitHub web UI or any other tool never invokes this hook — accepted,
# not a defect, because the harness only governs the actors it runs (see
# harness/*/CLAUDE.md and harness/*/AGENTS.md, "Fluxo de PR").
#
# WHAT THE GUARANTEE COVERS: the HEAD at the moment the pull request is opened, and
# nothing after it. A later `git push` on the branch, `gh pr ready`,
# `mcp__github__update_pull_request` and `gh api -X POST` on pull requests all pass
# without a gate — a design decision, not a gap: this hook governs creation, human
# review and CI govern what follows. Verified by execution: each of those commands
# returns no decision from this script.
#
# HEAD VALIDATION: both trigger paths can name an origin that is not the current
# checkout — `-H`/`--head` on the CLI (including the `owner:branch` cross-fork form),
# or the MCP tool's own `head`/`owner`/`repo` fields, which its schema marks required
# on every call. Validating the current checkout while a different origin is what
# actually ships would be validation by proxy, so the gate resolves the selected
# origin first and denies whenever it cannot reconcile it with the current checkout:
# a cross-fork head, a different local branch, or an MCP `owner/repo` that does not
# match the `origin` remote. An unparsable `origin` URL fails that specific check
# open (see `normalize_owner_repo`) rather than guessing.
#
# REMOTE FRESHNESS: the local `HEAD`-vs-upstream comparison only proves the tracking
# ref agrees with `HEAD`, not that the remote hasn't moved since the last fetch — a
# force-push leaves both stale in agreement and wrong. Before trusting that
# comparison, the gate makes one `git ls-remote` attempt against the tracked branch,
# budgeted to a hard ~10s wall-clock timeout (background job + poll + `kill -9`, never
# a hang on credentials: `GIT_TERMINAL_PROMPT=0`, `GIT_ASKPASS=true`, `SSH_ASKPASS=true`)
# and writing only to a `mktemp` file outside the repository. A reachable, divergent
# remote is denied; an unreachable remote is denied too, because the gate cannot
# establish what the PR will contain. The caller may use the explicit emergency bypass
# when that risk is understood.
#
# Written for bash 3.2 (macOS default): no associative arrays, no mapfile.

set -uo pipefail

CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/omh-quality-gate"
MCP_PR_TOOL="mcp__github__create_pull_request"

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
TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
TOOL_CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
MCP_HEAD=$(printf '%s' "$INPUT" | jq -r '.tool_input.head // empty' 2>/dev/null)
MCP_OWNER=$(printf '%s' "$INPUT" | jq -r '.tool_input.owner // empty' 2>/dev/null)
MCP_REPO=$(printf '%s' "$INPUT" | jq -r '.tool_input.repo // empty' 2>/dev/null)

# Two ways this harness opens a pull request: the `gh` CLI over Bash, or the GitHub
# MCP server's PR-creation tool. The MCP call carries no shell command, so it is
# identified by tool name instead of by regex.
#
# The Bash path is decided by a one-pass shell-aware scan instead of a regex over
# the raw first line. A regex anchored at the start of the first line let every
# chained, prefixed, parenthesised or absolute-path form through silently
# (`git push && gh pr create`, `git push; gh pr create`, `(gh pr create)`,
# `/opt/homebrew/bin/gh pr create`, `command gh pr create`), which is looser than
# Claude Code's own `if:` matcher — and on Codex, which has no `if:` condition, this
# script is the only guard.
#
# `matcher` itself is not the difference: Codex matches PreToolUse on `tool_name`
# exactly as Claude Code does, MCP tool names included, which is what makes the
# `mcp__github__create_pull_request` handler in the byte-identical descriptors work on
# both. Only the per-handler `if:` condition is Claude-Code-specific.
#
# `scan_command` walks the string once, honouring single quotes, double quotes and
# backslash escapes, splits it at every unquoted command separator, and stops at the
# first unquoted `<<` so a heredoc body is never read as a command. Each segment is
# then inspected in command position: leading `VAR=value` assignments and the
# command wrappers below are skipped, and the command word matches when it is `gh`
# or ends in `/gh`. Quoted text is never a command, so a PR title mentioning
# `gh pr create` or `OMH_GATE=off` cannot trigger or bypass the gate.
#
# An unlisted wrapper (`nice`, `xargs`, a shell function) still escapes, and so does
# a command substitution inside double quotes. That is the script's declared
# fail-open stance, not a claim of completeness.

GATE_TRIGGERED=no
GATE_BYPASS=no
SEG_COUNT=0
SEG_TOKENS=()
PR_ARGC=0
PR_ARGV=()

is_gh_word() {
  case "$1" in
    gh | */gh) return 0 ;;
  esac
  return 1
}

is_wrapper_word() {
  case "$1" in
    command | env | exec | sudo | doas | nohup | nice | stdbuf | time | builtin) return 0 ;;
  esac
  return 1
}

# Decide whether the segment currently in SEG_TOKENS is a `gh pr create` invocation.
# Records the arguments that follow so the selected PR origin can be read from the
# same parse, and honours `OMH_GATE=off` only as a real assignment prefix.
inspect_segment() {
  index=0
  bypass=no
  while [ "$index" -lt "$SEG_COUNT" ]; do
    word=${SEG_TOKENS[$index]}
    case "$word" in
      OMH_GATE=off) bypass=yes ;;
      [A-Za-z_]*=*) ;;
      *) is_wrapper_word "$word" || break ;;
    esac
    index=$((index + 1))
  done

  [ "$GATE_TRIGGERED" = yes ] && return
  [ $((index + 2)) -lt "$SEG_COUNT" ] || return
  is_gh_word "${SEG_TOKENS[$index]}" || return
  [ "${SEG_TOKENS[$((index + 1))]}" = pr ] || return
  [ "${SEG_TOKENS[$((index + 2))]}" = create ] || return

  GATE_TRIGGERED=yes
  [ "$bypass" = yes ] && GATE_BYPASS=yes
  index=$((index + 3))
  PR_ARGC=0
  PR_ARGV=()
  while [ "$index" -lt "$SEG_COUNT" ]; do
    PR_ARGV[$PR_ARGC]=${SEG_TOKENS[$index]}
    PR_ARGC=$((PR_ARGC + 1))
    index=$((index + 1))
  done
}

end_token() {
  if [ -n "$token" ] || [ "$token_open" -eq 1 ]; then
    SEG_TOKENS[$SEG_COUNT]="$token"
    SEG_COUNT=$((SEG_COUNT + 1))
    token=""
    token_open=0
  fi
}

end_segment() {
  [ "$SEG_COUNT" -gt 0 ] && inspect_segment
  SEG_COUNT=0
  SEG_TOKENS=()
}

scan_command() {
  command_line="$1"
  length=${#command_line}
  position=0
  token=""
  token_open=0
  SEG_COUNT=0
  SEG_TOKENS=()
  while [ "$position" -lt "$length" ]; do
    char=${command_line:position:1}
    case "$char" in
      "'")
        position=$((position + 1))
        while [ "$position" -lt "$length" ] && [ "${command_line:position:1}" != "'" ]; do
          token="$token${command_line:position:1}"
          position=$((position + 1))
        done
        token_open=1
        ;;
      '"')
        position=$((position + 1))
        while [ "$position" -lt "$length" ] && [ "${command_line:position:1}" != '"' ]; do
          [ "${command_line:position:1}" = '\' ] && position=$((position + 1))
          token="$token${command_line:position:1}"
          position=$((position + 1))
        done
        token_open=1
        ;;
      '\')
        position=$((position + 1))
        token="$token${command_line:position:1}"
        token_open=1
        ;;
      ' ' | $'\t')
        end_token
        ;;
      '<')
        end_token
        # `<<` opens a heredoc: everything after it is data, never a command.
        if [ "${command_line:$((position + 1)):1}" = '<' ]; then
          end_segment
          return
        fi
        ;;
      '>')
        end_token
        ;;
      ';' | '&' | '|' | '(' | ')' | '{' | '}' | '`' | $'\n')
        end_token
        end_segment
        ;;
      *)
        token="$token$char"
        token_open=1
        ;;
    esac
    position=$((position + 1))
  done
  end_token
  end_segment
}

IS_MCP=no
if [ "$TOOL_NAME" = "$MCP_PR_TOOL" ]; then
  IS_MCP=yes
else
  scan_command "$TOOL_CMD"
  [ "$GATE_TRIGGERED" = yes ] || defer
fi

# Escape hatch. The prefix form (`OMH_GATE=off gh pr create …`) sets the variable on
# the *creating* process, which this hook never inherits — so it is read off the
# command string too, not just our own environment. It counts only as a real
# assignment prefix of the triggering segment: a PR title or body that merely
# mentions OMH_GATE=off is a quoted argument and must not grant the bypass.
#
# The MCP tool call carries no command string, so there is no prefix form for it:
# bypass that path only through OMH_GATE=off in the environment this hook itself runs
# in, not by putting it in PR fields.
#
# That environment is not the user's alone. Under Claude Code, `env` in settings
# applies to a session and its subprocesses, `.claude/settings.local.json` is a valid
# scope, and a running session picks up changed values when the file is saved — so an
# agent that can `Write` that file can bypass the MCP path for the current session.
# This is documented rather than closed: the Bash path already accepts an agent-typed
# `OMH_GATE=off` prefix, so the bypass was never a user-only control, and every
# bypass says in its reason that the pull request was NOT verified. Treat the gate as
# an executable reminder with an audited escape, not as an access control.
if [ "${OMH_GATE:-}" = "off" ] || [ "$GATE_BYPASS" = yes ]; then
  decide allow "Quality gate ignorado via OMH_GATE=off. Este pull request NÃO foi verificado."
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

# Mid-merge or mid-rebase: opening a PR mid-conflict-resolution is not a normal flow,
# and gating it only blocks the resolution itself.
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null) || defer
if [ -e "$GIT_DIR/MERGE_HEAD" ] || [ -d "$GIT_DIR/rebase-merge" ] || [ -d "$GIT_DIR/rebase-apply" ]; then
  defer
fi

# ---------------------------------------------------------------- selected PR origin

# Read -H/--head out of the arguments `scan_command` already tokenized. Supports
# `--head=X`, `--head X` and `-H X`; the last occurrence wins, as an argument parser
# resolves a repeated flag. The values of the flags that carry free text are skipped,
# so a `--head` mentioned inside a title or body is never read as the flag: scanning
# the raw line with a regex extracted `support'` — dangling quote included — from
# `gh pr create --title 'add --head support' --fill`, and refused to open a pull
# request whose title merely mentioned the flag.
parse_head_argument() {
  index=0
  head_value=""
  while [ "$index" -lt "$PR_ARGC" ]; do
    argument=${PR_ARGV[$index]}
    case "$argument" in
      --head=*)
        head_value=${argument#--head=}
        ;;
      --head | -H)
        index=$((index + 1))
        [ "$index" -lt "$PR_ARGC" ] && head_value=${PR_ARGV[$index]}
        ;;
      --title | -t | --body | -b | --body-file | -F | --base | -B | --label | -l | \
        --assignee | -a | --reviewer | -r | --milestone | -m | --project | -p | --template | -T)
        index=$((index + 1))
        ;;
    esac
    index=$((index + 1))
  done
  printf '%s' "$head_value"
}

# Best-effort owner/repo from a remote URL. Only the two forms git/GitHub actually
# produce (`git@host:owner/repo(.git)` and `https://host/owner/repo(.git)`); anything
# else prints nothing, which the caller treats as "cannot verify" and skips the check.
normalize_owner_repo() {
  url="$1"
  url=${url%.git}
  case "$url" in
    git@*:*)
      printf '%s' "${url#*:}"
      ;;
    https://*|http://*)
      rest=${url#*://}
      printf '%s' "${rest#*/}"
      ;;
  esac
}

if [ "$IS_MCP" = yes ]; then
  HEAD_ARG="$MCP_HEAD"
else
  HEAD_ARG=$(parse_head_argument)
fi

CURRENT_BRANCH=$(git symbolic-ref --quiet --short HEAD 2>/dev/null)

if [ -n "$HEAD_ARG" ]; then
  case "$HEAD_ARG" in
    *:*)
      decide deny "O head do pull request ($HEAD_ARG) indica outro fork. O gate valida apenas o checkout atual; verifique $HEAD_ARG manualmente e tente novamente."
      ;;
  esac
  if [ "$HEAD_ARG" != "$CURRENT_BRANCH" ]; then
    decide deny "O head do pull request ($HEAD_ARG) difere do branch atualmente em checkout (${CURRENT_BRANCH:-HEAD detached}). Faça checkout de $HEAD_ARG ou verifique-o manualmente e tente novamente."
  fi
fi

if [ "$IS_MCP" = yes ] && [ -n "$MCP_OWNER" ] && [ -n "$MCP_REPO" ]; then
  ORIGIN_URL=$(git remote get-url origin 2>/dev/null)
  ORIGIN_OWNER_REPO=$(normalize_owner_repo "$ORIGIN_URL")
  if [ -n "$ORIGIN_OWNER_REPO" ]; then
    TARGET_OWNER_REPO=$(printf '%s/%s' "$MCP_OWNER" "$MCP_REPO" | tr '[:upper:]' '[:lower:]')
    if [ "$TARGET_OWNER_REPO" != "$(printf '%s' "$ORIGIN_OWNER_REPO" | tr '[:upper:]' '[:lower:]')" ]; then
      decide deny "O pull request aponta para $MCP_OWNER/$MCP_REPO, que não corresponde ao remote origin local ($ORIGIN_OWNER_REPO). Abra o PR a partir de um checkout desse repositório ou verifique-o manualmente."
    fi
  fi
  # ORIGIN_URL empty or in an unrecognized form: fail open, this specific check is skipped.
fi

# ---------------------------------------------------------------- what the PR will ship

# The PR ships HEAD, not the working tree. Anything uncommitted is silently absent
# from it, so a dirty tree must stop for a human decision rather than gate content
# that will not actually be reviewed. Modified tracked files and untracked files are
# reported separately: "uncommitted changes" is not a true description of a stray
# `.DS_Store` or an unignored build directory, and an inaccurate reason is what makes
# a gate look broken.
if [ -n "$(git status --porcelain --untracked-files=no 2>/dev/null)" ]; then
  decide deny "Há alterações não commitadas em arquivos rastreados que não entrarão no pull request. Faça commit ou descarte-as e tente novamente."
fi
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | head -5 | tr '\n' ' ')
if [ -n "$UNTRACKED" ]; then
  decide deny "Há arquivos não rastreados que não entrarão no pull request: ${UNTRACKED}. Faça commit deles, adicione-os ao .gitignore ou remova-os e tente novamente."
fi

# The PR is built from the branch on the remote it targets, not from the local HEAD
# and not necessarily from `@{upstream}`: a branch tracking `upstream/feat` while
# `origin` has no `feat` at all used to be allowed, and the pull request was then
# opened against a remote that did not have the branch. Resolve the remote the PR
# actually targets instead — `origin` when it exists, the branch's tracking remote
# otherwise — and compare HEAD against that ref.
PR_BRANCH=${HEAD_ARG:-$CURRENT_BRANCH}
if [ -z "$PR_BRANCH" ]; then
  decide deny "O HEAD está detached, portanto não há um branch a partir do qual abrir o pull request. Faça checkout do branch desejado e tente novamente."
fi

TARGET_REMOTE=origin
git remote get-url origin >/dev/null 2>&1 ||
  TARGET_REMOTE=$(git config --get "branch.$PR_BRANCH.remote" 2>/dev/null)
if [ -z "$TARGET_REMOTE" ]; then
  decide deny "O head local não foi enviado: $PR_BRANCH não tem um remote a partir do qual abrir o pull request. Faça push e tente novamente."
fi

HEAD_SHA=$(git rev-parse HEAD 2>/dev/null)
TARGET_SHA=$(git rev-parse --verify -q "refs/remotes/$TARGET_REMOTE/$PR_BRANCH" 2>/dev/null)
if [ -z "$TARGET_SHA" ]; then
  # A branch can track a remote the pull request will not use. Refusing beats
  # verifying `$TRACKING_REMOTE/$PR_BRANCH`, which would report "verified" about a ref
  # the pull request never reads. Name the situation, because the way out is the
  # bypass and nobody guesses that from "push it".
  TRACKING_REMOTE=$(git config --get "branch.$PR_BRANCH.remote" 2>/dev/null)
  if [ -n "$TRACKING_REMOTE" ] && [ "$TRACKING_REMOTE" != "$TARGET_REMOTE" ] &&
    git rev-parse --verify -q "refs/remotes/$TRACKING_REMOTE/$PR_BRANCH" >/dev/null 2>&1; then
    decide deny "$PR_BRANCH rastreia $TRACKING_REMOTE, mas o pull request seria aberto contra $TARGET_REMOTE, que não contém $PR_BRANCH. O gate recusa em vez de verificar $TRACKING_REMOTE/$PR_BRANCH, pois essa não é a ref usada pelo pull request. Faça push de $PR_BRANCH para $TARGET_REMOTE ou abra o pull request com o bypass de emergência (OMH_GATE=off gh pr create …), que registra que ele NÃO foi verificado."
  fi
  decide deny "O head local não foi enviado: $TARGET_REMOTE não contém $PR_BRANCH, portanto o pull request seria aberto contra um remote que não tem esse branch. Faça push para $TARGET_REMOTE e tente novamente."
fi
if [ -z "$HEAD_SHA" ] || [ "$TARGET_SHA" != "$HEAD_SHA" ]; then
  decide deny "O head local não foi enviado: HEAD difere de $TARGET_REMOTE/$PR_BRANCH. Faça push e tente novamente."
fi

# ---------------------------------------------------------------- remote reality check

# One `git ls-remote` attempt, hard-budgeted to ~10s wall clock. bash 3.2 has no
# built-in timeout and macOS has no guaranteed `timeout(1)`, so the budget is enforced
# by hand: background the command, poll, and `kill -9` past the deadline. The
# credential env vars stop it from ever blocking on a prompt; the output goes to a
# `mktemp` file under $TMPDIR, never inside the repository. Any failure — no hasher,
# no reachable remote, a slow remote, a non-zero exit, an empty ref — leaves the
# selected remote revision unknown, so the caller denies before running checks.
fetch_remote_sha() {
  remote="$1"; ref="$2"
  out=$(mktemp "${TMPDIR:-/tmp}/omh-quality-gate-ls-remote.XXXXXX" 2>/dev/null) || return 1
  (GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=true SSH_ASKPASS=true git ls-remote "$remote" "$ref" >"$out" 2>/dev/null) &
  pid=$!
  waited=0
  while kill -0 "$pid" 2>/dev/null; do
    waited=$((waited + 1))
    if [ "$waited" -gt 10 ]; then
      kill -9 "$pid" 2>/dev/null
      wait "$pid" 2>/dev/null
      rm -f "$out" 2>/dev/null
      return 1
    fi
    sleep 1
  done
  wait "$pid" 2>/dev/null
  rc=$?
  remote_sha=$(awk '{print $1; exit}' "$out" 2>/dev/null)
  rm -f "$out" 2>/dev/null
  [ "$rc" -eq 0 ] && [ -n "$remote_sha" ] || return 1
  printf '%s' "$remote_sha"
}

# Asked of the remote the PR targets and of the branch it will ship, so the live
# answer covers the same ref the local comparison above just accepted.
REMOTE_SHA=$(fetch_remote_sha "$TARGET_REMOTE" "refs/heads/$PR_BRANCH")
if [ -z "$REMOTE_SHA" ]; then
  decide deny "O branch remoto não pôde ser verificado. Restaure o acesso a $TARGET_REMOTE e tente novamente ou use o bypass de emergência explícito."
fi
if [ "$REMOTE_SHA" != "$HEAD_SHA" ]; then
  decide deny "O branch remoto foi alterado desde o último fetch local: $PR_BRANCH em $TARGET_REMOTE agora está em $REMOTE_SHA, enquanto este checkout está em $HEAD_SHA. Faça fetch e tente novamente."
fi

# ---------------------------------------------------------------- run cache

CONFIG=".claude/quality-gate.json"
CACHE_FILE="$CACHE_DIR/$REPO_SIG"

# Keyed on HEAD *and* on the content of the gate configuration. HEAD alone never
# invalidated on a configuration change, which is reachable without a new commit
# whenever `.claude/quality-gate.json` is ignored rather than tracked. It still does
# not invalidate on a toolchain change outside the repository — a discovered `make
# test` that starts failing for an installed-dependency reason is only re-run on the
# next commit. That limit is declared, not silently assumed.
CACHE_KEY="$HEAD_SHA"
[ -f "$CONFIG" ] && CACHE_KEY="$HEAD_SHA:$(sha < "$CONFIG")"

# An empty HEAD_SHA means `git rev-parse HEAD` failed; never let that collapse into a
# key that matches everything.
if [ -n "$HEAD_SHA" ] && [ -f "$CACHE_FILE" ]; then
  if [ "$(cat "$CACHE_FILE" 2>/dev/null)" = "$CACHE_KEY" ]; then
    decide allow "O quality gate já passou para este HEAD e esta configuração exatos."
  fi
fi

# ---------------------------------------------------------------- discovery

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
# otherwise the first PR is blocked by pre-existing debt the project never opted into.
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
      # with no tests un-PR-able — that is the invariant this whole gate rests on.
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
# would otherwise "fail" and block the pull request.
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
    decide deny "O quality gate FALHOU em ${kind}: \`${cmd}\`

$(printf '%s' "$out" | tail -25)

Corrija o problema, faça push da correção e abra o pull request novamente. Bypass de emergência (o PR NÃO é verificado): prefixe o comando com OMH_GATE=off ou exporte a variável antes de um PR disparado por MCP."
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
      decide deny "O quality gate FALHOU em uma verificação do projeto: \`${cmd}\`

$(printf '%s' "$out" | tail -25)"
    fi
    RAN="$RAN extra[$i]"
    i=$((i + 1))
  done
fi

if [ -z "$RAN" ]; then
  decide allow "O quality gate não encontrou comandos de format/lint/typecheck/test neste repositório — não há nada para verificar."
fi

if [ -n "$HEAD_SHA" ]; then
  mkdir -p "$CACHE_DIR" 2>/dev/null
  printf '%s' "$CACHE_KEY" > "$CACHE_FILE" 2>/dev/null
fi

decide allow "O quality gate passou:${RAN}."
