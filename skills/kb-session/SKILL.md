---
version: 3.1.0
name: kb-session
description: |
  Memória de sessão do harness — mantém um session record VIVO por sessão em
  ~/knowledge-base/{domain}/sessions/<session_id>.json (JSON reescrito in-place —
  exceção nomeada à imutabilidade das notas) e executa deep search na memória bruta
  de sessões quando os degraus 1–2 do retrieval não respondem.
  Cobre: o schema do record (harness, session_id, session_name, app_name, machine
  identity, domain, name, description, resume denso 200-800 chars — núcleo do texto
  embedado, entidades, aliases, referências, fatos temporais, cwd, transcript_path e
  created_at/updated_at),
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
  "session_name": "refactor-da-biblioteca-portable",
  "app_name": "Claude Code",
  "domain": "work/projects/oh-my-harness",
  "name": "Refactor da biblioteca portable",
  "description": "Sessão de refactor dos assets/ para o layout agnóstico de harness, cobrindo a decisão de symlink temado e o achatamento de skills.",
  "resume": "<prosa densa de 200-800 chars — núcleo do texto embedado>",
  "entities": ["oh-my-harness", "GitHub"],
  "aliases": ["OMH"],
  "entity_refs": [
    {"kind": "project", "name": "oh-my-harness", "aliases": ["OMH"]}
  ],
  "references": [
    {
      "kind": "repository-url",
      "label": "oh-my-harness repository",
      "target": "https://github.com/example/oh-my-harness",
      "entity": "oh-my-harness",
      "status": "observed"
    }
  ],
  "temporal_refs": [
    {"value": "2026-07-31", "timezone": "unknown", "meaning": "release deadline"}
  ],
  "cwd": "/Users/nelson.frugeri/projects/harness/oh-my-harness",
  "transcript_path": "/Users/nelson.frugeri/.claude/projects/-Users-nelson-frugeri-projects-harness-oh-my-harness/55cb8ac6-ffb4-417c-b9af-62e513f14737.jsonl",
  "machine_id": "49d7a0f0-4f0d-4ea0-8987-0f442fab9130",
  "machine_label": "m4",
  "hostname": "MacBook-Pro-de-Nelson",
  "username": "nelson.frugeri",
  "created_at": "2026-07-19T14:30:00Z",
  "updated_at": "2026-07-19T16:05:00Z"
}
```

| Campo | O que é |
|---|---|
| `harness` | String aberta identificando o harness da sessão: `"claude-code"`, `"codex"`, `"cursor"`, ... |
| `session_id` | UUID da sessão no harness — também é o nome do arquivo e o point id no Qdrant. |
| `session_name` | Nome atribuído pelo próprio harness, ou `null` quando a sessão não tem nome registrado. Não confundir com `name`, que é o assunto curado do record. |
| `app_name` | Nome do app registrado pela sessão, ou `null` quando o harness não expõe esse dado. |
| `domain` | O bounded context da sessão, relativo à raiz do bundle (mesma regra do resto da KB — ver `kb-write`). |
| `name` | Assunto curto da sessão, no estilo do auto-naming de sessões do Claude Code (ex.: "Refactor da biblioteca portable"). |
| `description` | Descrição da sessão **até aquele momento** — o que ela cobre, em 1-2 frases. |
| `resume` | Resumo denso da sessão até aquele momento — **núcleo do texto embedado** (o embedding é `name + description + resume`, ver seção 5). Aplique a mesma doutrina do summary de `kb-write`: prosa densa, específica e auto-contida de **200-800 chars**, sem bullets, nomeando sistemas, decisões e atores. É aqui que o recall da sessão é ganho ou perdido. |
| `entities` / `aliases` | Nomes canônicos materiais e aliases observados; nunca substituir o nome canônico pelo alias. |
| `entity_refs` | Entidades estruturadas por `kind + name`, seguindo o entity completeness gate de `kb-write`. |
| `references` | URLs e paths materiais, seguros e tipados; nunca credentials, tokens ou signed URLs. |
| `temporal_refs` | Datas, horas e intervalos materiais normalizados, preservando timezone ou `unknown`. |
| `cwd` | Diretório de trabalho absoluto observado na sessão (`/Users/...`, nunca `~` nem path relativo). |
| `transcript_path` | Caminho absoluto da memória bruta da sessão no harness, ou `null` no modo degradado. |
| `machine_id` / `machine_label` | Identidade estável e nome operacional lidos de `~/.local/share/omh-kb/identity.json`. |
| `hostname` / `username` | Valores observados na máquina no momento da atualização do record. |
| `created_at` / `updated_at` | ISO 8601 UTC. `created_at` **nunca muda** depois da criação; `updated_at` muda a cada reescrita. |

`harness`, `session_id`, `cwd`, `machine_id`, `machine_label`, `hostname` e `username`
são obrigatórios e não nulos. `session_name`, `app_name` e `transcript_path` são
nullable, mas os campos existem no schema mesmo quando o valor é `null`. Nunca omita
nem invente metadata para esconder ausência. Se um campo não nullable não puder ser
resolvido, estiver vazio ou contiver apenas whitespace, não escreva nem atualize o
record; informe o campo ausente. `cwd` e todo path não nulo devem ser absolutos.

### Compatibilidade com session records anteriores ao schema v3

Session records históricos podem não conter `session_name`, `app_name`, `cwd`,
`transcript_path`, `machine_id`, `machine_label`, `hostname`, `username`,
`entities`, `aliases`, `entity_refs`, `references` ou `temporal_refs`. Eles
continuam legíveis e reindexáveis em modo legacy, nunca inferidos nem escritos de volta:

1. O reindex projeta campos multivalorados ausentes como `[]`: `entities`,
   `aliases`, `entity_kinds`, `entity_keys`, `reference_targets` e
   `temporal_values`. Projeta campos escalares nullable ausentes como `null`:
   `session_name`, `app_name`, `transcript_path`. `entity_refs`, `references`
   e `temporal_refs` são campos estruturados disk-only e não entram no payload.
   Reporta o record como legacy sem rejeitar a reconstrução inteira.
2. O reindex nunca reescreve o JSON histórico e nunca atribui a máquina atual a uma
   sessão passada.
3. Ao atualizar o record da **sessão corrente**, promova-o ao schema v3 somente com
   valores observados nessa atualização. Preserve `created_at`; grave os campos
   nullable como `null` quando o harness não os expõe.
4. Se qualquer campo obrigatório não puder ser observado na atualização corrente,
   aplique o gate fail-closed: preserve o record legacy sem alteração e informe o
   campo pendente. Nunca fabrique provenance para concluir a promoção.

## 2. Ciclo de vida — sob demanda e de carona

O record é criado/atualizado em dois gatilhos:

- **Sob demanda** — o usuário pede explicitamente: "registra a sessão", "atualiza o
  resumo da sessão", "salva onde paramos".
- **De carona** — sempre que o agent `knowledge-base` for invocado para **qualquer**
  operação (write, retrieval, infra), ele aproveita a invocação e atualiza `name`,
  `description`, `resume`, `entities`, `aliases`, `entity_refs`, `references`,
  `temporal_refs` e `updated_at` do record da sessão corrente. Sem perguntar,
  sem anunciar como tarefa — é manutenção de rotina.

Mecânica da atualização: descubra a sessão corrente (seção 3), resolva a identidade da
máquina via `kb-infra`, leia o record se existir e reescreva o JSON inteiro in-place.
A omissão no turno atual não apaga um item anterior. Use uma chave específica por campo:

- `entity_refs`: `kind + nome canônico normalizado`; una aliases observados, preservando
  a primeira grafia canônica;
- `references`: `kind + target normalizado + entity`; normalize somente whitespace,
  scheme e host, sem casefold de path ou outro componente case-sensitive;
- `temporal_refs`: `value + timezone + meaning`; `created_at` e `updated_at` já
  representam o ciclo do record e não entram nessa coleção.

Após o merge, derive novamente todos os campos flat (`entities`, `aliases`,
`entity_kinds`, `entity_keys`, `reference_targets`, `temporal_values`) a partir
das estruturas mescladas. Remova um item somente após correção explícita ou evidência de
falso positivo. Se o record não existe, crie-o (`created_at` = agora).
**`created_at` nunca muda** numa atualização — só `updated_at` avança. Se o arquivo
existente for legacy, siga a promoção controlada descrita acima antes de reescrever.

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
elegância**: escreva `transcript_path: null` e diga explicitamente ao usuário o que
ficou pendente. **Nunca invente um caminho de transcript.** A ausência de `session_id`
não é degradável porque ele identifica tanto o arquivo quanto o point; nesse caso,
recuse a escrita até resolver a sessão correta.

> O `transcript_path` serve ao **modo degradado** do deep search (seção 4.2) e como
> ponteiro auditável para a origem bruta da sessão. Ele **não** é pré-requisito do deep
> search: com a capability `session-memory` disponível, a busca alcança os transcripts de
> todos os harnesses da máquina independentemente do que este campo diga — inclusive de
> sessões que nunca tiveram record.

## 4. Deep search na session memory — o coração da skill

Este é o degrau 3 da escada de retrieval (ver `kb-retrieval`): quando a busca no Qdrant
e a navegação em disco não respondem (ou respondem parcialmente), a resposta pode estar
na **memória bruta** de uma sessão passada.

O deep search roda pela capability **`session-memory`**, que indexa os transcripts de **todos
os harnesses e todos os projetos** da máquina — não só a sessão corrente. Isso importa: a
resposta com frequência está numa sessão que **nunca teve session record**, ou num harness
diferente. O caminho por `transcript_path` só alcança o que algum record já apontou; a
capability alcança o corpus inteiro.

> **Requisito de ambiente:** a capability precisa de `DEJA_INCLUDE_SUBAGENTS=1` exportado num
> lugar que valha para shell não-interativo (`~/.zshenv`). Sem isso o índice pula os transcripts
> de subagent — a maior parte do corpus recuperável num harness que delega — e o deep search
> devolve pouco sem sinalizar que está cego. Se um recall vier suspeito de vazio, cheque a
> variável antes de concluir que o assunto nunca foi discutido.

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
  `harness`, `session_id`, `session_name`, `app_name`, `domain`, `name`, `created_at`,
  `updated_at`, `entities`, `aliases`, `entity_kinds`, `entity_keys`,
  `reference_targets`, `temporal_values`, `cwd`, `transcript_path`, `machine_id`,
  `machine_label`, `hostname` e `username`. Os campos flat são derivados de
  `entity_refs`, `references` e `temporal_refs`; preserve os nullable com valor nulo.
- **Re-upsert no mesmo point a cada atualização** — documento vivo → índice vivo. Sem
  `supersedes`, sem `archived`: o point é sempre o estado corrente da sessão.

Degrade sem Qdrant: o JSON em disco é escrito mesmo assim e a indexação fica
**pendente** — informe explicitamente; o reindex de `kb-infra` reconcilia depois.

## Regras de execução

1. **Session record é documento VIVO** — reescrita in-place, exceção nomeada à
   imutabilidade das notas; `created_at` nunca muda, `updated_at` sempre avança.
2. **Entity completeness gate também vale na carona** — preserve e mescle nomes
   canônicos, aliases, referências e fatos temporais materiais; nunca apague por omissão
   do turno atual nem invente dados ausentes.
3. **`resume` segue a doutrina do summary denso** — 200-800 chars, prosa sem bullets,
   específica e auto-contida; é o contrato de recall da sessão.
4. **Deep search pela capability `session-memory`** — é ela que alcança outros harnesses e
   sessões sem record, e é ela que devolve trechos já **tarjados** (redaction aplicada).
   Acesso direto ao JSONL é o modo degradado, declarado como tal.
5. **NUNCA leia um transcript inteiro** — no modo degradado, deep search é grep dirigido +
   janelas por offset/limit ao redor dos hits.
6. **Query lexical é AND** — 2 a 3 termos raros, não uma frase. Vazio significa "estreitei
   demais": remova termos e tente sinônimos em pt e en.
7. **Toda resposta de deep search cita a fonte** — session name + session_id + harness; e
   diga quando o trecho veio de outro projeto/cwd.
8. **Nunca escreva conhecimento curado pela capability** — o mecanismo de notas dela,
   qualquer que seja seu nome nesta máquina, é proibido; conhecimento durável é nota via
   `kb-write`.
9. **Escrita só em `~/knowledge-base/`** — nunca no repo do usuário; scripts efêmeros
   via heredoc com o venv de `kb-infra`.
10. **Harness não mapeado → degrade explícito** — record com `transcript_path: null` e
   aviso do que ficou pendente; nunca invente um caminho de transcript. Sem
   `session_id`, a escrita é recusada.
11. **Proveniência de máquina é obrigatória** — leia a identidade persistente de
    `~/.local/share/omh-kb/identity.json`; não use MAC address bruto nem gere um novo
    UUID quando o arquivo já existir.
