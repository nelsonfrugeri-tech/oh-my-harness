# CLAUDE.md

Regras vinculantes deste ambiente. Aplicam-se a toda sessão do harness e a todo subagent.

<!-- Alvo de tamanho: < 200 linhas (recomendação oficial do Claude Code). Detalhe operacional
     mora nas skills, que carregam sob demanda; aqui só fica o que precisa valer em TODA sessão.
     Antes de adicionar uma linha, pergunte: "remover isto faria o Claude errar?" Se não, não entra. -->

---

## Política de permissões — fluxo contínuo, confirmação para destruição

Prossiga sem confirmação para operações normais e reversíveis dentro do escopo solicitado: ler,
pesquisar, criar, editar, instalar dependências, executar comandos e testes e acessar serviços
necessários à tarefa.

Peça confirmação explícita imediatamente antes de qualquer operação destrutiva: excluir arquivos,
diretórios, código, branches, tags, dados, recursos ou infraestrutura; truncar ou sobrescrever
conteúdo de recuperação difícil; executar operações destrutivas de Git; `DROP` ou `TRUNCATE`; ou
usar uma tool marcada como destrutiva. Resolva antes os alvos exatos, explique o que mudará e como
recuperar, e prefira uma movimentação recuperável quando possível. A autorização vale somente para
os alvos apresentados; mudança de escopo exige nova confirmação.

Sandbox e command rules são defesa em profundidade. Esta regra comportamental continua vinculante
para scripts, mutações indiretas e tools que escapem dos prefixos configurados.

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
| `databricks-sql` | SQL governado, schema checks e smoke tests no Databricks | _(configurar MCP gerenciado de SQL; fallback REST/CLI)_ |
| `databricks-lakeview` | Export, draft create/update e publish de dashboards AI/BI | _(configurar provider REST, CLI ou MCP fino)_ |
| `browser` | Validação visual do dashboard final | Browser automation do harness quando disponível |
| `social-x`   | Ler e publicar na plataforma X (Twitter)          | `mcp__xapi__*` via bridge `xurl mcp` → `https://api.x.com/mcp` |
| `team-messaging` | Ler contexto e criar rascunhos de mensagens de time | Slack MCP — drafts e leitura limitada ao contexto necessário |
| `session-memory` | Busca na memória bruta de sessões passadas — cross-harness e cross-projeto: recall por tema, digest, `blame` por arquivo | `deja` CLI / `mcp__deja__*` — índice em `~/.cache/deja` |
| `file-sync` | Replica case bundles entre máquinas e verifica propagação | _(configurar engine e sync root)_ |
| `tunnel` | Exposição temporária e autenticada de um site local | _(opcional; configurar provider aprovado)_ |

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
| `sync` | Monta case bundles portáteis e verifica propagação entre máquinas | `sync-bundle`, `sync-transport` |
| `slack` | Lê contexto e prepara rascunhos no tom pessoal do usuário | `slack-messaging` |
| `x-social` | Lê e publica no X; escrita sob confirmação explícita | `x-setup`, `x-ops` |
| `site` | Gera sites visuais citados e os expõe somente após aprovação | `site-report`, `site-expose` |

O roteamento fino vive nas descriptions dos agents; **a mecânica vive nas skills** — não a duplique aqui.

### Fatos de ambiente (vinculantes)

Só o que não dá pra descobrir lendo as skills:

1. **A knowledge base vive em `~/knowledge-base/`** — um bundle OKF v0.2, **sempre fora** do repositório do usuário. Runtime (volume do Qdrant, venvs) vive em `~/.local/share/omh-kb/`, **nunca dentro do bundle**: o bundle é markdown sincronizável; o índice é artefato derivado.
2. **O modelo de embedding é FIXO** (`BAAI/bge-m3`) — trocá-lo invalida o índice inteiro e exige decisão explícita do usuário.
3. **A indexação de transcripts pelo Deja é opt-in e exige autorização explícita.** Registrar o MCP não indexa o histórico. Depois da autorização, `DEJA_INCLUDE_SUBAGENTS=1` é obrigatório para não omitir transcripts de subagent.
4. **A redaction do deja-vu é piso, não garantia** — trechos que voltam pela capability já vêm tarjados, e por isso ela é o caminho preferido pra tocar transcript; ler o `.jsonl` cru contorna a proteção. Ao exportar para fora da máquina, revise antes.
5. **O wiring do deja-vu é do `deja install --auto`**, não do nosso sync — ele pluga MCP e hooks com paths desta máquina, e instala a skill `deja-history` em `~/.claude/skills/`: ela é **dele, não órfã**; o sync não deve removê-la.
6. **A skill `graphify` é vendored do upstream, em inglês.** O instalador do graphify escreve por cima de `~/.claude/skills/graphify/`, que é symlink pro repo — depois de um upgrade, rediffe e re-sincronize.
7. **A biblioteca é agnóstica a conta.** Nenhum `CLIENT_ID`, `CLIENT_SECRET`, token ou handle entra no repo; um agent reporta o *estado* da auth, nunca o valor de um segredo.
8. **O sync root default é `~/sync`.** Tudo dentro dele é cópia; a fonte da verdade permanece na knowledge base, session memory ou repositório. Só declare entrega após a capability `file-sync` provar propagação completa, e nunca inclua segredo ou `.env` num case bundle.

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

<!-- software-evidence:start -->
## Engenharia de software orientada a evidência

Em trabalho de engenharia de software, separe o que a evidência disponível estabelece do que ainda
está sendo inferido. Aplique este contrato a design de features, diagnóstico de bugs, implementação,
review, arquitetura, entrega e operações.

Classifique alegações materiais explicitamente sempre que o status delas afetar uma decisão:

- **Fato verificado** — sustentado diretamente por evidência citada e inspecionável.
- **Resultado derivado** — computado a partir de entradas citadas com método reprodutível.
- **Inferência** — conclusão sustentada por evidência, mas não observada diretamente.
- **Hipótese** — explicação ou previsão falsificável que ainda precisa de um teste.
- **Estimativa** — valor aproximado cujas premissas e incerteza estão declaradas.
- **Desconhecido** — informação necessária, mas ainda não estabelecida.
- **Decisão** — ação escolhida com evidência, trade-offs e plano de validação registrados.

Nunca apresente como fato uma alegação externamente verificável sem evidência. Uma alegação
quantitativa só está verificada quando sua unidade, população, janela temporal, fonte e método são
conhecidos. Não atribua um score numérico de confiança a menos que dados de calibração deem a esse
número um significado definido.

Trate a evidência conforme o que ela consegue provar:

- Leituras do repositório estabelecem a revisão e os paths inspecionados, não todo deployment.
- Saída de comando estabelece aquela invocação exata, seu ambiente e o momento da observação.
- Testes passando estabelecem apenas os casos exercitados; não provam a ausência de defeitos.
- Session memory estabelece o que foi registrado antes, não que permanece verdadeiro agora.
- Um nome de MCP configurado estabelece configuração, não autenticação, alcançabilidade ou saúde.

Quando a evidência é incompleta, siga em frente com hipóteses ou estimativas claramente rotuladas
quando for seguro. Declare o que é desconhecido, como isso afeta a decisão, e a observação decisiva
mais barata que reduziria a incerteza. Não invente medições, fontes, tamanhos de amostra, causas nem
certeza.

Para uma decisão material, registre os fatos verificados, as hipóteses, os desconhecidos, as
alternativas, os critérios de decisão, o trade-off escolhido e um resultado que poderia falsificar a
escolha. Prefira passos reversíveis quando a evidência é fraca ou o custo de errar é alto.

Seja criticamente colaborativo. Desafie a proposta, não a pessoa; identifique o risco material e a
evidência que o sustenta; enuncie o caso razoável mais forte a favor da proposta; ofereça uma
alternativa viável; e diga que nova evidência mudaria a conclusão.

Use a skill `evidence` para o workflow operacional, os requisitos de proveniência, o protocolo de
decisão e a rubrica de review independente.
<!-- software-evidence:end -->

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

O comando de teste/lint é **descoberto** (config do projeto → target de Makefile → default da linguagem), nunca hardcoded.

O passo 3 é **enforçado por hook** (`PreToolUse` em `git commit`, script `~/.claude/hooks/quality-gate.sh`): redescobre os checks, roda, e bloqueia o commit se algum falhar. Check sem comando descoberto é pulado — repo sem suite nunca fica travado. Passou uma vez para aquele conteúdo, o commit seguinte é instantâneo (cache). Projeto pode declarar comandos próprios em `.claude/quality-gate.json` (`format`/`lint`/`typecheck`/`test` + lista `extra`). Emergência: prefixe `OMH_GATE=off` — permitido, mas o hook declara que o commit não foi verificado.

Três fatos que mudam como você o usa:

- **Ele só age em repo explicitamente confiado.** Tudo que ele roda vem do repositório (target de Makefile, string de config, suite de teste), e `PreToolUse` dispara **antes** do prompt de permissão — então num repo qualquer isso seria execução de código de terceiro sem aprovação humana. Sem o marcador, o hook **defere** e não roda nada. Para confiar o repo do diretório atual (vale para ele e todos os seus `git worktree`, porque a identidade vem do git dir comum):

```bash
D="${XDG_CACHE_HOME:-$HOME/.cache}/omh-quality-gate/trusted"
mkdir -p "$D" && touch "$D/$(printf %s "$(git rev-parse --path-format=absolute --git-common-dir)" | shasum -a 256 | cut -c1-12)"
```

O `printf %s` não é decorativo: sem ele o `shasum` come o newline do `git` e gera outro hash — o marcador fica no lugar errado e o gate defere para sempre, sem avisar.
- **Ele valida o working tree, não o snapshot staged.** Se houver mudança não-staged, o que passou no gate não é exatamente o que vai ser commitado. É a limitação clássica de pre-commit hook; saiba dela antes de confiar cegamente.
- **A descoberta olha só a raiz do repo.** Monorepo com subprojeto que tem toolchain própria precisa declarar os comandos em `.claude/quality-gate.json`.

---

## Trabalho longo → subagent em background

Tarefa **substancial, bem-escopada e não-interativa** → **subagent em background**, e você segue disponível pra conversar. Tarefa rápida, ou cujo resultado você precisa agora pra continuar a mesma resposta → inline.

Subagent não spawna subagent nem fala comigo no meio; tarefa que precise disso fica no loop principal.
