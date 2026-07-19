# SETUP — sync da biblioteca para o `~/.claude` global

Runbook lido da fonte (este repo) e executado quando o usuário pede para instalar ou
sincronizar. Siga as regras de conduta em [`../INSTRUCTIONS.md`](../INSTRUCTIONS.md).

## Passo 0 — Origem e destino

- **FONTE** = raiz deste repositório (`agents/`, `skills/`, `claude-code/`).
- **DESTINO** = `${CLAUDE_HOME:-~/.claude}`.

## Passo 1 — Conteúdo da lib → symlink

Crie um symlink de cada item para o destino (assim `git pull` na fonte passa a atualizar
tudo automaticamente):

- `FONTE/agents/*.md` → `~/.claude/agents/<nome>.md`
- `FONTE/skills/<nome>/` → `~/.claude/skills/<nome>`
- `FONTE/claude-code/workflows/*.ts` → `~/.claude/workflows/<nome>.ts`

Reporte o que foi linkado e o que já estava correto.

## Passo 2 — Configs editáveis → diff interativo

Para `CLAUDE.md` e `settings.json` (que o usuário edita por máquina), compare fonte × destino
e resolva conforme o estado:

- **ausente no destino** → copie.
- **idêntico** → siga em frente.
- **diferente** → mostre o diff (formato abaixo) e deixe o usuário escolher **merge**,
  **sobrescrever** ou **manter**. Ofereça o merge como padrão (mantém as edições dele +
  traz o novo da fonte).

## Passo 3 — Capabilities / MCP → detectar e propor

Preencha a tabela `## Ambiente & Tools` do CLAUDE.md com os MCPs configurados na máquina:

1. Liste os MCP servers lendo `~/.claude.json`, `~/.claude/settings.json` (`mcpServers`),
   `.mcp.json` do escopo, ou rodando `claude mcp list`.
2. Proponha o mapeamento: git hosting (`github`/`gitlab`) → `code-host`; CI → `ci`;
   notas/memória → `memory`; capability sem MCP → `nenhuma`.
3. Mostre a proposta como diff e aplique após o usuário confirmar.
4. Use apenas o nome/prefixo do server (`mcp__github__*`).

## Passo 4 — Órfãos

Liste agents/skills/workflows que existem no `~/.claude/` e não na fonte. Para cada um,
pergunte ao usuário **manter** ou **apagar**, e aja conforme a resposta.

## Template de apresentação

Mostre a lista primeiro, depois o detalhe por arquivo.

```
## Sync: <FONTE> → ~/.claude

Conteúdo da lib (symlink):   novo: N   |   já ok: M
Configs:  [conflito] CLAUDE.md   [ok] settings.json
Capabilities/MCP:  code-host (vazio) → mcp__github__*   |   memory (vazio) → nenhuma
Órfãos:  skills/old-skill/ → manter ou apagar?
```

Detalhe de conflito — **atual** em cima, **novo** embaixo:

```
── ~/.claude/CLAUDE.md ──────────────────
ATUAL (sua máquina):
  <trecho>
NOVO (fonte):
  <trecho>
Ação? [merge / sobrescrever / manter]
```

## Ao final

Reporte: quantos linkados, configs resolvidos, capabilities mapeadas e o que ficou pendente.
Lembre o usuário de que o conteúdo da lib se auto-atualiza via `git pull` na fonte (symlinks).
