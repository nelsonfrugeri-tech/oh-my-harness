# harness config library

Biblioteca portátil de **agents**, **skills** e **workflows** para harness de IA
(Claude Code, e adaptável a Codex e Cursor). O objetivo é ser agnóstica de máquina e
de harness: nada aqui é acoplado a uma ferramenta MCP específica ou a um caminho local.

## Princípios

- **Portátil entre máquinas** — as tools concretas (GitHub numa máquina, GitLab noutra)
  entram por um único ponto de plugue; os agents e skills nunca citam uma tool concreta.
- **Portátil entre harness** — agents e skills são a base reutilizável; o que é específico
  do Claude Code (CLAUDE.md, settings.json, workflows) fica isolado em `claude-code/`.
- **pt-BR na instrução, inglês no código** — a prosa dos agents/skills é em pt-BR; código,
  comentários, docstrings e termos técnicos ficam em inglês.

## Estrutura

```
.
├── agents/           roster de subagents (name, description, tools, model)
├── skills/           knowledge base com progressive disclosure (SKILL.md + references/)
├── claude-code/      específico do Claude Code
│   ├── CLAUDE.md     regras duras + a tabela de capabilities (o plugue)
│   ├── settings.json permissions default
│   └── workflows/    orquestração determinística (Workflow API)
└── install.sh        symlinks agents/ e skills/ para ~/.claude/
```

## Capabilities — o plugue de tools

Agents e skills referenciam **capabilities** abstratas (`code-host`, `ci`, `memory`, `web`),
nunca uma tool concreta. A tabela em `claude-code/CLAUDE.md` (seção *Ambiente & Tools*)
mapeia cada capability para a tool desta máquina. Ao trocar de máquina, você edita só
essa tabela — os agents e skills funcionam sem alteração.

| Capability  | Papel                                  | Exemplo por máquina        |
| ----------- | -------------------------------------- | -------------------------- |
| `code-host` | Pull/Merge Requests, issues            | `mcp__github__*` / GitLab  |
| `ci`        | Pipelines de CI/CD                     | GitHub Actions / GitLab CI |
| `memory`    | Notas/contexto persistente (opcional)  | qualquer memory MCP        |
| `web`       | Busca e fetch                          | `WebSearch`, `WebFetch`    |

## Instalação

```bash
./install.sh                        # linka agents/ e skills/ em ~/.claude/
CLAUDE_HOME=/caminho ./install.sh   # home customizado
```

Depois, edite a seção *Ambiente & Tools* em `~/.claude/CLAUDE.md` para plugar as tools
da máquina.

## Padrões de código

As regras invioláveis de qualidade de código (tipagem total, imutabilidade, funções e
arquivos pequenos, guard clauses, design pattern no lugar de cadeias de `if/elif`, quality
gate ao final) vivem em `skills/implement/references/code-craft.md` — fonte única,
referenciada pela skill `implement` e reusada pela skill `review`.
