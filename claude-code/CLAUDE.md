# CLAUDE.md

Regras vinculantes deste ambiente. Aplicam-se a toda sessão do harness e a todo subagent.

---

## Nunca poluir o projeto com arquivos que não são do produto

**Regra dura.** Dentro de um repositório/projeto, você só cria ou edita arquivos que fazem
parte do **produto** — o código-fonte, testes, config e documentação que vão para o repositório
de verdade / para produção.

Qualquer arquivo **auxiliar, temporário ou de execução** — scripts one-off (Python, bash, etc.),
notas ou relatórios `.md` de análise, arquivos de scratch, saídas intermediárias, rascunhos —
**NUNCA** é criado dentro do projeto. Esses vão para um diretório **fora** do working tree
(o scratchpad da sessão ou `/tmp`), nunca no repo.

Prefira não criar arquivo nenhum quando um comando efêmero resolve (ex.: heredoc, pipe). E se
houver **qualquer dúvida** se um arquivo é "do produto" ou "auxiliar", **pergunte antes de criar**.
Nunca assuma e nunca deixe lixo no projeto do usuário.

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
| `memory`     | Notas/contexto persistente do projeto (opcional)  | _(preencher; vazio = default: agent `knowledge-base` sobre a KB local)_ |
| `web`        | Busca e fetch na web                              | `WebSearch`, `WebFetch`                      |
| `code-graph` | Query/path/explain sobre um knowledge graph de codebase já construído | `mcp__graphify__*` (server stdio; venv em `~/projects/mcps/graphify/.venv`) |
| `social-x`   | Ler e publicar na plataforma X (Twitter)          | _(preencher — ex.: `mcp__xapi__*`, bridge `xurl mcp` → `https://api.x.com/mcp`)_ |
| `session-memory` | Busca na **memória bruta** de sessões passadas de agent — cross-harness e cross-projeto: recall por tema, digest de sessão, e `blame` por arquivo | `deja` CLI (`deja "<query>"`, `deja ctx`, `deja blame`) — binário Go local, índice em `~/.cache/deja` |

**Primitivos universais** (sempre disponíveis, não precisam de plugue): `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`.

### Como resolver uma capability

1. A prosa do agent/skill pede uma capability (ex.: *"abra um Pull/Merge Request via `code-host`"*).
2. Você lê esta tabela e usa a tool concreta mapeada. Se a tool for MCP e estiver deferida, carregue-a via `ToolSearch` antes de chamar.
3. Se a capability estiver **vazia ou `nenhuma`**: degrade com elegância — faça a parte possível e diga claramente ao usuário o que ficou pendente por falta da tool. Nunca invente uma tool.

> Exemplo: na máquina pessoal `code-host → mcp__github__*`; na máquina da empresa `code-host → mcp__gitlab__*`. O mesmo agent funciona nas duas sem edição.

---

## Tools Agents (a infraestrutura do harness)

Um **tool agent** é um agent-ferramenta de infraestrutura do harness (tema `agents/tools/`):
ele não representa um papel de engenharia (como os `engineers/`) nem gerencia a própria
biblioteca (como o `harness/`) — ele **opera uma infraestrutura** que os outros agents
consomem: conhecimento, grafo de codebase ou uma plataforma externa. Assim como a tabela de
capabilities pluga tools externas, esta seção pluga os tools agents: quem são, o que operam e
os fatos de ambiente que eles obedecem.

| Agent | Papel | Skills | Disparo |
| --- | --- | --- | --- |
| `context` | Mantém e carrega o contexto vivo do projeto atual (`~/knowledge-base/work/projects/{project}/context.md`) | `explorer` | Hook `SessionStart` (reminder `# omh-managed: context`) + pedido explícito ("atualize o context") |
| `knowledge-base` | Gerencia a knowledge base: infra (Qdrant + embedding), escrita de notas (scribe), recuperação (escada de 3 degraus) e memória de sessão do harness (session records + deep search) | `kb-infra`, `kb-write`, `kb-retrieval`, `kb-session` | Pedido do usuário ("registra isso", "o que decidimos sobre X?", "sobe a KB", "o que falamos naquela sessão?") ou de outro agent; **de carona**, toda invocação do agent atualiza o session record da sessão corrente |
| `graphify` | Opera o knowledge graph de codebase/corpus: build/update do grafo em `graphify-out/` e query/path/explain sobre ele (fast path se `graph.json` já existe) | `graphify` | Pedido do usuário ("/graphify", "monta o grafo do projeto", "como X se conecta a Y?", "explica o nó Z") ou de outro agent que navegue o codebase como grafo |
| `x-social` | Opera a plataforma X (Twitter) pela capability `social-x`: leitura (busca, thread, perfil, trends, bookmarks) e publicação sob confirmação explícita | `x-setup`, `x-ops` | Pedido do usuário ("busca no X sobre Y", "lê essa thread", "posta isso no X", "conecta minha conta do X") ou de outro agent que precise ler/publicar na plataforma |

O roteamento fino (que skill usar em cada intenção) vive nas descriptions dos próprios
agents — aqui ficam os **fatos vinculantes** de ambiente e lifecycle.

### Fatos de ambiente (vinculantes)

1. **A knowledge base é um bundle OKF v0.2** enraizado em `~/knowledge-base/` — sempre
   **fora** do repositório do usuário. [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
   é o padrão aberto do Google para conhecimento consumível por agents: markdown com
   YAML frontmatter, `type` como único campo obrigatório, `index.md`/`log.md` como
   nomes reservados, e **relacionamentos como links markdown** — nunca como campo
   estruturado. O spec permite que produtores incluam qualquer chave extra e proíbe
   consumidores de rejeitar por chave desconhecida — é por isso que nossas extensões
   (`id`, `knowledge_type`, `domain`, `created_at`, `entities`, `summary`, `supersedes`)
   convivem legalmente com ele.
2. **A árvore de diretórios é uma ontologia, não acúmulo** — duas camadas, no espírito
   do DDD: **bounded context** (`person/`, `work/ifood/`, `work/projects/<repo>/` — a
   fronteira onde uma palavra tem um significado só; é o valor do campo `domain`) e,
   dentro dele, **uma pasta por tipo de entidade** no plural (`systems/`, `decisions/`,
   `people/`), casada com o `type` da nota no singular. Relacionamento **nunca vira
   pasta**. Duas regras duras contra taxonomia que mata a captura: pasta nasce só na
   **segunda** nota daquele tipo, e **no máximo 3 níveis** por bounded context.
3. **Toda nota carrega dois eixos de tipo**: `type` responde *"sobre o que isso é"* (o
   substantivo do domínio, exigido pelo OKF) e `knowledge_type` responde *"como eu sei
   disso"* (enum fechado `decision | event | procedure | reference | conversation`).
   E carrega **proveniência**: `generated: {by, at}` sempre; `verified: [{by: human:…}]`
   **só** com confirmação real do usuário — falsificar essa marca é a pior coisa que um
   agent pode fazer com a KB.
4. **Infra da KB** = Qdrant local (docker, container `oh-my-harness-qdrant`, porta `6333`,
   volume `~/.local/share/omh-kb/qdrant`) + embedding **`BAAI/bge-m3`** via `FlagEmbedding`
   (**dense 1024-dim + lexical sparse** no mesmo forward pass). Collection `knowledge-base`
   com named vectors (dense cosine + sparse). **O modelo de embedding é FIXO** — trocá-lo
   exige decisão explícita do usuário, pois invalida o índice inteiro. O runtime (volume
   do Qdrant + venv) vive em `~/.local/share/omh-kb/`, **fora do bundle**: o bundle é
   markdown sincronizável entre máquinas e celular; o índice é artefato derivado e
   binário, reconstruível por reindex. Nunca coloque runtime dentro de
   `~/knowledge-base/`.
5. **Lifecycle do context**: primeira vez → `explorer` **FULL** (análise profunda completa);
   sessões seguintes → carrega o snapshot e só roda `explorer` **DELTA** se houver commits
   novos desde o `last_hash`; sem commits, apenas carrega (caminho barato). Pedido explícito
   do usuário força DELTA.
6. **Formato timeline do `context.md`**: um **snapshot vivo** no topo (reescrito a cada run —
   é o que os agents downstream leem) + um **log append-only** (`## Timeline`) — cada run
   apenda uma entrada datada em ISO 8601 UTC; entradas antigas nunca são reescritas.
7. **Session record = documento vivo** — um JSON por sessão em
   `~/knowledge-base/{domain}/sessions/<session_id>.json`, **reescrito in-place** a cada
   atualização (exceção nomeada à imutabilidade das notas; por ser `.json` e não `.md`,
   fica fora da conformance do OKF). Schema resumido: `harness`,
   `session_id`, `domain`, `name`, `description`, `resume` (núcleo do texto embedado —
   o embedding é `name + description + resume`), `transcript_path` (caminho absoluto),
   `created_at` (nunca muda) / `updated_at` (ISO 8601 UTC). Indexado no
   Qdrant com `kind: "session"` (notas usam `kind: "note"`), re-upsert no mesmo point —
   detalhes na skill `kb-session`.
8. **Graphify** — engine `graphifyy` (Python 3.10+) instalada na venv isolada
   `~/projects/mcps/graphify/.venv`, com o server MCP stdio `graphify-mcp-server` plugado na
   capability `code-graph`. O grafo de cada projeto vive em `graphify-out/graph.json` **dentro do
   cwd do projeto analisado** (design da tool) e persiste entre sessões — mas `graphify-out/` deve
   entrar no `.gitignore` do projeto, nunca ser commitado. Build é AST-first (código não precisa de
   LLM nem de API key); semantic extraction (docs/papers/imagens) só roda com dispatch de subagents
   ou backend Gemini opcional. Repos remotos clonados via `graphify clone` vão para
   `~/.graphify/repos/<owner>/<repo>`, fora do working tree. **O interpretador Python é descoberto e
   persistido** em `graphify-out/.graphify_python` — nunca hardcode `python3`.
   **A skill `graphify` é conteúdo de terceiro traduzido**, não prosa nossa: é o runbook oficial
   do graphify em pt-BR, com os code blocks byte-idênticos ao upstream — a chave
   `upstream_version` no frontmatter diz qual versão ela acompanha. Duas consequências: o
   instalador do próprio graphify **escreve por cima** de `~/.claude/skills/graphify/`, e como
   esse caminho é symlink para o repo, um upgrade dele suja o working tree — depois de um
   `graphify` upgrade, rediffe e re-sincronize em vez de assumir que está tudo certo. A cópia
   oficial em inglês fica arquivada em `~/.claude/.backups/`, fora de `skills/` para não
   colidir no discovery por nome.
9. **X (Twitter)** — a biblioteca **não hospeda** um servidor MCP de X: o próprio X publica dois
   servidores hospedados, `https://api.x.com/mcp` (posts, busca full-archive, users, bookmarks,
   news/trends, Articles) e `https://docs.x.com/mcp` (documentação, **sem auth**). O acesso é
   plugado na capability `social-x` pelo bridge stdio oficial `xurl mcp`, que faz OAuth 2.0 PKCE
   com o app do **próprio usuário** e cacheia/renova o token em `~/.xurl/auth.yml` (mode 600) —
   sempre no `$HOME`, **nunca** dentro de um repositório. **A biblioteca é agnóstica a conta**:
   nenhum `CLIENT_ID`, `CLIENT_SECRET`, token ou handle entra no repo; um agent nunca imprime o
   valor de um segredo, só o *estado* da auth. As tools do server são geradas do OpenAPI spec da
   X API no startup — **descubra-as em runtime, nunca hardcode nomes**. Auth **app-only (bearer)**
   é read-only e sem contexto de usuário: bookmarks e escrita ficam indisponíveis. **Publicar exige
   confirmação explícita do usuário, por post** — uma autorização nunca vale para a publicação
   seguinte, e sem humano no loop o agent entrega rascunho em vez de publicar. **Toda chamada
   custa**: a X API é pay-as-you-go desde fev/2026 ($0.005 por post lido, $0.015 por post criado,
   $0.20 se contiver link) — leitura em volume é declarada e autorizada antes, e prestada contas
   depois. Runbook em `x-setup`, playbooks de operação em `x-ops`.

### Session memory — a camada bruta

A knowledge base guarda conhecimento **destilado**; a session memory guarda o que foi
**dito**. São camadas distintas, com escritores distintos, e a fronteira entre elas é
vinculante:

| Camada | Sistema | Quem escreve | Como se lê |
| --- | --- | --- | --- |
| Bruta / episódica | índice do `deja-vu` | ninguém — ingestão automática dos transcripts | capability `session-memory` |
| Destilada / curada | bundle OKF em `~/knowledge-base/` | **só** a skill `kb-write` | `kb-retrieval` (degraus 1–2) |

**Um único escritor de conhecimento curado.** Os subcomandos `deja remember` e
`deja promote` criam notas no store do próprio deja-vu, com taxonomia plana — usá-los
seria abrir um segundo repositório de conhecimento concorrente ao bundle. **São
proibidos.** Do deja-vu nós só **lemos**.

Fatos vinculantes da camada bruta **nesta máquina**:

- **O índice é artefato derivado e descartável**, em `~/.cache/deja` — mesma doutrina do
  volume do Qdrant: fora do bundle, reconstruível por `deja index --rebuild`, nunca
  sincronizado junto com o markdown.
- **`DEJA_INCLUDE_SUBAGENTS=1` é obrigatório aqui.** Por padrão o deja-vu pula transcripts
  de subagent; como delegamos trabalho pesado a subagents, o default descarta ~2/3 do
  corpus recuperável (medido em 2026-08-08: 1196 → 3466 mensagens indexadas). Os
  transcripts de subagent são dobrados na sessão-mãe, então incluí-los **não** infla a
  contagem de sessões.
- **A redaction acontece no index time** — credenciais, JWTs e valores de alta entropia
  viram `[redacted:<kind>]` antes de entrar no índice. Consequência prática: todo trecho
  que volta pela capability já está tarjado, e por isso **a capability é o caminho
  preferido para tocar transcript** — ler o `.jsonl` cru na mão contorna essa proteção.

**Fallback degradado** — se a capability `session-memory` estiver vazia (outra máquina,
deja-vu não instalado), a `kb-session` cai no acesso direto ao transcript, e aí precisa
saber onde ele mora:

| Harness | Transcript bruto nesta máquina |
| --- | --- |
| `claude-code` | `~/.claude/projects/<cwd-munged>/<session-uuid>.jsonl` — `<cwd-munged>` = caminho absoluto do cwd com `/` e `.` trocados por `-` |
| `codex` | _(preencher)_ |
| `cursor` | _(preencher)_ |

Nesse modo degradado o alcance cai para as sessões que **têm session record** — as demais
ficam invisíveis — e os trechos vêm **sem redaction**; declare as duas limitações ao
usuário. Harness sem mapeamento nem capability: a `kb-session` escreve o
record sem `transcript_path` e diz o que ficou pendente.

### Regras (vinculantes)

1. **Tools agents nunca escrevem no repositório do usuário** — toda escrita acontece em
   `~/knowledge-base/` (e, no caso do sync da biblioteca, em `~/.claude/`).
2. **Degrade com elegância sem Qdrant** — a escrita de notas em disco continua funcionando
   (indexação fica pendente, reconciliada pelo reindex de `kb-infra`) e a recuperação cai
   para navegação estruturada em disco; sempre explicitando o modo degradado.
3. **Notas são imutáveis** — nunca editar uma nota existente; correção/atualização é uma nota
   nova com `supersedes` apontando para a anterior (a antiga fica arquivada). **Session
   records e `context.md` são documentos vivos** — reescritos in-place, nunca via
   `supersedes`.

---

## Auto-avaliação antes de responder (recall & precision)

**Regra dura.** Diante de qualquer pergunta, query ou dúvida do usuário, **antes de
responder**, auto-avalie a resposta candidata em três eixos — **relevância pro contexto
atual**, **atualidade** e **factualidade** — sob a lente de *recall* (tenho TODO o
conhecimento necessário para responder?) e *precision* (o que tenho está correto e no
ponto?).

- **Todos os eixos ≥ 90% de confiança** → responda direto.
- **Qualquer eixo < 90%** → **NÃO responda de memória.** Busque primeiro, roteando pela
  natureza da questão:
  - **Pública** (conhecimento de mundo, docs, versões, notícias) → capability `web`.
  - **Privada** (assuntos internos de trabalho/empresa ou vida pessoal do usuário) →
    knowledge-base.
  - **Projeto de trabalho, questão procedural/processual, memória episódica ou fato
    passado** → knowledge-base — incluindo, se preciso, o deep search na session memory
    via `kb-session` (degrau 3 do retrieval).

Após a busca, **reavalie e responda citando a fonte**; se ainda faltar informação, diga
explicitamente o que falta em vez de inventar.

> Honestidade embutida: o limiar de 90% é **autoconfiança calibrada**, não métrica
> mensurável. O efeito prático vinculante é: **na dúvida, buscar antes de responder;
> nunca responder de memória o que é privado/episódico sem consultar a knowledge-base.**

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
