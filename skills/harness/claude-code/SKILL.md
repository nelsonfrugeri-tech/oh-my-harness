---
version: 1.0.1
name: claude-code
description: |
  Runbook de sync/instalação da biblioteca oh-my-harness no ~/.claude global. Cobre symlink
  temado de agents (subpastas de tema, discovery recursivo), achatamento de skills no destino
  (skills não são descobertas em subpastas de categoria — cada SKILL.md precisa virar filho
  direto de ~/.claude/skills/<leaf>/), symlink de workflows, limpeza de órfãos/symlinks
  quebrados do layout antigo, diff interativo de CLAUDE.md e settings.json, e detecção +
  proposta de mapeamento de capabilities/MCP na tabela Ambiente & Tools.
  Use quando: (1) instalar a biblioteca pela primeira vez numa máquina, (2) sincronizar depois
  de um git pull, (3) fazer setup de um MCP novo e remapear capabilities, (4) diagnosticar
  agents/skills órfãos ou symlinks quebrados em ~/.claude.
  Gatilhos: instalar, sincronizar, sync, setup, configurar harness, atualizar biblioteca.
type: capability
---

# Claude Code — Runbook de Sync para o `~/.claude` global

Runbook lido da fonte (`oh-my-harness`) e executado quando o usuário pede para instalar ou
sincronizar a biblioteca. Siga as *Regras de Conduta* abaixo antes de qualquer ação — elas
governam como você se comporta neste repositório, não apenas o procedimento de sync.

## Regras de Conduta (este repositório é uma FONTE, não um projeto de desenvolvimento)

1. **Você não desenvolve este repo.** Não cria, não edita e não faz scaffold de arquivos aqui
   — **exceto** quando o usuário pedir **explicitamente** para alterar a própria biblioteca (um
   agent, uma skill, um workflow). Fora isso, este repo é apenas a **fonte** de leitura de uma
   biblioteca de config de harness.
2. **Config do harness vai SEMPRE para o global `~/.claude/`** — nunca dentro deste repo, nunca
   dentro de projeto nenhum.
3. **Nunca polua um projeto com arquivos que não são do produto** — scripts one-off, `.md` de
   análise, scratch, saídas intermediárias ficam **fora** do working tree (scratchpad da sessão
   ou `/tmp`). Na dúvida, pergunte.
4. **Nunca faça nada que o usuário não pediu explicitamente.** Aja só sob pedido claro; quando
   o usuário está descrevendo o problema, leia e **peça confirmação antes de criar ou editar**.
5. **Nada destrutivo (apagar/sobrescrever) sem confirmação explícita.**

---

## Passo 0 — Origem e destino

- **FONTE** = raiz deste repositório (`agents/`, `skills/`, `claude-code/`).
- **DESTINO** = `${CLAUDE_HOME:-~/.claude}`.

## Passo 1 — Agents → symlink temado (espelha as subpastas)

Agents são descobertos **recursivamente** pelo Claude Code — subpastas funcionam nativamente,
e o nome do agent vem do frontmatter `name:`, não do path. Por isso o symlink apenas **espelha**
o tema da fonte no destino, sem achatar nada:

- `FONTE/agents/<theme>/<name>.md` → `~/.claude/agents/<theme>/<name>.md`

Exemplo: `agents/engineers/developer.md` → `~/.claude/agents/engineers/developer.md`,
`agents/tools/context.md` → `~/.claude/agents/tools/context.md`.

Como os nomes-folha (`name:` no frontmatter) já são únicos em toda a árvore, não há colisão
possível mesmo com múltiplos temas.

## Passo 2 — Skills → symlink ACHATADO (motivo técnico obrigatório)

**Skills NÃO são descobertas em subpastas de categoria no alvo `~/.claude/skills/`.** Cada
skill precisa ser filho **DIRETO** do destino: `~/.claude/skills/<leaf>/SKILL.md`, e o nome
resolvido é o nome do diretório-folha. Isso é diferente de agents (que são recursivos).

Portanto: a **FONTE** pode ficar temada (`skills/engineers/python/`, `skills/harness/claude-code/`,
`skills/tools/explorer/`), mas o passo de instalação precisa **ACHATAR** o diretório-folha para
o destino:

- Para cada `SKILL.md` encontrado sob `FONTE/skills/**`, crie o symlink do diretório-folha
  (não do arquivo) direto em `~/.claude/skills/<leaf>/`:
  - `FONTE/skills/engineers/python/` → `~/.claude/skills/python/`
  - `FONTE/skills/harness/claude-code/` → `~/.claude/skills/claude-code/`
  - `FONTE/skills/tools/explorer/` → `~/.claude/skills/explorer/`
  - `FONTE/skills/tools/kb-infra/` → `~/.claude/skills/kb-infra/` (idem `kb-write`, `kb-retrieval`, `kb-session`)

O symlink é sempre do **diretório-folha inteiro** — assim `references/` e arquivos de
suporte da skill (ex.: o `docker-compose.yml` de `kb-infra`) viajam junto.

Os nomes-folha já são únicos na fonte, então o achatamento nunca colide. Se um dia colidirem,
pare e pergunte ao usuário como resolver — nunca sobrescreva silenciosamente.

## Passo 3 — Workflows, hooks e doutrina → symlink direto

- `FONTE/claude-code/workflows/*.ts` → `~/.claude/workflows/<nome>.ts`
- `FONTE/claude-code/hooks/*.sh` → `~/.claude/hooks/<nome>.sh`
- `FONTE/doctrine` → `~/.claude/doctrine` (symlink do **diretório**)

O symlink de `doctrine/` é o que faz o import `@doctrine/epistemics.md` do `CLAUDE.md`
instalado resolver. Sem ele, a doutrina epistêmica simplesmente não carrega — e não há aviso
documentado de import quebrado; na prática ele falha em silêncio. Por isso a verificação é
obrigatória: depois do sync, confirme com `/context` que o arquivo aparece sob **Memory files**.

Depois de linkar um hook, garanta o bit de execução na **fonte** (`chmod +x`) — o symlink
não carrega permissão própria, e um hook sem `+x` falha silenciosamente como "non-blocking
error", deixando a proteção desligada sem avisar ninguém.

O `quality-gate.sh` só age em repositório **explicitamente confiado** (ver `CLAUDE.md`).
Ao sincronizar, ofereça criar o marcador de confiança para **este** repositório — e só para
ele. Nunca confie um repositório em massa: o marcador é o que separa "roda os checks do meu
projeto" de "executa comandos de qualquer repo que eu clonar".

## Passo 4 — Órfãos / symlinks quebrados

Detecte e limpe:

1. **Symlinks quebrados** (apontam para um path que não existe mais na fonte, geralmente
   restos do layout flat antigo — ex.: `~/.claude/agents/context.md` quando a fonte agora é
   `agents/tools/context.md`, ou `~/.claude/skills/drink-context/` removida na fonte).
2. **Agents/skills que existem no destino e não têm mais correspondente na fonte** (renomeados
   ou removidos).

Para cada item órfão/quebrado encontrado, **pergunte ao usuário** manter ou apagar — nunca
apague silenciosamente. Liste o path completo em cada pergunta.

## Passo 5 — Configs editáveis → diff interativo

Para `CLAUDE.md` e `settings.json` (que o usuário edita por máquina), compare fonte × destino
e resolva conforme o estado:

- **ausente no destino** → copie.
- **idêntico** → siga em frente.
- **diferente** → mostre o diff (formato abaixo) e deixe o usuário escolher **merge**,
  **sobrescrever** ou **manter**. Ofereça o merge como padrão — ele preserva a tabela local de
  capabilities (`## Ambiente & Tools`) do usuário enquanto traz o que há de novo na fonte.

## Passo 6 — Capabilities / MCP → detectar e propor

Preencha a tabela `## Ambiente & Tools` do `CLAUDE.md` com os MCPs configurados na máquina:

1. Liste os MCP servers lendo `~/.claude.json`, `~/.claude/settings.json` (`mcpServers`),
   `.mcp.json` do escopo, ou rodando `claude mcp list`.
2. Proponha o mapeamento: git hosting (`github`/`gitlab`) → `code-host`; CI → `ci`;
   notas/memória → `memory`; capability sem MCP → `nenhuma`.
3. Mostre a proposta como diff e aplique após o usuário confirmar.
4. Use apenas o nome/prefixo do server (`mcp__github__*`) — nunca uma tool individual.

## Passo 7 — Hook de SessionStart

Confirme que `claude-code/settings.json` aponta `SessionStart` para
`~/.claude/hooks/context-load.sh`. Esse adapter resolve o loader compartilhado em
`hooks/context-load.sh`, que deriva o projeto pelo Git root, injeta o snapshot existente e calcula
o drift desde `last_hash`. Quando o report estiver ausente ou desatualizado, a saída instrui o loop
principal a invocar o agent `context` em modo FULL ou DELTA. O hook nunca escreve `context.md` e
continua fail-open; a análise model-backed pertence ao agent, não ao processo de lifecycle.

---

## Template de apresentação

Mostre a lista primeiro, depois o detalhe por arquivo.

```
## Sync: <FONTE> → ~/.claude

Agents (symlink temado):      novo: N   |   já ok: M
Skills (symlink achatado):    novo: N   |   já ok: M
Workflows:                    novo: N   |   já ok: M
Configs:  [conflito] CLAUDE.md   [ok] settings.json
Capabilities/MCP:  code-host (vazio) → mcp__github__*   |   memory (vazio) → nenhuma
Órfãos:  ~/.claude/skills/drink-context/ (fonte removida) → manter ou apagar?
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

---

## Ao final

Reporte: quantos agents/skills/workflows linkados (novos vs já corretos), configs resolvidos,
capabilities mapeadas, órfãos tratados, e o que ficou pendente. Lembre o usuário de que o
conteúdo da lib se auto-atualiza via `git pull` na fonte (symlinks) — só configs editáveis
(`CLAUDE.md`, `settings.json`) exigem re-sync manual quando a fonte mudar.
