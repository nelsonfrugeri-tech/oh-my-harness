---
version: 2.1.0
name: claude-code
description: |
  Runbook de instalação da biblioteca oh-my-harness no Claude Code **como plugin nativo**.
  Cobre: o manifesto `.claude-plugin/plugin.json` (as skills em `skills/` são descobertas por
  padrão; só `./claude-code/skills/` precisa ser declarado), os hooks do plugin em `hooks/hooks.json`
  com `${CLAUDE_PLUGIN_ROOT}`, o marketplace para distribuição versionada por git (version,
  ref, sha), as duas superfícies que o plugin **não** cobre (`CLAUDE.md` e `permissions` do
  `settings.json`), e a migração a partir do layout antigo de symlinks — inclusive a remoção
  dos hooks duplicados que dispariam duas vezes. Cobre também a instalação dos plugins oficiais
  do LangChain (`langchain-skills` e `langchain-mcp`, do marketplace `langchain-ai/langchain-plugins`),
  que são o que os agents `ai-engineer`, `architect` e `developer` roteiam.
  Use quando: (1) instalar a biblioteca numa máquina, (2) atualizar depois de um push,
  (3) migrar do sync por symlink para o plugin, (4) diagnosticar skill/agent/hook que não
  carrega, (5) instalar ou diagnosticar os plugins do LangChain.
  Gatilhos: instalar, sincronizar, sync, setup, configurar harness, atualizar biblioteca, plugin,
  langchain, langgraph, deep agents.
type: capability
---

# Claude Code — Instalação como Plugin Nativo

A biblioteca é um **plugin do Claude Code**. Instalação, atualização, versionamento e
namespacing são do próprio harness; não há mais runbook de symlink a executar à mão.

## Regras de Conduta (este repositório é uma FONTE, não um projeto de desenvolvimento)

1. **Você não desenvolve este repo.** Não cria, não edita e não faz scaffold de arquivos aqui
   — **exceto** quando o usuário pedir **explicitamente** para alterar a própria biblioteca.
2. **Config do harness vai para o global** — nunca dentro deste repo, nunca dentro de projeto
   nenhum.
3. **Nunca polua um projeto com arquivos que não são do produto** — script one-off, `.md` de
   análise, scratch e saída intermediária ficam em `/tmp` ou no scratchpad da sessão.
4. **Nunca faça nada que o usuário não pediu explicitamente.**
5. **Nada destrutivo sem confirmação explícita.**

---

## Passo 1 — Instalar

Três caminhos, do mais permanente ao mais efêmero:

```bash
# distribuição por git (o caminho normal)
claude plugin marketplace add nelsonfrugeri-tech/oh-my-harness
claude plugin install oh-my-harness@oh-my-harness

# a partir de um clone local
claude plugin marketplace add /caminho/para/oh-my-harness
claude plugin install oh-my-harness@oh-my-harness

# desenvolvimento: carrega o repo direto, sem instalar
claude --plugin-dir /caminho/para/oh-my-harness
```

Confirme o estado:

```bash
claude plugin list                      # Status deve ser "✔ enabled"
claude plugin details oh-my-harness@oh-my-harness
```

O `details` imprime o inventário e o **custo de contexto projetado**. Duas leituras do output
que evitam susto:

- **`Agents (0)` é subcontagem, não ausência.** O inventário só conta agents na raiz de
  `agents/`; os nossos vivem em subpastas temadas e **carregam normalmente**, com nome escopado
  `oh-my-harness:<tema>:<nome>`. Verificado por execução, não por leitura do contador.
- **`Hooks` não custa contexto** — roda no harness, fora da janela do modelo.

## Passo 2 — O que o plugin NÃO cobre

Um plugin não fornece instruções globais nem preferências do usuário. Estas duas superfícies
continuam sendo instalação manual, e é isso que o `claude-code/` da fonte ainda serve:

| Superfície | Por quê | O que fazer |
| --- | --- | --- |
| `~/.claude/CLAUDE.md` | Plugin não pode fornecer instrução global — só skills, agents e hooks | Faça **merge** de `claude-code/CLAUDE.md`, preservando a tabela de capabilities da máquina e qualquer bloco local |
| `~/.claude/settings.json` → `permissions` | O `settings.json` de plugin só aceita `agent` e `subagentStatusLine` | Faça merge de `claude-code/settings.json`, preservando `model`, `theme`, `autoMode` e permissões do usuário |

**Os hooks NÃO entram mais no `settings.json`.** Eles são do plugin. Ver Passo 3.

## Passo 3 — Migração a partir do layout antigo

Numa máquina que já usou o sync por symlink, o conteúdo antigo **coexiste** com o plugin e
duplica. Diagnostique antes de remover:

```bash
find ~/.claude/agents ~/.claude/skills ~/.claude/hooks -maxdepth 2 -type l -exec ls -l {} \; 2>/dev/null
```

1. **Hooks duplicados são o sintoma mais visível.** Se `~/.claude/settings.json` ainda tem os
   handlers `SessionStart → context-load.sh` ou `PreToolUse → quality-gate.sh`, eles disparam
   **junto** com os do plugin — o snapshot de contexto aparece duas vezes e o quality gate roda
   duas vezes. Remova **apenas** esses dois handlers; preserve handlers de terceiros no mesmo
   evento (o Deja instala `SessionStart`, `PreCompact` e `UserPromptSubmit`).
2. **Symlinks de agents e skills** que apontam para este repositório viraram redundantes: o
   plugin fornece os mesmos componentes, com namespace. Remova-os, **um a um e com
   confirmação** — nunca em massa. Skills e agents de terceiros (`deja-history`, a cópia
   externa do `graphify`) **não** são órfãos e não podem ser removidos.
3. **`~/.claude/CLAUDE.md` e `permissions` permanecem** — são o Passo 2, não resíduo.

## Passo 4 — Capabilities / MCP

O plugin traz o comportamento; a **tabela de capabilities** é da máquina e vive no
`~/.claude/CLAUDE.md`:

1. Liste os MCP servers com `claude mcp list` (ou lendo `~/.claude.json`).
2. Proponha o mapeamento: git hosting → `code-host`; CI → `ci`; grafo → `code-graph`;
   memória de sessão → `session-memory`; sem provider → deixe **vazia**.
3. Mostre como diff e aplique após confirmação.
4. Use o prefixo do server (`mcp__github__*`), nunca uma tool individual.

## Passo 5 — Plugins oficiais do LangChain

O ecossistema LangChain entra por **marketplace de terceiro**, nunca por vendoring: o conteúdo é
mantido pela LangChain e chega pelo fluxo normal de update de plugin, sem trabalho neste repo.

```bash
claude plugin marketplace add langchain-ai/langchain-plugins
claude plugin install langchain-skills@langchain-plugins
claude plugin install langchain-mcp@langchain-plugins
```

São eles que os agents `ai-engineer`, `architect` e `developer` roteiam — sem os plugins, a seção
*Ecossistema LangChain* desses agents aponta para skills que não existem. Medido com
`claude plugin details` na instalação de referência:

| Plugin | Traz | Custo always-on |
| --- | --- | --- |
| `langchain-skills` | 22 skills de LangChain, LangGraph e Deep Agents | ~2.1k tokens por sessão |
| `langchain-mcp` | 2 MCP servers: `langchain-docs` e `langchain-reference` | ~0 (schema resolvido em runtime) |

Os ~2.1k always-on são o preço de ter as 22 descriptions disponíveis para roteamento; o corpo de
cada skill só carrega quando invocada. Declare esse custo ao usuário em vez de instalar calado.

O mesmo marketplace publica `langsmith-skills` e `langsmith-mcp`, que **não** instalamos por
padrão: exigem conta LangSmith e autorização OAuth. Instale-os do mesmo marketplace se o usuário
tiver conta e pedir.

> Observado nesta instalação: o `marketplace add` clona por **SSH** (`git@github.com:…`). Numa
> máquina sem acesso SSH ao GitHub o passo falha aí — diagnostique o clone antes de suspeitar do
> marketplace.

Verificação: `claude plugin list` mostra os dois como `✔ enabled`, `claude plugin details
langchain-skills@langchain-plugins` lista as skills (22 na instalação de referência — o upstream
pode somar mais), e numa sessão nova `/langchain-skills:ecosystem-primer` responde.

## Passo 6 — Atualizar

```bash
claude plugin marketplace update oh-my-harness
claude plugin update oh-my-harness@oh-my-harness
```

O usuário só recebe uma versão nova quando o `version` do `plugin.json` sobe — é isso que
torna a atualização uma decisão, não um efeito colateral de `git pull`. Para fixar uma versão
exata, o marketplace aceita `ref` (branch/tag) e `sha` (commit); com os dois presentes, o
`sha` vence.

`CLAUDE.md` e `permissions` **não** são atualizados pelo plugin: quando a fonte mudar, refaça
o merge do Passo 2.

## Passo 7 — Verificação

```bash
claude plugin validate <fonte>     # manifesto e marketplace
claude plugin list                 # enabled, sem erro de load
```

Depois abra uma **sessão nova** e confirme por observação, não por suposição:

- uma skill do plugin responde por `/oh-my-harness:<nome>`;
- um agent aparece como `oh-my-harness:<tema>:<nome>`;
- o `SessionStart` injetou snapshot ou pedido FULL/DELTA — **uma vez só**;
- `/context` lista o `CLAUDE.md` sob **Memory files**.

> `claude plugin validate` valida os manifestos, **não** o carregamento. Erro de hook duplicado
> ou de path só aparece no `plugin list` depois de instalar. Rode os dois.

---

## Ao final

Reporte: versão instalada, contagem real de skills e agents (por execução, não pelo contador),
estado dos hooks, o que foi migrado do layout antigo, o que foi preservado por ser de terceiro,
e o que ficou pendente.
