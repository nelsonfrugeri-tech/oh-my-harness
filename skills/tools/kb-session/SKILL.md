---
version: 2.0.0
name: kb-session
description: |
  Memória de sessão do harness — mantém um session record VIVO por sessão em
  ~/knowledge-base/{domain}/sessions/<session_id>.json (JSON reescrito in-place —
  exceção nomeada à imutabilidade das notas) e executa deep search na memória bruta
  de sessões quando os degraus 1–2 do retrieval não respondem.
  Cobre: o schema do record (harness, session_id, domain, name, description, resume
  denso 200-800 chars — núcleo do texto embedado, transcript_path, created_at/updated_at),
  a descoberta da sessão corrente por harness (claude-code: JSONL mais recente em
  ~/.claude/projects/<cwd-munged>/), a atualização de carona em toda invocação do
  agent knowledge-base, a indexação como point vivo no Qdrant (kind: "session",
  re-upsert no mesmo point, sem supersedes) e o playbook de deep search pela capability
  `session-memory` — busca cross-harness e cross-projeto por tema, digest de sessão e
  blame por arquivo, com a disciplina de query lexical AND (poucos termos raros, não
  frases) — mais o modo degradado por grep dirigido sobre o JSONL quando a capability
  não existe. Invocada pelo agent `knowledge-base` sob demanda ("registra a sessão",
  "atualiza o resumo da sessão", "o que falamos naquela sessão sobre X?", "que sessões
  mexeram neste arquivo?") ou como degrau 3 de `kb-retrieval` — não destinada a
  invocação direta pelo usuário.
type: capability
---

# KB Session — Memória de Sessão do Harness

Você mantém a ponte entre a knowledge base e a **memória bruta de sessão do harness**:
um *session record* por sessão, vivo e pesquisável, que aponta para o transcript bruto
onde a conversa inteira está registrada. Duas responsabilidades:

1. **Manter o session record** — um JSON vivo por sessão, criado/atualizado in-place.
2. **Deep search** — quando a knowledge base estruturada não responde, mergulhar no
   transcript bruto da sessão e extrair o trecho que responde.

---

## 1. Session record — documento VIVO (exceção nomeada à imutabilidade)

A doutrina da knowledge base diz que notas são imutáveis (`kb-write`). O session record
é uma **exceção explícita e nomeada** a essa regra — como o `context.md` do `explorer`,
ele é um **documento vivo**: um único arquivo por sessão, **reescrito in-place** a cada
atualização, sem `supersedes`, sem arquivo novo. A sessão evolui; o record evolui junto.

Um JSON por sessão em `~/knowledge-base/{domain}/sessions/<session_id>.json`
(`{domain}` = o bounded context da sessão, relativo à raiz do bundle — para uma sessão
de código, `work/projects/<basename-do-cwd-em-lowercase-kebab>`, exatamente a mesma
derivação que o `explorer` usa para o `context.md`, para que sessão e contexto do mesmo
repositório caiam no mesmo bounded context. `mkdir -p` se preciso).

> Session records são `.json`, não `.md` — ficam **fora** do conjunto de arquivos que a
> conformance do OKF avalia, e por isso podem seguir sendo documentos vivos em JSON
> dentro de um bundle conforme.

Schema:

```json
{
  "harness": "claude-code",
  "session_id": "55cb8ac6-ffb4-417c-b9af-62e513f14737",
  "domain": "work/projects/oh-my-harness",
  "name": "Refactor da biblioteca portable",
  "description": "Sessão de refactor dos assets/ para o layout agnóstico de harness, cobrindo a decisão de symlink temado e o achatamento de skills.",
  "resume": "<prosa densa de 200-800 chars — núcleo do texto embedado>",
  "transcript_path": "/Users/nelson.frugeri/.claude/projects/-Users-nelson-frugeri-projects-harness-oh-my-harness/55cb8ac6-ffb4-417c-b9af-62e513f14737.jsonl",
  "created_at": "2026-07-19T14:30:00Z",
  "updated_at": "2026-07-19T16:05:00Z"
}
```

| Campo | O que é |
|---|---|
| `harness` | String aberta identificando o harness da sessão: `"claude-code"`, `"codex"`, `"cursor"`, ... |
| `session_id` | UUID da sessão no harness — também é o nome do arquivo e o point id no Qdrant. |
| `domain` | O bounded context da sessão, relativo à raiz do bundle (mesma regra do resto da KB — ver `kb-write`). |
| `name` | Assunto curto da sessão, no estilo do auto-naming de sessões do Claude Code (ex.: "Refactor da biblioteca portable"). |
| `description` | Descrição da sessão **até aquele momento** — o que ela cobre, em 1-2 frases. |
| `resume` | Resumo denso da sessão até aquele momento — **núcleo do texto embedado** (o embedding é `name + description + resume`, ver seção 5). Aplique a mesma doutrina do summary de `kb-write`: prosa densa, específica e auto-contida de **200-800 chars**, sem bullets, nomeando sistemas, decisões e atores. É aqui que o recall da sessão é ganho ou perdido. |
| `transcript_path` | Caminho da memória bruta da sessão no harness (o transcript completo). Grave sempre o **caminho absoluto expandido** (`/Users/...`, nunca `~`) — o deep search o segue diretamente com Read/grep, que não expandem `~`. |
| `created_at` / `updated_at` | ISO 8601 UTC. `created_at` **nunca muda** depois da criação; `updated_at` muda a cada reescrita. |

## 2. Ciclo de vida — sob demanda e de carona

O record é criado/atualizado em dois gatilhos:

- **Sob demanda** — o usuário pede explicitamente: "registra a sessão", "atualiza o
  resumo da sessão", "salva onde paramos".
- **De carona** — sempre que o agent `knowledge-base` for invocado para **qualquer**
  operação (write, retrieval, infra), ele aproveita a invocação e atualiza `name`,
  `description`, `resume` e `updated_at` do record da sessão corrente. Sem perguntar,
  sem anunciar como tarefa — é manutenção de rotina.

Mecânica da atualização: descubra a sessão corrente (seção 3), leia o record se
existir, reescreva o JSON inteiro in-place com os campos atualizados. Se o record não
existe ainda, crie-o (`created_at` = agora). **`created_at` nunca muda** numa
atualização — só `updated_at` avança.

## 3. Descoberta da sessão corrente

### claude-code (nesta máquina)

Os transcripts vivem em `~/.claude/projects/<cwd-munged>/<session-uuid>.jsonl`, onde
`<cwd-munged>` é o caminho absoluto do cwd com `/` e `.` trocados por `-`:

```
/Users/nelson.frugeri/projects/harness/oh-my-harness
→ -Users-nelson-frugeri-projects-harness-oh-my-harness
```

Heurística: o `.jsonl` **modificado mais recentemente** nesse diretório é a sessão
corrente; o nome do arquivo (sem extensão) é o `session_id`:

```bash
ls -t ~/.claude/projects/<cwd-munged>/*.jsonl | head -1
```

Caveat: com **duas sessões simultâneas no mesmo cwd**, a heurística pode apontar para a
sessão errada. Se houver mais de um `.jsonl` modificado nos últimos minutos, confira o
conteúdo (as últimas linhas devem bater com a conversa corrente) antes de assumir.

### Outros harnesses

Estrutura análoga a descobrir: um diretório de sessões por projeto, um arquivo por sessão
nomeado pelo id. Se você não conseguir determinar o caminho com confiança, **degrade com
elegância**: escreva o record sem `transcript_path` e diga explicitamente ao usuário o que
ficou pendente. **Nunca invente um caminho de transcript.**

> O `transcript_path` serve ao **modo degradado** do deep search (seção 4.2) e como
> ponteiro auditável para a origem bruta da sessão. Ele **não** é pré-requisito do deep
> search: com a capability `session-memory` disponível, a busca alcança os transcripts de
> todos os harnesses da máquina independentemente do que este campo diga — inclusive de
> sessões que nunca tiveram record.

## 4. Deep search na session memory — o coração da skill

Este é o degrau 3 da escada de retrieval (ver `kb-retrieval`): quando a busca no Qdrant
e a navegação em disco não respondem (ou respondem parcialmente), a resposta pode estar
na **memória bruta** de uma sessão passada.

O deep search roda pela capability **`session-memory`** (ver `CLAUDE.md`), que indexa os
transcripts de **todos os harnesses e todos os projetos** da máquina — não só a sessão
corrente. Isso importa: a resposta com frequência está numa sessão que **nunca teve
session record**, ou num harness diferente. O caminho por `transcript_path` só alcança o
que algum record já apontou; a capability alcança o corpus inteiro.

### 4.1 Modo normal — via capability

1. **Busque por tema.** Chame a capability com os termos da query. Se ela devolver
   sessões demais, restrinja por janela temporal; se devolver nada, use a disciplina de
   query abaixo antes de desistir.
2. **Aprofunde na melhor candidata.** Com a sessão identificada, peça o **digest** dela
   para ler o contexto em volta do trecho, em vez de abrir o transcript na mão.
3. **Pergunta sobre um arquivo, não sobre um tema?** Existe uma entrada própria: a busca
   por **quais sessões tocaram um path**. Use-a quando a pergunta for "quando mexemos
   neste arquivo?", "quem escreveu isso?", "por que este trecho ficou assim?".
4. **Responda com citação obrigatória** — ver 4.3.

> **Disciplina de query — o oposto da busca semântica.** A capability é **lexical com
> semântica AND**: cada palavra a mais *estreita* o resultado, ao contrário do embedding,
> onde uma frase rica *melhora* o recall. Escreva **2 a 3 termos raros**, não uma
> pergunta. Aspas exigem a frase contígua. Se veio vazio, **remova** termos e tente
> sinônimos — em português e em inglês, porque os transcripts misturam os dois.

### 4.2 Modo degradado — sem a capability

Se `session-memory` estiver vazia na tabela de capabilities, caia no acesso direto ao
transcript. **Declare o modo degradado** e suas duas limitações: o alcance cai para as
sessões que **têm session record** e cujo transcript ainda existe — sessões sem record
ficam invisíveis; e os trechos vêm **sem redaction** (podem conter credenciais — não os
ecoe inteiros).

Candidatos = os session records ranqueados pelos degraus 1–2 de `kb-retrieval` (hits
`kind: "session"` do Qdrant, ou os JSONs achados em disco). Chegando pela **entrada
lateral por arquivo**, a escada não foi subida: monte os candidatos você mesmo, usando o
path ou o basename do arquivo como termo de busca. Por candidato, siga o
`transcript_path` do record. Se o arquivo não existe mais, registre e passe ao próximo.
Então:

1. **Grep dirigido, nunca leitura integral.** Os transcripts são arquivos grandes —
   **NUNCA leia o JSONL inteiro**. Vários greps baratos superam uma leitura cara:

   ```bash
   grep -n -i "termo-da-query" <transcript_path>
   grep -n -i -E "sinonimo1|sinonimo2|nome-do-sistema" <transcript_path>
   ```

2. **Leitura por janelas ao redor dos hits.** Com os números de linha, leia apenas
   **janelas** (Read com offset/limit — ex.: ~20 linhas antes e depois). Expanda só se o
   trecho estiver truncado.
3. **Extraia o texto humano, ignore o ruído.** Cada linha do JSONL é um evento JSON —
   mensagens, respostas, tool calls. Extraia o que foi dito/decidido/explicado; ignore
   metadata, ids de evento e payloads que não carregam a resposta.

### 4.3 Regras comuns aos dois modos

- **Citação obrigatória.** Todo trecho recuperado é citado com **session name +
  session_id + harness** (ex.: *"na sessão 'Refactor da biblioteca portable'
  (55cb8ac6…, claude-code)"*). O leitor precisa saber de qual conversa o conhecimento
  veio. Quando o trecho vier de outro projeto/cwd, **diga isso** — é informação, não
  ruído.
- **Cirúrgico, não exaustivo.** Percorra do mais relevante ao menos relevante e **pare
  quando a query estiver respondida**.
- **Nada encontrado?** Diga explicitamente que o deep search não encontrou resposta —
  nunca preencha o vazio com invenção.
- **Transcript é evidência, não conhecimento.** Se o trecho recuperado revela algo que
  merece virar conhecimento durável, isso é uma nota via `kb-write` — nunca pelo
  **mecanismo de escrita/notas da própria capability**, qualquer que seja o nome dele
  nesta máquina (ver `CLAUDE.md`: um único escritor de conhecimento curado).

## 5. Indexação no Qdrant — índice vivo, sem supersedes

O record é indexado na collection `knowledge-base` (desenho em `kb-infra`):

- **Texto embedado**: `name + "\n" + description + "\n" + resume` — dense + sparse via
  bge-m3, igual às notas.
- **Point ID**: o UUID do `session_id`.
- **Payload**: `kind: "session"` (notas usam `kind: "note"` — ver `kb-infra`),
  `harness`, `session_id`, `domain`, `name`, `created_at`, `updated_at`,
  `transcript_path`.
- **Re-upsert no mesmo point a cada atualização** — documento vivo → índice vivo. Sem
  `supersedes`, sem `archived`: o point é sempre o estado corrente da sessão.

Degrade sem Qdrant: o JSON em disco é escrito mesmo assim e a indexação fica
**pendente** — informe explicitamente; o reindex de `kb-infra` reconcilia depois.

## Regras de execução

1. **Session record é documento VIVO** — reescrita in-place, exceção nomeada à
   imutabilidade das notas; `created_at` nunca muda, `updated_at` sempre avança.
2. **`resume` segue a doutrina do summary denso** — 200-800 chars, prosa sem bullets,
   específica e auto-contida; é o contrato de recall da sessão.
3. **Deep search pela capability `session-memory`** — é ela que alcança outros harnesses e
   sessões sem record, e é ela que devolve trechos já **tarjados** (redaction aplicada).
   Acesso direto ao JSONL é o modo degradado, declarado como tal.
4. **NUNCA leia um transcript inteiro** — no modo degradado, deep search é grep dirigido +
   janelas por offset/limit ao redor dos hits.
5. **Query lexical é AND** — 2 a 3 termos raros, não uma frase. Vazio significa "estreitei
   demais": remova termos e tente sinônimos em pt e en.
6. **Toda resposta de deep search cita a fonte** — session name + session_id + harness; e
   diga quando o trecho veio de outro projeto/cwd.
7. **Nunca escreva conhecimento curado pela capability** — o mecanismo de notas dela,
   qualquer que seja seu nome nesta máquina, é proibido; conhecimento durável é nota via
   `kb-write`.
8. **Escrita só em `~/knowledge-base/`** — nunca no repo do usuário; scripts efêmeros
   via heredoc com o venv de `kb-infra`.
9. **Harness não mapeado → degrade explícito** — record sem `transcript_path` e aviso
   do que ficou pendente; nunca invente um caminho de transcript.
