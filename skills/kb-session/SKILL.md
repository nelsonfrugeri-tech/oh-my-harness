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
  embedado, cwd, transcript_path, created_at/updated_at),
  a descoberta da sessão corrente por harness (claude-code: JSONL mais recente em
  ~/.claude/projects/<cwd-munged>/), a atualização de carona em toda invocação do
  agent knowledge-base, a indexação como point vivo no Qdrant (kind: "session",
  re-upsert no mesmo point, sem supersedes) e o playbook de deep search pela capability
  `session-memory` — busca cross-harness e cross-projeto por tema, digest de sessão e
  blame por arquivo, com a disciplina de query lexical AND (poucos termos raros, não
  frases) — mais o modo degradado por grep dirigido sobre o JSONL e a destilação
  integral auditável em intervalos cronológicos quando o usuário pede transformar uma
  sessão longa em várias notas. Invocada pelo agent `knowledge-base` sob demanda ("registra a sessão",
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
de código em repo Git, resolva a raiz com `git -C <cwd> rev-parse --show-toplevel` e
normalize **o basename da raiz**, nunca o basename do `cwd`: lowercase, caracteres fora
de `[a-z0-9-]` convertidos em hífen, hífens repetidos colapsados e pontas aparadas. O
resultado é `work/projects/<project>`, exatamente a mesma derivação de `explorer`,
`kb-write` e `context-load.sh`, inclusive quando a sessão começa num subdiretório. Sem
repo Git, se a atividade for um projeto de software, reutilize o slug canônico já
registrado em `work/projects/<project>` ou aplique a única pergunta de nome e slug de
`kb-write`; nunca desvie seu session record para um domain não-projeto. Somente conteúdo
que realmente não pertence a projeto usa o domain não-projeto adequado. Não derive
silenciosamente um project do diretório corrente. Antes de `mkdir` ou de qualquer
reescrita, aplique integralmente o collision gate de `kb-write` ao domain: identidade
divergente ou insuficiente bloqueia o session record; nunca crie slug alternativo só
neste writer. `mkdir -p` somente depois de o gate passar).

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
`transcript_path`, `machine_id`, `machine_label`, `hostname` ou `username`. Eles
continuam legíveis e reindexáveis em modo legacy:

1. O reindex projeta cada campo ausente no payload Qdrant como `null` e reporta o
   record como legacy; não rejeita a reconstrução inteira.
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
  `description`, `resume` e `updated_at` do record da sessão corrente. Sem perguntar,
  sem anunciar como tarefa — é manutenção de rotina.

Mecânica da atualização: descubra a sessão corrente (seção 3), resolva a identidade da
máquina via `kb-infra`, leia o record se
existir, reescreva o JSON inteiro in-place com os campos atualizados. Se o record não
existe ainda, crie-o (`created_at` = agora). **`created_at` nunca muda** numa
atualização — só `updated_at` avança. Se o arquivo existente for legacy, siga a
promoção controlada descrita acima antes de reescrever.

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

### 4.4 Destilação integral de sessão

Deep search responde uma pergunta e para cedo; **destilar a sessão inteira** é outra
operação e só acontece por pedido explícito. Nesse modo, percorra o transcript completo
em intervalos cronológicos limitados, sem carregá-lo inteiro no contexto, e entregue os
candidatos a `kb-write`. A carona que atualiza o session record não cria notas
automaticamente.

1. Resolva o transcript real e registre tamanho em bytes, quantidade total de registros
   brutos, eventos parseáveis, parsing failures e primeiro/último timestamp. Sem
   transcript, não existe alegação de cobertura integral: reporte o modo parcial e o
   que falta.
2. Divida o corpus em intervalos cronológicos contíguos, com pequena sobreposição apenas
   nas fronteiras. Para cada intervalo, extraia decisões, eventos, procedimentos,
   referências, entidades, topics e ponteiros de evidência; ignore tool noise e
   tentativas transitórias sem valor durável.
3. Antes de registrar candidatos, detecte credentials, tokens, secrets, personal data e
   outros dados sensíveis. Redija os valores irreversivelmente no ledger e no corpus
   entregue a `kb-write`, preservando apenas categoria e contexto necessários. Nunca
   grave o valor bruto em nota, summary, link, log ou Qdrant. Se houver detecção ou
   dúvida sobre PII, apresente o plano já redigido e obtenha confirmação humana antes de
   escrever; confirmação nunca autoriza persistir um secret bruto.
4. Mantenha fora do repo, no scratchpad da sessão ou em `/tmp`, um **ledger de
   cobertura** com intervalo, offsets ou ids inicial/final, bytes, total de registros,
   status de cada registro e candidatos. Cada registro termina como conteúdo processado,
   noise excluído com motivo, parsing failure ou tipo desconhecido não classificado.
   Marque um intervalo como processado somente depois de contabilizar todos os seus
   registros; parsing failure ou registro não classificado é gap, nunca descarte.
5. Antes de sintetizar, valide que os intervalos formam uma cobertura contínua do
   primeiro ao último byte e registro, sem lacunas e sem duplicação fora das fronteiras.
   Só diga “sessão integralmente analisada” quando houver **nenhum intervalo não
   processado**, parsing failure ou registro não classificado.
6. Reúna candidatos equivalentes encontrados em intervalos diferentes, preserve todos
   os ponteiros de evidência e entregue a `kb-write` o corpus, o ledger e a janela total.
   `kb-write` decide `create | supersede | skip`, atomiza e conecta as notas.
7. O relatório final informa fonte, janela, método, bytes, população total de registros,
   eventos parseáveis, noise justificado, parsing failures, registros não classificados,
   intervalos processados, gaps, candidatos e resultado por nota. Não confunda número
   de linhas JSONL com número de mensagens sem declarar o parser usado.

Esta seção é a exceção explícita à regra de não ler transcript inteiro: a operação cobre
o corpus inteiro **por streaming e janelas**, nunca como um único prompt. A proibição
continua valendo para deep search comum.

## 5. Indexação no Qdrant — índice vivo, sem supersedes

O record é indexado na collection `knowledge-base` (desenho em `kb-infra`):

- **Texto embedado**: `name + "\n" + description + "\n" + resume` — dense + sparse via
  bge-m3, igual às notas.
- **Point ID**: o UUID do `session_id`.
- **Payload**: `kind: "session"` (notas usam `kind: "note"` — ver `kb-infra`),
  `harness`, `session_id`, `session_name`, `app_name`, `domain`, `name`, `created_at`,
  `updated_at`, `cwd`, `transcript_path`, `machine_id`, `machine_label`, `hostname` e
  `username`. Preserve os campos nullable com valor nulo.
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
4. **NUNCA carregue um transcript inteiro no contexto** — deep search degradado usa grep
   dirigido + janelas; somente a destilação integral explícita percorre todo o corpus,
   por streaming, intervalos e ledger de cobertura conforme a seção 4.4.
5. **Query lexical é AND** — 2 a 3 termos raros, não uma frase. Vazio significa "estreitei
   demais": remova termos e tente sinônimos em pt e en.
6. **Toda resposta de deep search cita a fonte** — session name + session_id + harness; e
   diga quando o trecho veio de outro projeto/cwd.
7. **Nunca escreva conhecimento curado pela capability** — o mecanismo de notas dela,
   qualquer que seja seu nome nesta máquina, é proibido; conhecimento durável é nota via
   `kb-write`.
8. **Escrita só em `~/knowledge-base/`** — nunca no repo do usuário; scripts efêmeros
   via heredoc com o venv de `kb-infra`.
9. **Harness não mapeado → degrade explícito** — record com `transcript_path: null` e
   aviso do que ficou pendente; nunca invente um caminho de transcript. Sem
   `session_id`, a escrita é recusada.
10. **Proveniência de máquina é obrigatória** — leia a identidade persistente de
    `~/.local/share/omh-kb/identity.json`; não use MAC address bruto nem gere um novo
    UUID quando o arquivo já existir.
