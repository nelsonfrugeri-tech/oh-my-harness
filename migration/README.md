# Migração: caminho para separar oh-my-harness e keep-lore

> Status: **planejado** · Atualizado em: 2026-06-22
>
> Documento de contexto da transição arquitetural. Vive no repo (decisão
> explícita) para viajar junto com o código durante a migração. Os planos
> detalhados (ADRs) ficam na knowledge base do projeto — ver [Referências](#referências).

## Decisão atual

Por enquanto **mantemos tudo em um único projeto** (`oh-my-harness`), com os
nomes atuais. É mais simples agora. A separação em dois projetos acontece **no
futuro**, depois que o marco abaixo estiver validado.

## Visão de destino (o que queremos virar)

Dois projetos, com responsabilidades separadas:

| Projeto | Plano | Papel |
|---|---|---|
| **oh-my-harness** (CLI `omh`) | control plane | ferramenta de terminal focada em código, para claude-code / codex / cursor: harness config, asset mgmt (skills/agents/workflows), injeção no `CLAUDE.md`, hooks, e **registro do MCP da KB nos clientes** |
| **keep-lore** (futuro) | data plane | a knowledge base como **servidor MCP** (stdio local **+ Streamable HTTP remoto**), portável para qualquer framework de agente em produção (deep-agents, LangGraph, custom) — não só claude-code |

Princípio: os dois acoplam **por MCP / processo, nunca por import** (o `omh`
não importa a KB; só sabe registrar/lançar o MCP dela).

## Marco imediato (o que destrava o split)

**Expor o MCP da KB por Streamable HTTP (chamada de API)** para uso no
**claude-desktop** (e mobile depois), mantendo o **stdio** para o claude-code
local. Mesmo backend (Qdrant + bundle em disco), dois transportes.

Sequência:

1. Adicionar o transporte **Streamable HTTP** ao servidor MCP da KB
   (`o-kb-mcp`), reaproveitando `build_context`/`build_server` — o stdio
   continua intacto. Provavelmente um comando de lifecycle (`omh serve` /
   daemon) para o processo de longa duração.
2. **Validar com o claude-desktop** consumindo a KB via API (atenção: cliente
   remoto exige HTTPS público + OAuth 2.1; localhost/LAN não é alcançável pela
   nuvem da Anthropic — ver spike de suporte a clientes na KB).
3. **Só então** migrar/quebrar os projetos (extrair a KB para `keep-lore`).

## Boundary (o que migra para keep-lore quando separarmos)

O corte passa **por dentro** de `oh_my_harness/kb/`. Resumo (detalhe no ADR):

- **→ keep-lore (data plane):** `kb/core`, `kb/storage`, `kb/embedding`,
  `kb/services`, `kb/mcp`, `kb/infra/docker_qdrant.py`; os comandos de KB
  (`reindex`, `kb create/use`, `start`/`stop` do Qdrant); o stack pesado
  (FlagEmbedding/torch, qdrant-client, docker, python-frontmatter).
- **fica no oh-my-harness (control plane):** `kb/agents/` (bootstrap, harness,
  hooks, injector, templates), `kb/cli` de install/harness/assets, `kb/i18n.py`,
  e o `o-agents-mcp` (preferences / `develop_leap_update`).
- **Única dependência reversa hoje** (control → data): `kb/agents/template.py`
  importa os objetos `KB_*_TOOL` de `kb/mcp/tools` só para ler `name`/
  `description` ao montar o bloco do `CLAUDE.md`. Cortar essa linha (virar um
  catálogo estático de 5 entradas) é o que torna o split limpo — depois disso o
  `omh` não importa mais nada da KB.

## Gatilho do split

Quando o MCP da KB por Streamable HTTP estiver **validado e funcionando no
claude-desktop**. Aí executamos a extração para `keep-lore` (fases A→B→C do ADR).

## Referências (na knowledge base do projeto)

- `adr-okf-adoption.md` — formato de bundle em disco da KB (já na `master`).
- `spec-note-to-okf-mapping.md` — mapeamento campo-a-campo do note.
- `adr-keep-lore-extraction.md` — inventário módulo-a-módulo + plano de extração
  em 3 fases para o `keep-lore`.
- `spike-cursor-support-investigation.md` — investigação de suporte a clientes
  (Cursor / desktop / mobile, auth de MCP remoto).
