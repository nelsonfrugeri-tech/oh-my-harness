---
version: 3.1.0
name: kb-write
description: |
  O scribe da knowledge base — playbook de julgamento e mecânica para registrar
  conhecimento como notas imutáveis em bundles conformes ao Open Knowledge Format
  (OKF v0.2): markdown com YAML frontmatter em ~/knowledge-base/, indexado no Qdrant
  (summary → dense+sparse via BAAI/bge-m3). Cobre: onde a nota mora (bounded context +
  pasta por tipo de entidade, no espírito do DDD), os dois eixos de classificação
  (`type` = o substantivo do domínio, exigido pelo OKF; `knowledge_type` = o enum
  fechado decision | event | procedure | reference | conversation, que diz como o
  conhecimento foi obtido), quando criar vs. superseder (nota é conhecimento imutável
  num ponto do tempo — nunca editar in-place), como escrever o summary denso de 200-800
  chars que decide o recall, entity completeness gate para nomes canônicos, aliases,
  referências e fatos temporais, extração de entities e tags, relacionamentos como links
  markdown no corpo (não como campo estruturado), proveniência de agent, harness,
  sessão e máquina, sinais linguísticos do usuário para supersede, e quando NÃO
  escrever.
  Invocada pelo agent `knowledge-base` quando a intenção é registrar conhecimento.
type: capability
---

# KB Write — o Scribe

Esta skill diz **onde a nota mora** e **como preencher seus campos**. A mecânica (nome
de arquivo, indexação) está na seção final; o resto é **julgamento**: em que domínio
registrar, qual entidade a nota descreve, como escrever um summary que recupera bem, e
com o que ela se relaciona.

O corpo de toda nota segue o template em
[`references/note-template.md`](references/note-template.md).

---

## 1. Onde a nota mora — bounded context e tipo de entidade

A knowledge base inteira é **um bundle OKF**: uma árvore de markdown enraizada em
`~/knowledge-base/`. A árvore não é acúmulo — ela é uma **ontologia deliberada**,
desenhada no espírito do DDD.

Duas camadas, e só duas:

```
~/knowledge-base/                    # raiz do bundle (index.md declara okf_version)
  person/                            # bounded context: vida pessoal
    people/  finances/  health/  ideas/
  work/
    ifood/                           # bounded context: a empresa
      systems/  teams/  people/  rituals/  metrics/  decisions/
    projects/
      oh-my-harness/                 # bounded context: um repositório
        context.md  log.md
        decisions/  procedures/  components/
```

| Camada | O que é | Como nomear |
|---|---|---|
| **Bounded context** | A fronteira onde uma palavra tem um significado só. `people/` dentro de `ifood/` são colegas; dentro de `person/` são amigos e família — entidades diferentes, contextos diferentes. | Caminho relativo à raiz do bundle. É o valor do campo `domain`. |
| **Tipo de entidade** | A pasta imediatamente acima da nota. É o **substantivo do domínio** no plural: `systems/`, `decisions/`, `people/`. Casa com o valor de `type` no singular. | Plural, lowercase-kebab, inglês. |

**Relacionamento nunca vira pasta.** A hierarquia expressa *pertencimento*; tudo o mais
(depende-de, causou, substitui, opera) é **link markdown no corpo** — é ali que mora o
grafo de verdade, mais rico que a árvore de diretórios.

Duas regras duras contra a taxonomia que mata a captura:

1. **Uma pasta nasce quando aparece a segunda nota daquele tipo.** Nunca crie pasta
   especulativamente — uma nota solta na raiz do contexto é preferível a vinte pastas
   vazias.
2. **Máximo 3 níveis dentro de um bounded context.** Se você precisou de um quarto, o
   que falta é link, não pasta.

Na dúvida sobre em que contexto a nota entra, pergunte ao usuário uma vez. Contexto
errado é o único erro caro aqui — os demais campos se corrigem com uma nota nova.

## 2. Os dois eixos de classificação

Toda nota responde **duas** perguntas diferentes, e por muito tempo respondemos só uma:

| Campo | Pergunta | Valores |
|---|---|---|
| `type` | **Sobre o que isso é?** — o substantivo do domínio | String livre, casada com a pasta no singular: `system`, `person`, `team`, `ritual`, `metric`, `component`, `decision`... Exigido pelo OKF. |
| `knowledge_type` | **Como eu sei disso?** — a natureza epistêmica | Enum **fechado**: `decision \| event \| procedure \| reference \| conversation`. Extensão nossa. |

O OKF deixa `type` livre de propósito. Nós **restringimos por convenção**: o valor tem
que ser o singular da pasta que contém a nota. Isso mantém o vocabulário ubíquo e o
filtro por tipo utilizável — liberdade sem entropia.

### Escolhendo o `knowledge_type`

Escolha a natureza **dominante**; não misture.

- **decision** — uma escolha feita entre alternativas, com uma justificativa. A
  palavra-chave é "decidimos X porque Y". Se não houver Y, provavelmente é `reference`.
- **event** — algo que aconteceu, com data. Incidentes, releases, lançamentos,
  reuniões. "Em 2026-05-30 o pipeline de embedding ficou fora do ar."
- **procedure** — passo a passo de "como fazer X". Reproduzível. Se um leitor futuro
  vai executar estes passos, é um procedimento.
- **reference** — um fato, uma definição, uma restrição permanente. Conhecimento de
  fundo estável. "O vetor denso do bge-m3 tem 1024 dimensões."
- **conversation** — uma troca notável cujo resultado é o significado. Use com
  parcimônia; se a conversa produziu uma decisão, escreva a decisão.

**Natureza mista?** Escolha aquilo sobre o que a nota é *principalmente*. Se uma decisão
foi tomada durante um incidente, são duas notas: um `event` para o incidente, um
`decision` para o que foi decidido — linkadas entre si.

## 3. Criar uma nota nova vs. superseder

Uma nota é **conhecimento imutável num ponto no tempo**. Nunca edite uma nota
existente; escreva uma nota nova e defina `supersedes` com o id da nota substituída.

| Situação | O que fazer |
|---|---|
| Registrar algo novo (uma decisão que acabamos de tomar, um evento que acabou de acontecer, um procedimento que acabou de ser definido) | **Criar** — nota nova com `supersedes: null`. |
| O usuário pede explicitamente para **revisar**, **atualizar**, **corrigir** ou **substituir** uma nota existente | **Superseder** — busque a nota anterior via `kb-retrieval`, escreva a nova com `supersedes: <id-anterior>` e marque a antiga com `status: deprecated`. A nova traz o conteúdo atualizado; a antiga permanece arquivada no histórico. |
| O usuário está fazendo uma pergunta ou explorando — nenhum conhecimento novo está sendo registrado | **Não escreva.** Escrever é *registrar* conhecimento, não conversar. |

Sinais do usuário que significam "superseder": "atualiza", "corrige", "revisa",
"agora ficou assim", "muda para", "a partir de hoje X em vez de Y".

> O OKF tem `status: deprecated`, mas ele não diz **quem** substituiu a nota. Por isso
> mantemos `supersedes` como extensão: os dois campos andam juntos numa supersessão —
> `status` para o consumidor OKF genérico, `supersedes` para a cadeia navegável.

> **A única mutação permitida numa nota existente** é virar o `status` dela para
> `deprecated` no frontmatter, durante um supersede — venha de `stable` ou de `draft`.
> Título, corpo, summary e
> todos os demais campos permanecem imutáveis. Essa exceção existe porque o degrau 2 do
> retrieval (navegação em disco, sem Qdrant) não tem outro jeito de distinguir
> conhecimento vigente de arquivado — sem ela, uma KB sem índice serviria decisões
> revogadas como se fossem atuais.

> **Fronteira**: *session records* (os JSONs de `sessions/`) **não são notas** — são
> documentos vivos mantidos pela skill `kb-session`, reescritos in-place por definição,
> e por serem `.json` ficam fora do conjunto de arquivos que o OKF avalia. A
> imutabilidade e o `supersedes` desta skill valem **apenas para notas**.

Se não tiver certeza entre "isso corrige uma nota existente" e "isso é algo novo",
pergunte ao usuário uma vez. Não adivinhe.

## 4. Escrevendo o `summary` — aqui o recall é ganho ou perdido

O `summary` é o texto que será embedado (dense + sparse via bge-m3) para busca por
similaridade. Ele **não** é um rótulo. É uma **prosa densa, específica e auto-contida**
— um único parágrafo (**200–800 chars**) que outro agent poderia ler isoladamente e
entender do que a nota trata e por que é relevante.

> Não confunda com o `description` do OKF, que é **uma frase** de vitrine, lida por
> consumidores genéricos ao listar o bundle. Os dois convivem: `description` é a
> etiqueta, `summary` é o contrato de recall. Nunca faça um ser cópia do outro.

**Regras**:

1. Não repita o título. O summary deve dizer algo que o título não diz.
2. Não escreva rótulos formulaicos ("Esta nota é sobre X"). Escreva o conteúdo.
3. Seja específico: nomeie o sistema, a decisão, a restrição, os atores. Prosa
   genérica recupera genericamente.
4. Seja auto-contido: o leitor não deve precisar abrir o arquivo para saber o que a
   nota cobre.
5. Não use listas com marcadores. Bullets não embedam bem. Use prosa.

**Exemplos** — a diferença entre ruim e bom é o recall:

> ❌ "Decision about authentication." *(rótulo genérico, inútil para recall)*

> ✅ "Decisão de adotar OIDC com PKCE como fluxo de autenticação do dashboard interno,
> em vez de OAuth2 client-credentials, porque o dashboard é consumido por usuários
> humanos e queremos token de sessão curto com refresh, não credenciais de serviço de
> longa duração."

---

> ❌ "Incident in the deploy pipeline."

> ✅ "No dia 2026-05-30 o pipeline de deploy do api-gateway ficou parado 47 minutos
> depois que a action `cache@v3` foi deprecada e quebrou a restauração do cache de
> dependências; mitigamos pinando `cache@v4`. Causa raiz: não escutávamos o feed de
> deprecation do GitHub."

---

> ❌ "How to roll back."

> ✅ "Procedimento para reverter um release de produção do api-gateway usando
> `kubectl rollout undo` no deployment `api-gateway-prod` no namespace `prod`, com
> janela de validação de 5 minutos no dashboard de latência p99 antes de declarar o
> rollback concluído. Use apenas quando o release atual está ativo há menos de 30
> minutos; rollbacks mais antigos exigem o procedimento de migração de schema reverso."

Um summary mais curto que ~200 chars quase sempre significa "rótulo, não conteúdo".
Um summary mais longo que ~800 chars quase sempre significa "você colocou conteúdo do
corpo no summary". O corpo tem seu próprio lugar. E o summary nunca pode ser igual ao
título.

## 5. Entity completeness gate

Antes de escrever, construa um inventário das **entidades nomeadas, referências e fatos
temporais materiais** presentes na fonte. Material significa que o dado muda a
identidade, o significado, a rastreabilidade ou uma pergunta futura plausível; não
inclua substantivos genéricos nem exemplos incidentais.

O gate só passa quando cada item do inventário aparece no frontmatter estruturado e,
quando necessário para explicar a relação, no corpo. Se um item material estiver
ausente, complete a nota antes de gravar. Se duas identidades puderem corresponder ao
mesmo nome ou alias, não adivinhe: busque na KB e peça desambiguação quando a evidência
continuar insuficiente.

### Entidades e aliases

Preserve a grafia, capitalização e acentuação do **nome canônico** conforme a fonte mais
autoritativa observada. `aliases` contém somente siglas, handles, slugs, nomes anteriores
ou grafias alternativas realmente observadas; alias nunca substitui o nome canônico.

Tipos mínimos reconhecidos: `project`, `repository`, `person`, `company`, `brand`,
`system`, `product`, `service`, `team`, `technology` e `other`. Não funda
entidades só porque os nomes parecem semelhantes. Marca e empresa legal, project e
repository, ou duas pessoas homônimas permanecem separadas até existir evidência de
identidade.

Mantenha `entities` como a lista flat de nomes canônicos para compatibilidade. Registre
o detalhe em `entity_refs`:

```yaml
entities: [oh-my-harness, GitHub, Nelson Frugeri]
aliases: [OMH, github]
entity_refs:
  - kind: project
    name: oh-my-harness
    aliases: [OMH]
  - kind: brand
    name: GitHub
    aliases: [github]
  - kind: person
    name: Nelson Frugeri
    aliases: []
```

Não há limite arbitrário de entidades: registre **todas** as materiais. Deduplicate por
`kind + name canônico`; ordem de primeira ocorrência torna a revisão reproduzível.

### References e endereços

Toda URL ou path material vai para `references`, mesmo quando também aparece no corpo:

```yaml
references:
  - kind: repository-url
    label: oh-my-harness repository
    target: https://github.com/example/oh-my-harness
    entity: oh-my-harness
    status: verified
  - kind: repository-path
    label: local checkout
    target: /absolute/path/to/oh-my-harness
    entity: oh-my-harness
    status: observed
```

Kinds usuais: `repository-url`, `repository-path`, `website`, `document-url`,
`issue-url`, `artifact-path` e `other`. Preserve o target exato e estável. Para
local repository, resolva a raiz Git e o remote observado; `cwd` é provenance e não
prova o repo root. Valide sintaxe, existência local ou alcance remoto quando essa
observação for barata. Use `observed` quando apenas a fonte forneceu o valor e
`unverified` quando a validação falhar; nunca promova plausibilidade a `verified`.

Nunca persista credentials, tokens, URL userinfo, secret query params ou signed URLs.
Remova tracking params sem significado; se sanitizar tornaria o endereço inútil,
registre a referência como redacted e peça uma alternativa segura.

### Datas e horas

`occurred_at` registra o instante principal de um evento quando ele é conhecido.
`temporal_refs` preserva todas as demais datas, horas, deadlines e intervalos materiais,
cada um com significado. Normalize para ISO 8601 e preserve a timezone observada. Para
uma data sem hora, use `YYYY-MM-DD`; para uma hora sem timezone, grave `timezone:
unknown` — nunca invente UTC nem a timezone local. Somente um timestamp RFC 3339 com timezone
é projetado no payload Qdrant `occurred_at`; datas sem hora e valores com timezone
`unknown` permanecem recuperáveis em `temporal_values`, com `occurred_at: null` no
índice.

`tags` continua sendo o campo **transversal** do OKF: recortes que atravessam bounded
contexts (`["custo", "segurança"]`). Se a tag só faz sentido dentro de um contexto,
ela não é tag — é entidade. De zero a três tags; a maioria das notas não precisa de
nenhuma.

## 6. Relacionamentos — links markdown, não campo estruturado

Antes de escrever, **busque via `kb-retrieval`** com o tema da nova nota (use
`top_k >= 10`). Notas relevantes que aparecerem viram **links markdown no corpo**, na
frase que explica a relação:

```markdown
Substitui o fluxo definido em [rotação de chave KMS](/work/projects/api-gateway/procedures/2026-03-11--kms-rotation.md),
que assumia chave única por ambiente.

Motivada pelo incidente de [2026-05-30](/work/projects/api-gateway/events/2026-05-30--cache-deprecation.md).
```

Três regras de link:

1. **Caminho absoluto ao bundle** (começando com `/`, a partir de `~/knowledge-base/`).
   Sobrevive melhor à movimentação do que caminho relativo.
2. **O link mora na frase que explica a relação.** O OKF não tipa relacionamentos — quem
   diz que a relação é "substitui" ou "foi causada por" é a **prosa em volta**. Link
   solto numa lista de "ver também" não carrega informação.
3. **Nunca linke por similaridade de palavras** — linke por relação semântica real. Um
   link que o leitor não poderia prever a partir do contexto é um link errado.

**Limites quantitativos**: no máximo **5 links** por nota (acima disso vira ruído de
navegação). Na busca híbrida com fusão RRF (ver `kb-retrieval`), descarte candidatos com
`score < 0.4` — o RRF do Qdrant usa `k = 2` e rank base zero, então o teto é **1.0** e
0.4 é o piso de "aparece bem posicionado nas duas listas". Em corpus pequeno (≤ 50 notas)
o filtro de score não discrimina — confie inteiramente no critério qualitativo. Score
alto sem relação semântica real **não** vira link.

> Por que abandonamos `links_out: [uuid]`: uuid no frontmatter só é navegável por quem
> tem o índice. Link markdown é navegável por qualquer leitor, renderiza no GitHub,
> resolve no Obsidian e desenha o grafo — e é exatamente o que o OKF especifica.

## 7. Proveniência — quem, em qual sessão e em qual máquina

Todo conhecimento gravado por um agent carrega duas camadas de proveniência:

1. `generated` e `verified` registram quem produziu e quem confirmou o conhecimento.
2. `provenance` identifica o harness, a sessão, a execução e a máquina que originaram
   a escrita.

```yaml
generated:
  by: knowledge-base/3.0        # o agent que escreveu
  at: 2026-08-01T14:30:00Z
provenance:
  harness:
    name: codex
    session_id: 55cb8ac6-ffb4-417c-b9af-62e513f14737
    session_name: refactor-da-biblioteca-portable
    app_name: Codex Desktop
  execution:
    cwd: /Users/nelson.frugeri/projects/harness/oh-my-harness
    transcript_path: /Users/nelson.frugeri/.codex/sessions/2026/08/01/rollout.jsonl
  machine:
    id: 49d7a0f0-4f0d-4ea0-8987-0f442fab9130
    label: m4
    hostname: MacBook-Pro-de-Nelson
    username: nelson.frugeri
verified:
  - by: human:nelson            # o prefixo human: é obrigatório e define o tier de confiança
    at: 2026-08-01T15:02:00Z
```

- **`generated` sempre.** Nenhuma nota escrita por agent sai sem ele.
- **Campos obrigatórios e não nulos:** `provenance.harness.name`,
  `provenance.harness.session_id`, `provenance.execution.cwd`,
  `provenance.machine.id`, `provenance.machine.label`,
  `provenance.machine.hostname` e `provenance.machine.username`.
- Valor vazio ou composto apenas por whitespace equivale a ausente.
- **Campos obrigatoriamente presentes, mas nullable:**
  `provenance.harness.session_name`, `provenance.harness.app_name` e
  `provenance.execution.transcript_path`. Preserve o valor fornecido pelo harness;
  quando ele realmente não existir, grave `null`, nunca string vazia ou valor
  inventado.
- **Paths sempre absolutos.** `cwd` nunca usa `~` nem path relativo. Quando houver
  transcript, `transcript_path` segue a mesma regra.
- **Identidade local estável.** Leia `machine.id` e `machine.label` de
  `~/.local/share/omh-kb/identity.json`, inicializado de forma idempotente por
  `kb-infra`. O UUID nunca muda; `label` é o nome operacional legível (`m4`, `m1`,
  `ifood`). Capture `hostname` e `username` observados no momento da escrita.
- **Não use MAC address bruto.** Uma máquina pode ter vários adaptadores, MAC
  randomizado e mudanças por dock ou rede; além disso, é um identificador sensível.
  O UUID de `identity.json` é a identidade canônica da máquina.
- **Falha fechada.** Se qualquer campo obrigatório não puder ser resolvido, não escreva
  a nota. Informe exatamente o campo ausente e inicialize/corrija a identidade ou a
  descoberta da sessão antes de tentar novamente. A indisponibilidade do Qdrant não
  muda esta regra: ela adia apenas a indexação, nunca a proveniência.
- **`verified` só quando houve confirmação real do usuário** — ele leu e concordou.
  Nunca preencha `verified` por conta própria: seria falsificar a única marca de
  confiança que a KB tem.
- **`stale_after`** quando o conhecimento tem validade conhecida (preço, versão,
  política, headcount). Melhor declarar a data de expiração do que esperar alguém
  julgar frescor de cabeça.

## 8. Quando NÃO escrever

- O usuário está perguntando, explorando ou debatendo — sem conhecimento novo fechado.
- O conteúdo é genérico demais para ter entidades ("reunião sobre roadmap").
- O conhecimento já existe em nota vigente e nada mudou (não duplique — linke).
- O conteúdo é transitório e sem valor futuro (um TODO da tarde, um log de tentativa).

Na dúvida se algo merece nota, pergunte ao usuário uma vez.

---

## 9. Mecânica — o arquivo e o índice

### Arquivo em disco (fonte da verdade)

Cada nota é um markdown em `~/knowledge-base/<domain>/<tipo-entidade-plural>/`
(`mkdir -p` se preciso):

- **Nome do arquivo**: `<YYYY-MM-DD>--<slug-do-titulo>.md` (slug lowercase-kebab). A
  data no nome permite navegação cronológica sem abrir arquivos; a identidade canônica
  é o `id` do frontmatter, não o nome.
- **Frontmatter**:

```markdown
---
# --- OKF v0.2 ---
type: <substantivo do domínio, singular da pasta>
title: <título curto e específico>
description: <uma frase de vitrine — NÃO é o summary>
tags: [<0-3 recortes transversais>]
status: stable | draft | deprecated
generated:
  by: <producer/version>
  at: <ISO 8601 UTC>
provenance:
  harness:
    name: <harness>
    session_id: <id real da sessão>
    session_name: <nome real da sessão, ou null>
    app_name: <nome do app registrado pela sessão, ou null>
  execution:
    cwd: <path absoluto>
    transcript_path: <path absoluto, ou null>
  machine:
    id: <uuid estável de ~/.local/share/omh-kb/identity.json>
    label: <nome operacional da máquina>
    hostname: <hostname observado>
    username: <usuário observado>
verified:                       # só se houve confirmação humana real
  - by: human:<id>
    at: <ISO 8601 UTC>
stale_after: <YYYY-MM-DD>       # opcional, quando há validade conhecida

# --- extensões oh-my-harness (o spec permite qualquer chave extra) ---
id: <uuid4>
knowledge_type: decision | event | procedure | reference | conversation
domain: <caminho do bounded context, relativo à raiz do bundle>
created_at: <ISO 8601 UTC — nascimento da nota; é o que vai ao payload>
entities: [<todos os nomes canônicos materiais>]
aliases: [<aliases observados, ou vazio>]
entity_refs:
  - kind: <project | repository | person | company | brand | ...>
    name: <nome canônico>
    aliases: [<aliases observados>]
references:
  - kind: <repository-url | repository-path | website | document-url | issue-url | artifact-path | other>
    label: <descrição curta>
    target: <URL segura ou path absoluto>
    entity: <nome canônico relacionado, ou null>
    status: <verified | observed | unverified | redacted>
occurred_at: <ISO 8601 com timezone, YYYY-MM-DD, ou null>
temporal_refs:
  - value: <ISO 8601 ou intervalo normalizado>
    timezone: <timezone observada ou unknown>
    meaning: <o que a data/hora representa>
supersedes: <uuid da nota substituída, ou null>
summary: >
  <prosa densa de 200-800 chars — o texto que vira embedding>
---

<corpo seguindo references/note-template.md, com os relacionamentos como links markdown>
```

Duas notas sobre datas: **`created_at` é a data canônica da nota** — é ela que vai ao
payload do Qdrant e sustenta os filtros temporais do retrieval; numa nota imutável ela
nunca muda. O campo `timestamp` do OKF v0.1 **não é usado**: na v0.2 ele foi superado
por `generated.at`, e numa KB de notas imutáveis ele seria redundante com `created_at`.

### Arquivos reservados do bundle

- **`index.md`** — listagem do diretório, para navegação progressiva sem busca. Sempre
  que criar uma pasta de tipo de entidade nova, crie o `index.md` dela. Por convenção
  nossa (o spec apenas permite), o `index.md` da **raiz do bundle** declara
  `okf_version: "0.2"` e é o único que carrega essa chave.
- **`log.md`** — histórico cronológico do bounded context, agrupado por data, mais
  recente no topo. É o mesmo padrão da timeline do `context.md` mantido pelo `explorer`.

Nenhum dos dois carrega frontmatter de conceito, e nenhum é indexado como nota.

### Indexação no Qdrant (índice derivado)

Após gravar o arquivo, indexe na collection `knowledge-base` (desenho em `kb-infra`):
embede o **summary** com bge-m3 (dense 1024 + sparse) e faça upsert com o `id` da nota
como point id e payload `kind: "note"`, `id`, `title`, `type`, `knowledge_type`,
`domain`, `created_at`, `summary`, `path` (absoluto), `supersedes`, `archived: false`,
`entities`, `aliases`, `entity_kinds`, `entity_keys`, `reference_targets`, `occurred_at`,
`temporal_values`, `harness`, `session_id`, `session_name`, `app_name`, `cwd`,
`transcript_path`, `machine_id`, `machine_label`, `hostname` e `username`. Derive os
campos flat dos metadados estruturados no disco. Os campos nullable permanecem
no payload com valor nulo; não os omita.
Ao superseder, faça as duas coisas: vire o `status` da nota antiga para `deprecated` no
frontmatter dela (a única mutação permitida — ver seção 3) e atualize o payload dela
para `archived: true`. O corpo da nota antiga nunca muda.

Se o Qdrant estiver fora do ar: **o arquivo em disco é escrito mesmo assim** e a
indexação fica pendente — informe explicitamente e lembre que o reindex de `kb-infra`
reconcilia depois. Nunca deixe de registrar conhecimento por falta de índice.

## Regras de execução

1. **Nota é imutável** — correção = nota nova com `supersedes`. A **única** edição
   permitida num arquivo existente é virar o `status` dela para `deprecated` durante um
   supersede; corpo, título e summary nunca mudam.
2. **Escrita só em `~/knowledge-base/`** — nunca no repo do usuário.
3. **`type` é o singular da pasta; `knowledge_type` é o enum fechado.** Os dois eixos
   sempre presentes, nunca confundidos.
4. **Relacionamento é link markdown no corpo**, com caminho absoluto ao bundle e a
   relação explicada na prosa. `links_out` não existe mais.
5. **Summary 200–800 chars, ≠ título, ≠ `description`, prosa sem bullets** — é o
   contrato de recall.
6. **`generated` e `provenance` completos em toda nota; `verified` só com confirmação
   humana real.** Proveniência obrigatória ausente bloqueia a escrita; nunca invente
   metadata para satisfazer o schema.
7. **Pasta nasce na segunda nota do tipo; no máximo 3 níveis por bounded context.**
8. **Uma nota, um conhecimento** — natureza mista vira duas notas linkadas.
9. **Busque antes de escrever** — para descobrir relacionamentos e evitar duplicar nota
   vigente.
10. **Date tudo que pode driftar** — versões, custos, valores de config: use
    `stale_after` no frontmatter e a data de observação no corpo.
11. **Passe o entity completeness gate** — toda entidade, alias, referência e data/hora
    material da fonte fica estruturada; ambiguidade é desambiguada, nunca adivinhada.
12. **Endereços são seguros e verificáveis** — preserve URLs/paths úteis sem credentials,
    tokens ou signed URLs e declare quando não foi possível validá-los.
