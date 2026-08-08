# CLAUDE.md

Regras vinculantes deste ambiente. Aplicam-se a toda sessão do harness e a todo subagent.

<!-- Alvo de tamanho: < 200 linhas (recomendação oficial do Claude Code). Detalhe operacional
     mora nas skills, que carregam sob demanda; aqui só fica o que precisa valer em TODA sessão.
     Antes de adicionar uma linha, pergunte: "remover isto faria o Claude errar?" Se não, não entra. -->

---

## Idioma

- **Conversa, prosa instrucional, títulos e explicações** → pt-BR.
- **Termos técnicos e nomes próprios** de engenharia → inglês inline (*guard clause*, RAG, OAuth).
- **Base de código** — código, comentários, docstrings e docs que vivem num repositório → **inglês**.
- **Nomes de skill/agent e triggers** → inglês em kebab-case. **Chaves de frontmatter** → inglês, em kebab-case ou snake_case (o ecossistema usa `knowledge_type`, `created_at`, `upstream_version`).
- **Conteúdo *vendored* de terceiro** (skill/runbook publicado por outro projeto) → fica **no idioma original**. Traduzir cria um fork que dá drift silencioso a cada release upstream; marque a proveniência com `upstream_version`.

---

## Nunca poluir o projeto com arquivos que não são do produto

**REGRA DURA.** Dentro de um repositório você só cria ou edita arquivos **do produto** — código, testes, config e documentação que vão pro repositório de verdade.

Arquivo **auxiliar, temporário ou de execução** — script one-off, relatório `.md` de análise, scratch, saída intermediária — **NUNCA** entra no projeto. Vai pro scratchpad da sessão ou `/tmp`. Prefira comando efêmero (heredoc, pipe) a criar arquivo. Na dúvida se é "produto" ou "auxiliar", **pergunte antes de criar**.

---

## Ambiente & Tools (o plugue de capabilities)

Agents e skills **nunca** citam uma tool concreta. Eles referenciam uma **capability** abstrata; esta tabela é o único lugar acoplado ao ambiente. Ao trocar de máquina, você edita só ela.

| Capability   | Papel                                             | Tool concreta nesta máquina                 |
| ------------ | ------------------------------------------------- | ------------------------------------------- |
| `code-host`  | Pull/Merge Requests, issues, reviews remotos      | _(preencher — ex.: `mcp__github__*`)_       |
| `ci`         | Pipelines de CI/CD                                | _(preencher)_                                |
| `memory`     | Notas/contexto persistente do projeto (opcional)  | _(vazio = default: agent `knowledge-base`)_ |
| `web`        | Busca e fetch na web                              | `WebSearch`, `WebFetch`                      |
| `code-graph` | Query/path/explain sobre um knowledge graph de codebase | `mcp__graphify__*` (stdio; venv em `~/projects/mcps/graphify/.venv`) |
| `social-x`   | Ler e publicar na plataforma X (Twitter)          | `mcp__xapi__*` via bridge `xurl mcp` → `https://api.x.com/mcp` |
| `session-memory` | Busca na memória bruta de sessões passadas — cross-harness e cross-projeto: recall por tema, digest, `blame` por arquivo | `deja` CLI / `mcp__deja__*` — índice em `~/.cache/deja` |

**Primitivos universais** (não precisam de plugue): `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`.

**Como resolver:** a prosa pede a capability → você lê esta tabela e usa a tool mapeada (se for MCP deferida, carregue via `ToolSearch` antes). Capability **vazia** → degrade com elegância: faça a parte possível e diga o que ficou pendente. **Nunca invente uma tool.**

---

## Tools Agents (a infraestrutura do harness)

Um **tool agent** opera uma infraestrutura que os outros agents consomem — conhecimento, grafo de codebase ou plataforma externa.

| Agent | Papel | Skills |
| --- | --- | --- |
| `context` | Contexto vivo do projeto atual em `~/knowledge-base/work/projects/{project}/context.md` | `explorer` |
| `knowledge-base` | Infra (Qdrant + embedding), escrita de notas, recuperação em 3 degraus e memória de sessão | `kb-infra`, `kb-write`, `kb-retrieval`, `kb-session` |
| `graphify` | Knowledge graph de codebase: build/update em `graphify-out/` e query/path/explain | `graphify` |
| `x-social` | Lê e publica no X; escrita sob confirmação explícita | `x-setup`, `x-ops` |

O roteamento fino vive nas descriptions dos agents; **a mecânica vive nas skills** — não a duplique aqui.

### Fatos de ambiente (vinculantes)

Só o que não dá pra descobrir lendo as skills:

1. **A knowledge base vive em `~/knowledge-base/`** — um bundle OKF v0.2, **sempre fora** do repositório do usuário. Runtime (volume do Qdrant, venvs) vive em `~/.local/share/omh-kb/`, **nunca dentro do bundle**: o bundle é markdown sincronizável; o índice é artefato derivado.
2. **O modelo de embedding é FIXO** (`BAAI/bge-m3`) — trocá-lo invalida o índice inteiro e exige decisão explícita do usuário.
3. **`DEJA_INCLUDE_SUBAGENTS=1` é obrigatório** (exportado em `~/.zshenv`). Sem ele o deja-vu pula transcripts de subagent e descarta ~2/3 do corpus recuperável.
4. **A redaction do deja-vu é piso, não garantia** — trechos que voltam pela capability já vêm tarjados, e por isso ela é o caminho preferido pra tocar transcript; ler o `.jsonl` cru contorna a proteção. Ao exportar para fora da máquina, revise antes.
5. **O wiring do deja-vu é do `deja install --auto`**, não do nosso sync — ele pluga MCP e hooks com paths desta máquina, e instala a skill `deja-history` em `~/.claude/skills/`: ela é **dele, não órfã**; o sync não deve removê-la.
6. **A skill `graphify` é vendored do upstream, em inglês.** O instalador do graphify escreve por cima de `~/.claude/skills/graphify/`, que é symlink pro repo — depois de um upgrade, rediffe e re-sincronize.
7. **A biblioteca é agnóstica a conta.** Nenhum `CLIENT_ID`, `CLIENT_SECRET`, token ou handle entra no repo; um agent reporta o *estado* da auth, nunca o valor de um segredo.

### Duas camadas de memória, dois escritores

| Camada | Onde | Quem escreve | Como se lê |
| --- | --- | --- | --- |
| Bruta / episódica — o que foi **dito** | índice do `deja-vu` | ninguém: ingestão automática | capability `session-memory` |
| Destilada / curada — o que **ficou valendo** | bundle OKF em `~/knowledge-base/` | **só** a skill `kb-write` | `kb-retrieval` |

**Um único escritor de conhecimento curado.** O mecanismo de notas da capability `session-memory` (`remember`/`promote`) abriria um segundo repositório concorrente ao bundle — **é proibido**. Do deja-vu nós só lemos.

### Regras (vinculantes)

1. **Tools agents nunca escrevem no repositório do usuário** — escrita em `~/knowledge-base/` (e `~/.claude/`, no sync da biblioteca).
2. **Degrade com elegância sem infra** — sem Qdrant, a escrita em disco continua e a indexação fica pendente; a recuperação cai pra navegação estruturada. Sempre declare o modo degradado.
3. **Notas são imutáveis** — correção é nota nova com `supersedes`. **Session records e `context.md` são documentos vivos**, reescritos in-place.

---

## Auto-avaliação antes de responder

**Na dúvida, busque antes de responder — nunca responda de memória o que é privado ou episódico.**

Antes de responder, avalie a resposta candidata em relevância, atualidade e factualidade. Se qualquer eixo não estiver sólido, busque primeiro, roteando pela natureza da pergunta:

- **Pública** (mundo, docs, versões, notícias) → capability `web`.
- **Privada, episódica, ou fato passado de projeto/processo** → knowledge-base, incluindo o deep search na session memory (degrau 3 do `kb-retrieval`).

Depois da busca, **responda citando a fonte**. Se ainda faltar informação, diga o que falta em vez de inventar.

---

## Padrões de código — ativação obrigatória

**Antes de escrever, modificar ou revisar qualquer linha de código**, siga os *Padrões de código — invioláveis* da skill `implement` (corpo + `references/code-craft.md`). Não são sugestões.

---

## Fluxo de commit

Quando **você pedir um commit**, antes de `git commit`:

1. **Format + lint** primeiro (alteram arquivos).
2. **Em paralelo:** code-review num subagent fixado no modelo **fable** sobre o diff *staged* (skill `review` + code-craft), e a suite de testes do projeto.
3. **Gate:** só commita se o review não tiver blocker **e** os testes passarem. Senão, corrija e repita.

O comando de teste/lint é **descoberto** (Makefile target → config do projeto → default da linguagem), nunca hardcoded.

---

## Trabalho longo → subagent em background

Tarefa **substancial, bem-escopada e não-interativa** → **subagent em background**, e você segue disponível pra conversar. Tarefa rápida, ou cujo resultado você precisa agora pra continuar a mesma resposta → inline.

Subagent não spawna subagent nem fala comigo no meio; tarefa que precise disso fica no loop principal.
