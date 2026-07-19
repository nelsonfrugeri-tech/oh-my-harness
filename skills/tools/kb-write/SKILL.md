---
version: 1.0.0
name: kb-write
description: |
  O scribe da knowledge base — playbook de julgamento e mecânica para registrar
  conhecimento como notas imutáveis em ~/knowledge-base/{project}/notes/ (markdown com
  frontmatter) indexadas no Qdrant (summary → dense+sparse via BAAI/bge-m3). Cobre:
  quando criar vs. superseder (nota é conhecimento imutável num ponto do tempo — nunca
  editar in-place), o enum fechado de tipos (decision | event | procedure | reference |
  conversation) com critérios de escolha, como escrever o summary denso de 200-800
  chars que decide o recall, extração de entities, links entre notas, sinais
  linguísticos do usuário para supersede, e quando NÃO escrever. Invocada pelo agent
  `knowledge-base` quando a intenção é registrar conhecimento.
type: capability
---

# KB Write — o Scribe

Esta skill diz **como preencher os campos** de uma nota da knowledge base. A mecânica
(onde o arquivo vive, como indexar) está na seção final; o resto é **julgamento**:
quando escrever, qual tipo escolher, como escrever um summary que recupera bem, quais
entidades extrair e como descobrir notas existentes para linkar.

O corpo de toda nota segue o template em
[`references/note-template.md`](references/note-template.md).

---

## 1. Criar uma nota nova vs. atualizar uma existente (`supersedes`)

Uma nota é **conhecimento imutável num ponto no tempo**. Nunca edite uma nota
existente; escreva uma nota nova e defina `supersedes` com o id da nota substituída.

| Situação | O que fazer |
|---|---|
| Registrar algo novo (uma decisão que acabamos de tomar, um evento que acabou de acontecer, um procedimento que acabou de ser definido) | **Criar** — nota nova com `supersedes: null`. |
| O usuário pede explicitamente para **revisar**, **atualizar**, **corrigir** ou **substituir** uma nota existente | **Superseder** — busque a nota anterior via `kb-retrieval`, então escreva a nota nova com `supersedes: <id-anterior>`. A nova traz o conteúdo atualizado; a antiga permanece arquivada no histórico. |
| O usuário está fazendo uma pergunta ou explorando — nenhum conhecimento novo está sendo registrado | **Não escreva.** Escrever é *registrar* conhecimento, não conversar. |

Sinais do usuário que significam "superseder": "atualiza", "corrige", "revisa",
"agora ficou assim", "muda para", "a partir de hoje X em vez de Y".

Se não tiver certeza entre "isso corrige uma nota existente" e "isso é algo novo",
pergunte ao usuário uma vez. Não adivinhe.

## 2. Escolhendo o `type`

O enum é fechado: `decision | event | procedure | reference | conversation`.
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

**Natureza mista?** Escolha o tipo sobre o qual a nota é *principalmente*. Se uma
decisão foi tomada durante um incidente, são duas notas: um `event` para o incidente,
um `decision` para o que foi decidido — linkadas entre si.

## 3. Escrevendo o `summary` — aqui o recall é ganho ou perdido

O `summary` é o texto que será embedado (dense + sparse via bge-m3) para busca por
similaridade. Ele **não** é um rótulo. É uma **prosa densa, específica e auto-contida**
— um único parágrafo (**200–800 chars**) que outro agent poderia ler isoladamente e
entender do que a nota trata e por que é relevante.

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

## 4. Extraindo `entities`

`entities` é uma lista de substantivos de domínio sobre os quais a nota *trata*. Não
fazem parte do contrato de embedding — são metadados para filtragem e agrupamento.

- Incluir: nomes de sistemas, produtos/serviços, times ou pessoas se forem relevantes,
  tecnologias específicas, conceitos formais.
- Excluir: palavras genéricas ("sistema", "código", "usuário"), artigos, qualquer coisa
  substituível por sinônimo sem mudar o significado.

| Título / summary | Boas entidades | Por quê |
|---|---|---|
| "Decisão de migrar do Postgres 14 para 16 no banco de pedidos" | `["postgres", "pedidos-db", "migração"]` | Sistemas específicos + a operação. |
| "Procedimento de rotação de chave KMS no api-gateway" | `["kms", "api-gateway", "rotação-de-chave"]` | Concreto, pesquisável. |
| "Reunião sobre roadmap" | `[]` ou pule a nota | Genérico demais — provavelmente não deveria ser uma nota. |

De duas a seis entidades é a forma certa. Dez é ruído.

## 5. Propondo `links_out`

Antes de escrever, **busque via `kb-retrieval`** com o tema da nova nota (use
`top_k >= 10`). Se notas relevantes existentes aparecerem, inclua seus ids em
`links_out`. Isso transforma o corpus de um conjunto de notas em um grafo navegável.

Heurísticas para o que linkar:

- A nota que esta **sucede, contradiz ou refina**. Substituição direta é `supersedes`;
  "ver também" é `links_out`.
- Os **eventos** que motivaram uma decisão, ou as **decisões** causadas por um evento.
- O **procedimento** referenciado por uma decisão (para que o próximo leitor possa agir).
- Outras **referências** que definem os termos usados por esta nota.

Não linke por similaridade de palavras — linke por relação semântica real. Um link que
o leitor não poderia prever a partir do contexto é um link errado.

**Limites quantitativos**: no máximo **5 links** por nota (acima disso a lista vira
ruído de navegação). Na busca híbrida com fusão RRF (ver `kb-retrieval`), descarte
candidatos com `score < 0.02` — o score RRF com `k=60` e duas listas (dense + sparse)
tem teto teórico ≈ 0.033; 0.02 captura hits consistentes nas duas listas sem incluir
ruído. Em corpus pequeno (≤ 50 notas) o filtro de score não discrimina — confie
inteiramente no critério qualitativo. Score alto sem relação semântica real **não**
vira link: o critério qualitativo prevalece sempre.

## 6. Quando NÃO escrever

- O usuário está perguntando, explorando ou debatendo — sem conhecimento novo fechado.
- O conteúdo é genérico demais para ter entidades ("reunião sobre roadmap").
- O conhecimento já existe em nota vigente e nada mudou (não duplique — linke).
- O conteúdo é transitório e sem valor futuro (um TODO da tarde, um log de tentativa).

Na dúvida se algo merece nota, pergunte ao usuário uma vez.

---

## 7. Mecânica — onde a nota vive e como é indexada

### Arquivo em disco (fonte da verdade)

Cada nota é um arquivo markdown em `~/knowledge-base/{project}/notes/`
(`{project}` = basename do cwd, lowercase-kebab; `mkdir -p` se preciso):

- **Nome do arquivo**: `<YYYY-MM-DD>--<slug-do-titulo>.md` (slug lowercase-kebab). A
  data no nome permite navegação cronológica sem abrir arquivos; a identidade canônica
  é o `id` do frontmatter, não o nome.
- **Frontmatter obrigatório**:

```markdown
---
id: <uuid4>
title: <título curto e específico>
type: decision | event | procedure | reference | conversation
project: <project>
created_at: <ISO 8601 UTC, ex.: 2026-07-19T14:30:00Z>
entities: [<2-6 substantivos de domínio>]
links_out: [<uuids de notas relacionadas, máx. 5>]
supersedes: <uuid da nota substituída, ou null>
summary: >
  <prosa densa de 200-800 chars — o texto que vira embedding>
---

<corpo seguindo references/note-template.md>
```

- **Corpo**: siga o template por tipo em
  [`references/note-template.md`](references/note-template.md).

### Indexação no Qdrant (índice derivado)

Após gravar o arquivo, indexe no Qdrant (collection `knowledge-base`, desenho em
`kb-infra`): embede o **summary** com bge-m3 (dense 1024 + sparse) e faça upsert com o
`id` da nota como point id e payload `id`, `title`, `type`, `project`, `created_at`,
`summary`, `path` (path absoluto do arquivo), `supersedes`, `archived: false`. Ao
superseder, além de indexar a nova, atualize o payload da nota antiga para
`archived: true` (o arquivo dela em disco não muda — imutabilidade é do conteúdo).

Se o Qdrant estiver fora do ar: **o arquivo em disco é escrito mesmo assim** e a
indexação fica pendente — informe explicitamente e lembre que o reindex de `kb-infra`
reconcilia depois. Nunca deixe de registrar conhecimento por falta de índice.

## Regras de execução

1. **Nota é imutável** — nunca edite arquivo de nota existente; correção = nota nova
   com `supersedes`.
2. **Escrita só em `~/knowledge-base/`** — nunca no repo do usuário.
3. **Summary 200–800 chars, ≠ título, prosa sem bullets** — é o contrato de recall.
4. **Uma nota, um conhecimento** — natureza mista vira duas notas linkadas.
5. **Busque antes de escrever** — para descobrir `links_out` e evitar duplicar nota
   vigente.
6. **Date tudo que pode driftar** — versões, custos, valores de config: inclua a data
   de observação no corpo.
