---
version: 1.0.0
name: kb-session
description: |
  Memória de sessão do harness — mantém um session record VIVO por sessão em
  ~/knowledge-base/{domain}/sessions/<session_id>.json (JSON reescrito in-place —
  exceção nomeada à imutabilidade das notas) e executa deep search dentro dos
  transcripts brutos do harness quando os degraus 1–2 do retrieval não respondem.
  Cobre: o schema do record (harness, session_id, domain, name, description, resume
  denso 200-800 chars — núcleo do texto embedado, transcript_path, created_at/updated_at),
  a descoberta da sessão corrente por harness (claude-code: JSONL mais recente em
  ~/.claude/projects/<cwd-munged>/), a atualização de carona em toda invocação do
  agent knowledge-base, a indexação como point vivo no Qdrant (kind: "session",
  re-upsert no mesmo point, sem supersedes) e o playbook de deep search dirigido —
  grep + leitura por janelas sobre o JSONL, nunca o arquivo inteiro. Invocada pelo
  agent `knowledge-base` sob demanda ("registra a sessão", "atualiza o resumo da
  sessão", "o que falamos naquela sessão sobre X?") ou como degrau 3 de
  `kb-retrieval` — não destinada a invocação direta pelo usuário.
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

Estrutura análoga a descobrir, guiada pela tabela **"Session memory por harness"** do
`CLAUDE.md` — é ela que mapeia onde vive a memória bruta de cada harness **nesta
máquina**. Se o harness corrente não estiver mapeado na tabela, **degrade com
elegância**: escreva o record sem `transcript_path` e diga explicitamente ao usuário o
que ficou pendente (deep search indisponível para essa sessão até o mapeamento existir).

## 4. Deep search na session memory — o coração da skill

Este é o degrau 3 da escada de retrieval (ver `kb-retrieval`): quando a busca no Qdrant
e a navegação em disco não respondem (ou respondem parcialmente), a resposta pode estar
na **memória bruta** de uma sessão passada. Você recebe a **query** e os **session
records candidatos** (vindos do Qdrant ou do disco, já ranqueados por relevância) e,
para cada candidato, faz busca **dirigida** dentro do transcript.

O playbook, por candidato:

1. **Siga o `transcript_path`** do record. Se o arquivo não existe mais (transcript
   expirado/apagado), registre isso e passe ao próximo candidato.
2. **Grep dirigido, nunca leitura integral.** Os transcripts são arquivos grandes —
   **NUNCA leia o JSONL inteiro**. Comece com `grep -n` sobre o arquivo usando os
   termos da query — e variações: sinônimos, o termo em inglês e em português, nomes de
   arquivos/sistemas relacionados. Vários greps baratos superam uma leitura cara:

   ```bash
   grep -n -i "termo-da-query" <transcript_path>
   grep -n -i -E "sinonimo1|sinonimo2|nome-do-sistema" <transcript_path>
   ```

3. **Leitura por janelas ao redor dos hits.** Com os números de linha dos hits, leia
   apenas **janelas** ao redor deles (Read com offset/limit — ex.: ~20 linhas antes e
   depois do hit) para capturar o contexto conversacional do trecho. Expanda a janela
   só se o trecho estiver truncado.
4. **Extraia o texto humano, ignore o ruído.** Cada linha do JSONL é um evento JSON da
   conversa — mensagens do usuário, respostas do assistant, tool calls e resultados.
   Extraia o **texto humano relevante** (o que foi dito/decidido/explicado); ignore
   metadata, ids de evento, payloads de tool call que não carregam a resposta.
5. **Responda com citação obrigatória.** Todo trecho recuperado é citado com
   **session name + session_id + harness** (ex.: *"na sessão 'Refactor da biblioteca
   portable' (55cb8ac6…, claude-code)"*). O leitor precisa saber de qual conversa o
   conhecimento veio.
6. **Nada encontrado?** Diga explicitamente que o deep search nos N transcripts
   candidatos não encontrou resposta — nunca preencha o vazio com invenção.

Ordem de trabalho: percorra os candidatos do mais relevante para o menos relevante e
**pare quando a query estiver respondida** — deep search é cirúrgico, não exaustivo.

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
3. **NUNCA leia um transcript inteiro** — deep search é grep dirigido + janelas por
   offset/limit ao redor dos hits.
4. **Toda resposta de deep search cita a fonte** — session name + session_id + harness.
5. **Escrita só em `~/knowledge-base/`** — nunca no repo do usuário; scripts efêmeros
   via heredoc com o venv de `kb-infra`.
6. **Harness não mapeado → degrade explícito** — record sem `transcript_path` e aviso
   do que ficou pendente; nunca invente um caminho de transcript.
