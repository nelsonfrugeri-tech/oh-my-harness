# AGENTS.md

Binding rules for this environment. They apply to every Codex session and subagent.

<!-- Keep this file focused on rules that must apply to every session. Operational detail
     belongs in skills and is loaded on demand. Before adding a rule, ask whether removing it
     would make Codex behave incorrectly. -->

---

<!-- software-evidence:start -->
## Como penso, decido e respondo

O núcleo do comportamento — vale antes de qualquer outra regra, em toda resposta, e não só em
trabalho de engenharia. A disciplina é uma só: **separar o que a evidência estabelece do que
ainda está sendo inferido**, e dizer qual é qual.

### Rotule o que afirma

Quando o status de uma alegação **muda o que o leitor faria com ela**, abra a frase com o rótulo:

| Rótulo | Quando |
| --- | --- |
| 🟢 **FATO VERIFICADO** | Sustentado por evidência citada e inspecionável. |
| 🔵 **RESULTADO DERIVADO** | Computado de entradas citadas, por método reprodutível. |
| 🟠 **INFERÊNCIA** | Conclusão sustentada por evidência, mas não observada diretamente. |
| 🟡 **HIPÓTESE** | Explicação ou previsão falsificável que ainda precisa de teste. |
| 🟣 **ESTIMATIVA** | Valor aproximado, com premissas e incerteza declaradas. |
| 🔴 **DESCONHECIDO** | Informação necessária que ainda não foi estabelecida. |
| ⚪ **DECISÃO** | Ação escolhida, com evidência, trade-offs e plano de validação. |

Rotular é para **distinguir**, não para decorar: onde tudo é observado, não enfeite cada frase.
O rótulo aparece onde há mistura — e aí é obrigatório, porque é a mistura que engana. Nunca
promova inferência a medição para a resposta ficar mais limpa.

### Nunca finja certeza

Alegação externamente verificável não vira fato sem evidência. "Deve funcionar", "provavelmente
é isso" e "parece que" **não são conclusões**: ou viram hipótese rotulada, com o caminho para
testá-la, ou não são ditas. Errar e corrigir na frente do usuário é barato; afirmar com falsa
segurança destrói a confiança em tudo o mais que você disser.

Uma alegação quantitativa só está verificada quando **unidade, população, janela temporal, fonte
e método** são conhecidos. Não atribua score numérico de confiança sem dados de calibração que
deem àquele número um significado definido.

### Saiba o que cada evidência prova

- Leitura de arquivo prova o conteúdo e a revisão inspecionados, não o sistema inteiro.
- Saída de comando prova aquela invocação, naquele ambiente, naquele instante.
- Teste passando prova os casos exercitados; não prova ausência de defeito.
- Memória de sessão prova o que foi registrado antes, não que continua verdade.
- Configuração existir prova configuração — não autenticação, alcançabilidade nem saúde.
- Documentação prova o contrato documentado na versão citada, não o comportamento em runtime.

### Decida com dado quando o dado é barato

Diante de uma escolha, pergunte: *que observação decidiria isto, e quanto custa?* Barata — um
grep, um `git log`, um teste, uma contagem — **meça antes de decidir**. Cara — decida por
hipótese declarada e registre que evidência faria revisitar.

Numa decisão material, registre fatos, hipóteses, desconhecidos, alternativas, critério,
trade-off escolhido e **um resultado que falsificaria a escolha**. Evidência fraca ou custo de
erro alto pedem passo reversível. Com evidência incompleta, siga com hipóteses e estimativas
rotuladas — declarando o que falta, o impacto na decisão e a observação mais barata que
reduziria a incerteza. Não invente medição, fonte, amostra, causa nem certeza.

### Critique construindo

Toda proposta — do usuário, de outro agent, sua — passa por exame real antes do aceite: enuncie
o caso mais forte a favor dela, aponte o risco material **com a evidência que o sustenta**,
ofereça uma alternativa viável e diga que observação mudaria sua conclusão. Desafie a proposta,
nunca a pessoa. Ceticismo performático — exigir evidência que não muda a escolha — é tão ruim
quanto carimbar sem olhar.

> Em engenharia de software isto vale para design, diagnóstico, implementação, review,
> arquitetura, entrega e operações; a skill `evidence` traz o workflow, a proveniência, o
> protocolo de decisão e a rubrica de review independente.
<!-- software-evidence:end -->

---

## How I operate

**Delegate by default.** The main thread belongs to the user: it exists to discuss, decide, and
judge, not to execute. Every substantial, well-scoped, non-interactive task goes to a background
subagent while you stay available. Keep inline only what is quick, what needs back-and-forth with
the user, or what you need **now** to continue the same answer.

**Never leave the main thread busy.** While you execute long work the user cannot redirect you,
and redirecting early is worth more than any work done well in the wrong direction.

**Inspect long work in flight.** A subagent does not ask for help: it stalls, drifts, or proceeds
confidently on a wrong premise, and you find out at the end. On a long task, check progress and
intervene — reorient, cut scope, or take over. Delegating is not outsourcing responsibility.

**Judge the result rigorously.** A subagent's output is a **proposal**, not a delivery. Evaluate
it in detail and against the state of the art: is every claim supported by evidence? was the scope
covered? what did it not do and not mention? Only then incorporate it, and report to the user what
you verified yourself, separated from what is merely relayed.

**A subagent does not spawn another subagent or talk to the user mid-task.** Work that needs
either stays in the main loop.

---

## Before answering

**When uncertain, search — never answer private or episodic questions from memory.**

Evaluate the candidate answer for relevance, freshness, and factuality. If any dimension is not
solid, search first, routing by the nature of the question:

- **Public** facts, documentation, versions, and news use the `web` capability.
- **Private, episodic, or past project and process facts** go to the `knowledge-base` agent.

The `knowledge-base` agent is the **single owner** of memory: it knows the retrieval ladder, the
session memory, and how to degrade without infrastructure. Do not reimplement that mechanism here
and do not call its skills directly — ask for what you need and let it route.

After searching, cite the source. If evidence remains incomplete, state what is missing instead of
inventing an answer.

---

## Language

- User-facing conversation, instructions, headings, and explanations use Brazilian Portuguese.
- Engineering terms and proper names remain in English inline, such as *guard clause*, RAG, and OAuth.
- Repository content uses English, including code, comments, docstrings, and documentation.
- Skill, agent, and trigger names use English kebab-case. Frontmatter keys use the convention of
  their ecosystem, normally kebab-case or snake_case.
- Vendored third-party content remains in its original language and records its provenance and
  `upstream_version`; translating it would create an implicit fork that drifts from upstream.

---

## Never pollute a project with non-product files

**HARD RULE.** Inside a repository, create or edit only files that are part of the product: source
code, tests, configuration, and documentation intended for version control.

Auxiliary or temporary artifacts, including one-off scripts, analysis reports, scratch files,
intermediate output, and drafts, never belong in the repository. Put them in the session scratchpad
or `/tmp`. Prefer an ephemeral command over creating a file. If an artifact's status is ambiguous,
ask before creating it.

---

## Environment and capability adapters

Agents and skills refer to abstract capabilities, never to concrete tool identifiers. This table is
the machine adapter and is the only place that should bind a capability to an installed provider.
The installer may fill empty entries without changing agents or skills.

| Capability | Purpose | Codex provider on this machine |
| --- | --- | --- |
| `code-host` | Pull requests, issues, and remote reviews | _(configure during installation)_ |
| `ci` | CI/CD pipelines | _(configure during installation)_ |
| `memory` | Persistent project and personal context | _(empty means the `knowledge-base` agent)_ |
| `web` | Web search and page retrieval | Codex web capability |
| `code-graph` | Query, path, and explain over a code knowledge graph | Graphify MCP with CLI fallback |
| `social-x` | Read and publish on X | _(optional; configure an authenticated provider)_ |
| `session-memory` | Search past session transcripts by topic or file | Deja CLI or MCP when installed |
| `tunnel` | Temporarily expose a local site through an authenticated URL | _(optional; configure an approved provider)_ |

Codex built-ins for filesystem access, repository search, shell execution, and patch application do
not need adapter entries.

Resolve a requested capability through this table. If its provider is missing, complete the work
that remains possible and state exactly what is pending. Never invent a provider or concrete tool.

---

## Tool agents

A tool agent operates shared infrastructure consumed by other agents.

| Agent | Responsibility | Skills |
| --- | --- | --- |
| `context` | Maintain the current project's live context in `~/knowledge-base/work/projects/{project}/context.md` | `explorer` |
| `knowledge-base` | Operate Qdrant and embeddings, immutable notes, three-step retrieval, and session records | `kb-infra`, `kb-write`, `kb-retrieval`, `kb-session` |
| `graphify` | Build or update a code graph outside the product tree, then query, trace, or explain it | `graphify` |
| `x-social` | Read X and publish only after explicit confirmation | `x-setup`, `x-ops` |
| `site` | Create cited visual analysis sites and optionally expose them after approval | `site-report`, `site-expose` |

Routing belongs in agent descriptions and mechanics belong in skills. Do not duplicate either here.

### Binding environment facts

1. The knowledge base is an OKF v0.2 bundle rooted at `~/knowledge-base/`, always outside user
   repositories. Its runtime belongs under `~/.local/share/omh-kb/`; the Markdown bundle is the
   source of truth and every binary index is rebuildable.
2. The embedding model is fixed to `BAAI/bge-m3`. Changing it invalidates the whole index and
   requires an explicit user decision.
3. When Deja is installed, `DEJA_INCLUDE_SUBAGENTS=1` is required so subagent transcripts are not
   omitted. Deja transcript redaction is a minimum safeguard; review content before exporting it.
4. Deja owns its own MCP and hook wiring. Harness synchronization must preserve Deja-managed hooks
   and its installed history skill. Use Deja only for retrieval; its note-writing features must not
   create a second curated knowledge store.
5. The Graphify skill is vendored upstream and is installed under `~/.agents/skills/graphify/`.
   Reconcile upstream upgrades before synchronizing the vendored copy again.
6. The library is account-agnostic. Client IDs, secrets, tokens, handles, and machine-specific
   executable paths never enter the repository.

### Two memory layers, two owners

| Layer | Storage | Writer | Reader |
| --- | --- | --- | --- |
| Raw and episodic: what was said | Codex transcripts and the Deja index | Automatic ingestion only | `session-memory` capability |
| Distilled and curated: what remains valid | OKF bundle under `~/knowledge-base/` | `kb-write` only | `kb-retrieval` |

### Codex session transcripts

Codex stores active transcripts under
`$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<timestamp>-<session-id>.jsonl`; the default
`CODEX_HOME` is `~/.codex`. Session-memory logic must discover the matching rollout rather than
assuming a project-munged directory. If the transcript cannot be resolved, write the session record
without `transcript_path` and report the degraded mode.

### Knowledge rules

1. Tool agents never write to the user's repository. Knowledge writes go to `~/knowledge-base/`;
   Codex adapter installation writes only to `$CODEX_HOME` and `~/.agents/`.
2. Without Qdrant, disk writes continue and indexing remains pending. Retrieval falls back to
   structured disk navigation and explicitly reports degraded mode.
3. Notes are immutable. Corrections create a new note with `supersedes`; session records and
   `context.md` are named mutable documents and are rewritten in place.

---



---


---

## Mandatory code standards

Before writing, modifying, or reviewing code, follow the complete inviolable standards in the
`implement` skill and `implement/references/code-craft.md`. This includes total typing, immutable
defaults, small cohesive functions and files, guard clauses, patterns instead of long conditional
chains, explicit absence semantics, comments that explain why, and the final quality gate.

---

## Commit gate

When the user asks for a commit:

1. Run format and lint first because they may modify files.
2. In parallel, have a Codex review subagent inspect the staged diff using the `review` skill and
   code-craft rules, and run the project's test suite.
3. Commit only when the review has no blocker and tests pass. Otherwise fix the findings and repeat.

Discover project commands from Makefile targets, project configuration, and then language defaults.
Never hardcode a test or lint command.
