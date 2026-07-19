<div align="center">

# oh-my-harness

**Biblioteca portátil de agents, skills e workflows para harness de IA.**

Agnóstica de máquina e de harness — o mesmo conjunto roda no Claude Code hoje e é
adaptável a Codex/Cursor, plugando as tools de cada ambiente por um único ponto.

`pt-BR na instrução` · `inglês no código` · `zero acoplamento`

</div>

---

## Por que existe

Config de harness normalmente nasce acoplada: uma tool MCP hardcoded aqui, um caminho
`~/.config/...` ali, uma referência a um serviço específico acolá. Trocou de máquina ou de
harness — quebrou.

Esta biblioteca separa **o que o agente faz** (portátil) de **com qual tool ele faz** (por
máquina), através de uma camada de *capabilities*. O mesmo `developer` abre um Pull Request
via GitHub na sua máquina pessoal e via GitLab na máquina da empresa — sem uma linha de
diferença nos arquivos.

## Conceitos

### 🔌 Capabilities — o plugue de tools

Agents e skills referenciam **capabilities** abstratas, nunca uma tool concreta. Uma única
tabela (em `claude-code/CLAUDE.md`) mapeia cada capability para a tool desta máquina. Trocou
de ambiente? Só a tabela muda.

| Capability  | Papel                                 | Exemplo por máquina        |
| ----------- | ------------------------------------- | -------------------------- |
| `code-host` | Pull/Merge Requests, issues           | `mcp__github__*` / GitLab  |
| `ci`        | Pipelines de CI/CD                    | GitHub Actions / GitLab CI |
| `memory`    | Notas/contexto persistente (opcional) | qualquer memory MCP        |
| `web`       | Busca e fetch                         | `WebSearch`, `WebFetch`    |

### 📚 Progressive disclosure

Cada skill é um `SKILL.md` enxuto (visão geral + quando usar) apontando para `references/`
carregados **sob demanda**. O contexto só paga pelo detalhe que a tarefa realmente precisa.

### 🧱 code-craft

As regras invioláveis de qualidade de código — tipagem total, imutabilidade, funções e
arquivos pequenos, guard clauses no lugar de aninhamento, design pattern no lugar de cadeias
de `if/elif`, quality gate ao final — vivem em `skills/implement/references/code-craft.md`
como **fonte única**, referenciada por `implement` e reusada por `review`.

### 🗣️ Contrato de idioma

Prosa de instrução em **pt-BR**; código, comentários, docstrings e termos técnicos em
**inglês**.

## Estrutura

```
.
├── agents/           roster de subagents (name, description, tools, model)
├── skills/           knowledge base (SKILL.md + references/) com progressive disclosure
├── claude-code/      específico do Claude Code
│   ├── CLAUDE.md     regras duras + a tabela de capabilities
│   ├── SETUP.md      procedimento de sync fonte → ~/.claude
│   ├── settings.json permissions default
│   └── workflows/    orquestração determinística (Workflow API)
├── INSTRUCTIONS.md   como o harness deve atuar neste repositório
└── install.sh        atalho determinístico opcional
```

## Instalação

Este repositório é a **fonte**. Para levá-lo ao seu harness global (`~/.claude`), você **pede
ao harness** — ele lê o [`INSTRUCTIONS.md`](INSTRUCTIONS.md), executa
[`claude-code/SETUP.md`](claude-code/SETUP.md) e resolve o sync (symlink do conteúdo, diff dos
configs, mapeamento de MCP). Sem rodar scripts na mão.

Para um atalho determinístico, há também o `install.sh`:

```bash
./install.sh                        # symlinks agents/ e skills/ em ~/.claude/
CLAUDE_HOME=/caminho ./install.sh   # home customizado
```

## Agents

| Agent         | Papel                                          | Model  |
| ------------- | ---------------------------------------------- | ------ |
| `architect`   | System design, ADRs, C4, trade-offs, API       | opus   |
| `developer`   | Implementação, bug fix, refactor, testes       | sonnet |
| `ai-engineer` | LLM/RAG/embeddings, data pipelines, eval        | sonnet |
| `qa`          | Estratégia de testes, E2E, performance, a11y   | sonnet |
| `sre`         | Observabilidade, SLO/SLI, incidentes, runbooks | sonnet |
| `tech-pm`     | User stories, backlog, roadmap, PRD            | sonnet |
| `explorer`    | Análise profunda de repo → `context.md`        | opus   |
| `context`     | Carrega o contexto vivo do projeto na sessão   | sonnet |

## Skills

**Conhecimento (linguagens & domínios):** `python` · `typescript` · `ai-engineer` ·
`api-design` · `frontend-ui` · `security` · `observability`

**Capacidade (metodologia & processo):** `implement` · `design` · `test` · `review` ·
`research` · `operate` · `manage` · `environment` · `ci-cd`

**Comando & workflow:** `feature` · `drink-context`

Cada skill traz um `SKILL.md` e, quando aplicável, uma pasta `references/` com o aprofundamento.

## Workflows

| Workflow         | O que faz                                                                  |
| ---------------- | -------------------------------------------------------------------------- |
| `create-feature` | Pipeline ponta-a-ponta: user_history → dev → loop[qa+sre] → PR (via `code-host`) |

## Portabilidade entre harness

`agents/` e `skills/` são a base reutilizável. O que é específico do Claude Code (`CLAUDE.md`,
`settings.json`, `workflows/`, `SETUP.md`) fica isolado em `claude-code/`, para que adaptar a
outro harness signifique acrescentar uma pasta irmã — não reescrever a biblioteca.

## Licença

Ver [`LICENSE`](LICENSE).
