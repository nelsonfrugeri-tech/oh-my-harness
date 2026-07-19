---
name: setup
description: |
  Sincroniza esta biblioteca (agents, skills, workflows, CLAUDE.md, settings.json) com o
  estado global do harness em ~/.claude. É um procedimento de instalação/sync: você lê da
  FONTE (este repositório) e escreve no GLOBAL (~/.claude), nunca dentro de projeto nenhum.
  Use quando o usuário pedir para instalar, sincronizar ou atualizar a config do harness.
  Triggers: /setup, sincronizar config, sync harness, instalar skills e agents, atualizar ~/.claude.
type: command
---

# SETUP — sync da biblioteca para o ~/.claude global

Você (harness) está executando um **procedimento de sincronização**, não desenvolvendo este
repositório. Este repo é a **FONTE**. O destino é sempre o **estado global** `~/.claude/`.

## Regras invioláveis deste procedimento

1. **Nunca trate este repositório como um projeto de desenvolvimento.** Não crie, edite nem
   scaffolde arquivos dentro dele. Você só **lê** daqui.
2. **Nunca escreva config de harness dentro de um projeto.** Todo destino é `~/.claude/`
   (ou `$CLAUDE_HOME`, se definido).
3. **Nada destrutivo sem confirmação explícita** do usuário (apagar, sobrescrever).

## Passo 0 — Resolver origem e destino

- **FONTE** = raiz deste repositório (onde estão `agents/`, `skills/`, `claude-code/`). Se não
  conseguir determinar, pergunte o path ao usuário.
- **DESTINO** = `${CLAUDE_HOME:-~/.claude}`.

## Passo 1 — Conteúdo da lib (agents, skills, workflows) → symlink

Estes você **não** edita localmente: são símbolo, não conteúdo. Aplique symlinks
(idempotente — relinkar não quebra nada):

- `FONTE/agents/*.md` → `~/.claude/agents/<nome>.md`
- `FONTE/skills/<nome>/` → `~/.claude/skills/<nome>`
- `FONTE/claude-code/workflows/*.ts` → `~/.claude/workflows/<nome>.ts`

Não há diff aqui: symlink faz o destino **ser** a fonte, então `git pull` na fonte atualiza tudo.
Só reporte o que foi linkado e o que já estava correto.

## Passo 2 — Configs editáveis (CLAUDE.md, settings.json) → diff interativo

Estes o usuário **edita por máquina** (tabela de capabilities, permissions). Não sobrescreva
cego. Para cada um (`claude-code/CLAUDE.md` → `~/.claude/CLAUDE.md`; `claude-code/settings.json`
→ `~/.claude/settings.json`):

- **Não existe no destino** → crie (copie) e reporte.
- **Existe e é idêntico** → nada a fazer.
- **Existe e difere** → é conflito: mostre o diff (formato abaixo) e deixe o usuário resolver.
  Prefira **merge** (manter as edições dele + trazer o que é novo da fonte) a sobrescrever.

## Passo 3 — Capabilities / MCP → detectar e propor mapeamento

A tabela `## Ambiente & Tools` do CLAUDE.md mapeia capability → tool concreta desta máquina.
Complete-a a partir dos MCPs **realmente configurados** (não invente):

1. Enumere os MCP servers configurados: leia `~/.claude.json`, `~/.claude/settings.json`
   (chave `mcpServers`) e `.mcp.json` do escopo, ou rode `claude mcp list`.
2. Proponha o mapeamento por julgamento semântico:
   - server de git hosting (`github`, `gitlab`…) → `code-host` (ex.: `mcp__github__*`)
   - server de CI → `ci`; server de notas/memória → `memory`
   - se um capability não tem MCP correspondente → proponha `nenhuma`
   - se um MCP não mapeia pra nenhum capability → mencione, não force
3. Apresente como diff (linha atual da tabela em cima, proposta embaixo) e **confirme** antes de escrever.
4. **Nunca** copie tokens/secrets para o CLAUDE.md — só o nome/prefixo do server (`mcp__github__*`).

## Passo 4 — Órfãos (existe no destino, não na fonte)

Liste agents/skills/workflows presentes em `~/.claude/` que **não** existem na fonte. Para cada
um, pergunte: **manter** ou **apagar**. Nunca apague sem confirmação.

## Template de apresentação

Primeiro a **lista** (visão geral), depois o **detalhe por arquivo**.

```
## Sync: <FONTE> → ~/.claude

Conteúdo da lib (symlink):
  novo:        N   |   já ok: M

Configs (precisam de decisão):
  [conflito] ~/.claude/CLAUDE.md
  [ok]       ~/.claude/settings.json (idêntico)

Capabilities/MCP:
  code-host   (vazio)  → proposta: mcp__github__*
  memory      (vazio)  → proposta: nenhuma

Órfãos (existem no ~/.claude, não na fonte):
  skills/old-skill/   → manter ou apagar?
```

Detalhe de cada conflito (**atual** em cima, **novo** embaixo):

```
── ~/.claude/CLAUDE.md ─────────────────────────────
ATUAL (sua máquina):
  <trecho atual>
NOVO (fonte):
  <trecho novo>
Ação? [merge / sobrescrever / manter o atual]
```

## Ao final

Reporte: quantos linkados, quais configs resolvidos e como, o mapeamento de capabilities
aplicado, e o que ficou pendente. Lembre o usuário de que o conteúdo da lib se auto-atualiza
via `git pull` na FONTE (por serem symlinks).
