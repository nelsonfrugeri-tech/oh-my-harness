# INSTRUCTIONS.md — como o harness deve atuar neste repositório

> Para o agente de IA (Claude Code ou outro harness) que abrir este repositório.
> Leia isto **antes** de qualquer ação. Não resuma — obedeça.

## Este repositório é uma FONTE, não um projeto de desenvolvimento

Você **não** desenvolve este repo. Não cria, não edita e não scaffolda arquivos aqui —
**exceto** quando o usuário pedir **explicitamente** para alterar a própria biblioteca
(um agent, uma skill, um workflow). Fora isso, este repo é apenas a **fonte** de leitura de
uma biblioteca de config de harness.

## Sua tarefa quando o usuário pedir para instalar / sincronizar

Abra e execute **`claude-code/SETUP.md`**. Ele é o procedimento passo a passo:

- **agents / skills / workflows** → symlink em `~/.claude/` (auto-atualizam via `git pull`)
- **CLAUDE.md / settings.json** → diff interativo + merge (config editável por máquina)
- **capabilities / MCP** → detecta os MCPs configurados e propõe o mapeamento
- **órfãos** → lista o que existe no `~/.claude` e não na fonte, pergunta manter/apagar

## Regras invioláveis

1. **Config do harness vai SEMPRE para o global `~/.claude/`** — nunca dentro deste repo, nunca dentro de projeto nenhum.
2. **Nunca polua um projeto com arquivos que não são do produto** — scripts one-off, `.md` de análise, scratch, saídas intermediárias ficam **fora** do working tree (scratchpad da sessão ou `/tmp`). Na dúvida, pergunte.
3. **Nunca faça nada que o usuário não pediu explicitamente.** Aja só sob pedido claro; quando o usuário está escrevendo, leia e **peça confirmação antes de criar ou editar**.
4. **Nada destrutivo (apagar / sobrescrever) sem confirmação explícita.**
