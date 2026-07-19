# CLAUDE.md

Regras vinculantes deste ambiente. Aplicam-se a toda sessão do harness e a todo subagent.

---

## Idioma

- **Conversa, prosa instrucional, títulos e explicações** → pt-BR.
- **Termos técnicos, jargões e nomes próprios** de engenharia de software → inglês inline (ex.: *guard clause*, *idempotency*, *strangler fig*, RAG, OAuth).
- **Base de código** — código-fonte, comentários, docstrings e documentação que vive num repositório de software → **inglês**.
- **Chaves de frontmatter, nomes de skill/agent e triggers** → inglês em kebab-case.

Regra prática: você fala comigo em pt-BR; o que vai pro repositório de software é escrito em inglês.

---

## Ambiente & Tools (o plugue de capabilities)

Agents e skills **nunca** citam uma tool concreta (ex.: `mcp__github__create_pull_request`). Eles referenciam uma **capability** abstrata. Esta seção mapeia cada capability para a tool concreta **desta máquina** — é o único lugar acoplado ao ambiente. Ao trocar de máquina, você edita só esta tabela.

| Capability   | Papel                                             | Tool concreta nesta máquina                 |
| ------------ | ------------------------------------------------- | ------------------------------------------- |
| `code-host`  | Pull/Merge Requests, issues, reviews remotos      | _(preencher — ex.: `mcp__github__*`)_       |
| `ci`         | Pipelines de CI/CD                                | _(preencher — ex.: GitHub Actions via CLI)_ |
| `memory`     | Notas/contexto persistente do projeto (opcional)  | _(preencher, ou `nenhuma`)_                 |
| `web`        | Busca e fetch na web                              | `WebSearch`, `WebFetch`                      |

**Primitivos universais** (sempre disponíveis, não precisam de plugue): `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`.

### Como resolver uma capability

1. A prosa do agent/skill pede uma capability (ex.: *"abra um Pull/Merge Request via `code-host`"*).
2. Você lê esta tabela e usa a tool concreta mapeada. Se a tool for MCP e estiver deferida, carregue-a via `ToolSearch` antes de chamar.
3. Se a capability estiver **vazia ou `nenhuma`**: degrade com elegância — faça a parte possível e diga claramente ao usuário o que ficou pendente por falta da tool. Nunca invente uma tool.

> Exemplo: na máquina pessoal `code-host → mcp__github__*`; na máquina da empresa `code-host → mcp__gitlab__*`. O mesmo agent funciona nas duas sem edição.

---

## Padrões de código — ativação obrigatória

**Antes de escrever, modificar ou revisar qualquer linha de código**, siga integralmente os *Padrões de código — invioláveis* da skill `implement` (corpo + `references/code-craft.md`). Não são sugestões. Resumo do que elas impõem: tipagem total, imutabilidade por padrão, funções e arquivos pequenos, guard clauses no lugar de aninhamento, design pattern no lugar de cadeias de `if/elif`, sem retornar `None`, comentário só pro *porquê*, e **quality gate ao final** (format → lint → typecheck → test, com o comando descoberto do projeto, nunca hardcoded).

---

## Fluxo de commit

Quando **você pedir um commit**, antes de rodar `git commit`:

1. **Format + lint** primeiro (alteram arquivos — precisam vir antes de revisar/testar).
2. **Em paralelo:**
   - **Code-review** — abra um subagent fixado no modelo **fable** que revisa o diff *staged* usando a skill `review` + as regras de code-craft.
   - **Testes** — rode a suite do projeto (comece leve: `Bash` em background; promova a subagent com modelo barato só se quiser triage automático de falha).
3. **Gate:** só commita se o review não tiver blocker **e** os testes passarem. Caso contrário, corrija e repita.

O comando de teste/lint é **descoberto** (Makefile target → config do projeto → default da linguagem), nunca hardcoded.

---

## Trabalho longo → subagent em background

Quando eu pedir uma tarefa **substancial e autônoma** — provavelmente acima de ~3 min, bem-delimitada, com entregável claro, sem exigir ida-e-volta comigo no meio — **abra um subagent em background** e continue disponível pra conversar. Não trave a thread principal executando a tarefa inteira.

- **Delegue** quando é: demorada, bem-escopada, não-interativa, roda sozinha.
- **Faça inline** quando é rápida (o custo de spawn supera o trabalho), precisa de interação constante, ou você precisa do resultado agora pra continuar a mesma resposta.
- Os "3 min" são intuição de *"isso é longo e autônomo?"*, não um cronômetro. Subagent não spawna subagent nem fala comigo no meio — tarefa que precise disso fica no loop principal.
