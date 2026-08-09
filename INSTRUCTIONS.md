# INSTRUCTIONS.md — bootstrap para o harness que abrir este repositório

> Para o agente de IA (Claude Code ou outro harness) que abrir este repositório pela primeira
> vez, antes de a biblioteca estar instalada localmente. Leia isto **antes** de qualquer ação.

Este repositório é uma **FONTE** de config de harness — não um projeto de desenvolvimento.
Numa máquina nova, o agent `claude-code` e a skill `claude-code` ainda não estão instalados no
`~/.claude` local, então este arquivo existe só como entrypoint legível para o bootstrap.

**Your task when the user requests installation or synchronization:** select the adapter for the
active harness. For Claude Code, run the `claude-code` agent or follow
`skills/harness/claude-code/SKILL.md`. For Codex, run `python3 codex/install.py` and validate with
`python3 codex/install.py --check`; the full runbook lives in `codex/skills/codex/SKILL.md`.

Never translate one harness adapter into another during machine setup. The versioned adapter is the
source of truth for its global files, agents, hooks, workflows, and MCP integration behavior.
