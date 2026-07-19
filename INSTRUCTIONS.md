# INSTRUCTIONS.md — bootstrap para o harness que abrir este repositório

> Para o agente de IA (Claude Code ou outro harness) que abrir este repositório pela primeira
> vez, antes de a biblioteca estar instalada localmente. Leia isto **antes** de qualquer ação.

Este repositório é uma **FONTE** de config de harness — não um projeto de desenvolvimento.
Numa máquina nova, o agent `claude-code` e a skill `claude-code` ainda não estão instalados no
`~/.claude` local, então este arquivo existe só como entrypoint legível para o bootstrap.

**Sua tarefa quando o usuário pedir para instalar ou sincronizar:** rode o agent `claude-code`
(veja `agents/harness/claude-code.md`), ou, se preferir seguir o runbook diretamente, leia
`skills/harness/claude-code/SKILL.md` — ele contém o procedimento completo (symlink temado de
agents, achatamento de skills, workflows, diff de configs, mapeamento de capabilities/MCP e
tratamento de órfãos).
