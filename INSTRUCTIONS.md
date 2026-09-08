# INSTRUCTIONS.md — bootstrap for the harness opening this repository

> For the AI agent (Claude Code or another harness) opening this repository for the first time,
> before the library is installed locally. Read this **before** taking any action.

This repository is a harness configuration **SOURCE**, not a development project. On a new
machine, the `claude-code` agent and skill are not yet installed in the local `~/.claude`, so this
file exists only as a readable bootstrap entrypoint.

**Your task when the user requests installation or synchronization:** select the adapter for the
active harness. For Claude Code, run the `claude-code` agent or follow
`harness/claude/skills/claude-code/SKILL.md`. For Codex shared skills, its Codex-only installation skill,
and hooks, install the repository marketplace and its `oh-my-harness` plugin, then review and trust
its hook definitions through `/hooks`. Run `python3 installers/codex/install.py` and validate with
`python3 installers/codex/install.py --check` only when custom agents, global guidance, or local integrations
are also required; the full adapter runbook lives in `harness/codex/skills/codex/SKILL.md`.

Never translate one harness adapter into another during machine setup. The versioned adapter is the
source of truth for its global files, agents, hooks, workflows, and MCP integration behavior.
