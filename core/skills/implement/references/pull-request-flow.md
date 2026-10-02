# Pull Request Flow

How a change reaches a pull request. Agents that write code load this through `implement`; the
session modes add their own draft and ready rules in `developer` and `reviewer`.

## Gate before opening

- Commit and push freely when the user asks; no gate applies to them.
- Open a pull request only with passing tests and an independent review with no blocker.
- The review is independent: a subagent that applies the `review` skill to the diff that goes to
  the pull request. The quality-gate hook does not replace it, because the hook runs checks and
  does not judge correctness, architecture, or coverage.
- In the session modes, the developer opens the pull request as a draft with passing tests, and
  the reviewer mode moves it to ready after a review with no blocker and no pending plan revision.

## What the quality-gate hook enforces

- A `PreToolUse` hook, shipped by the plugin, runs on `gh pr create` and on the `code-host` MCP
  tool that creates pull requests. It discovers and runs format, lint, typecheck, and tests on the
  `HEAD` that goes to the pull request, and blocks the creation when any of them fails.
- Before any check, it denies a dirty working tree, a local `HEAD` not pushed to the remote, a head
  from another branch or fork, an `owner/repo` that does not match the `origin` remote, and a
  remote that diverged or cannot be verified: the pull request carries what is on the remote.
- It denies instead of asking because `ask` is not portable: Codex documents
  `permissionDecision: "ask"` as parsed but not supported and continues the tool call, while
  Claude Code asks the user. `deny` is the only value that blocks in both harnesses.
- A branch that tracks another remote, such as `upstream`, while `origin` lacks the branch is
  denied rather than validated against the tracking ref; the reason names both remotes. Push the
  branch to `origin`, or use the emergency escape.
- It acts only in a repository explicitly trusted with the on-disk marker; without the marker it
  defers and runs nothing.

## What the guarantee covers

The gate proves the `HEAD` at the moment the pull request opens, and nothing more. Later pushes,
`gh pr ready`, pull-request updates through the `code-host` MCP, and `gh api -X POST` on pull
requests do not pass through it, by design: the hook governs creation, and human review and CI
govern what follows.

## Emergency escape

Prefix `OMH_GATE=off` to the command (`OMH_GATE=off gh pr create …`), or export `OMH_GATE=off` in
the hook environment for the MCP path. The gate allows the creation and states that the pull
request was not verified. The escape is an audited reminder, not access control.

Mechanics, repository trust, and limits live in the header of `core/hooks/quality-gate.sh`.
