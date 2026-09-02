---
version: 4.1.0
name: kb-write
description: |
  O scribe da knowledge base — playbook de julgamento e mecânica para registrar
  conhecimento como notas imutáveis em bundles conformes ao Open Knowledge Format
  (OKF v0.2): markdown com YAML frontmatter em ~/knowledge-base/, indexado no Qdrant
  (summary → dense+sparse via BAAI/bge-m3). Cobre: onde a nota mora (scope + bounded
  context + topic estável), resolução do projeto por evidência, os dois eixos de classificação
  (`type` = o substantivo do domínio, exigido pelo OKF; `knowledge_type` = o enum
  fechado decision | event | procedure | reference | conversation, que diz como o
  conhecimento foi obtido), quando criar vs. superseder (nota é conhecimento imutável
  num ponto do tempo — nunca editar in-place), como escrever o summary denso de 200-800
  chars que decide o recall, extração de entities e tags, relacionamentos como links
  markdown no corpo (não como campo estruturado), proveniência de agent, harness,
  sessão e máquina, sinais linguísticos do usuário para supersede, destilação
  idempotente de sessões longas em várias notas atômicas interligadas, e quando NÃO
  escrever.
  Invocada pelo agent `knowledge-base` quando a intenção é registrar conhecimento.
type: capability
---

# KB Write — o Scribe

Esta skill diz **onde a nota mora** e **como preencher seus campos**. A mecânica (nome
de arquivo, indexação) está na seção final; o resto é **julgamento**: em que domínio
registrar, qual topic e entidade a nota descrevem, como escrever um summary que recupera
bem, e com o que ela se relaciona.

O corpo de toda nota segue o template em
[`references/note-template.md`](references/note-template.md).

---

## 1. Onde a nota mora — scope, domain e topic

A knowledge base inteira é **um bundle OKF**: uma árvore de markdown enraizada em
`~/knowledge-base/`. A árvore é uma ontologia deliberada, mas não tenta codificar
todas as dimensões no path. O routing primário é:

```text
scope → domain → topic → concept
```

- **Scope** separa as grandes fronteiras de acesso e significado: `person` e `work`.
- **Domain** é o bounded context. Para software, é
  `work/projects/<project>`; para conhecimento técnico transversal pode ser
  `work/data-architecture`; para a empresa, `work/ifood`.
- **Topic** é o assunto ou entidade temática estável dentro do domain, em
  lowercase-kebab: `knowledge-base`, `codex-adapter`, `authentication`.
- **Concept** é uma unidade de conhecimento em um Markdown.

O layout padrão nasce topic-first:

```
~/knowledge-base/                    # raiz do bundle (index.md declara okf_version)
  person/                            # scope e domain para vida pessoal
    health/                          # topic
      <YYYY-MM-DD>--<short-slug>.md
  work/
    data-architecture/               # domain transversal
      icloud/                        # topic
        <YYYY-MM-DD>--<short-slug>.md
    projects/
      oh-my-harness/                 # domain de um projeto
        context.md
        sessions/
        knowledge-base/              # topic
          index.md
          <YYYY-MM-DD>--<short-slug>.md
```

### Resolva o projeto antes do topic

Para conhecimento de software, determine o project nesta ordem:

1. Considere o nome de projeto fornecido explicitamente pelo usuário como identidade
   legível, não como autorização para divergir o path canônico.
2. Para todo repositório Git, use o resolver canônico compartilhado
   por `explorer`, `kb-session` e `context-load.sh`: basename da raiz Git, lowercase,
   caracteres fora de `[a-z0-9-]` convertidos em hífen, hífens repetidos colapsados e
   pontas aparadas. Esse slug único mantém notas, contexto e sessões no mesmo domain.
3. Antes de escrever num domain existente, prove que ele pertence ao mesmo repo. Com
   `context.md`, valide `remote_url` e `Repository` contra o remote e a raiz Git
   observados. Sem `context.md`, inspecione a provenance de **todas** as notas e session
   records existentes: resolva a raiz Git e o remote dos `cwd` ainda acessíveis e exija
   compatibilidade. Artifact existente sem identidade suficiente deixa o domain
   ocupado e ambíguo; falhe fechado. Divergência ou ambiguidade é colisão a reportar;
   nunca procure outro slug nem redirecione somente a nota.
4. Se não houver identidade Git estável, o projeto ainda não está registrado: pergunte
   uma vez qual nome e slug canônicos o usuário quer antes de criar
   `work/projects/<project>/index.md`. Esse caso não é consumido pelo context loader
   até existir uma associação futura explícita.
5. Em repo Git, colisão bloqueia a escrita: informe as identidades observadas e
   não crie outro slug. A escrita só pode continuar depois que um resolver persistente
   e compartilhado por `explorer`, `kb-session`, `context-load.sh` e `kb-write` tiver
   sido definido; um alias local fragmentaria o bounded context.
6. Se o conhecimento não pertencer a projeto, escolha o domain não-projeto adequado;
   nunca force tudo para `work/projects`.

Projeto Git resolvido pelo algoritmo compartilhado não gera pergunta repetida. Nunca
aceite nem descubra um slug alternativo para o mesmo remote ou raiz: isso fragmenta
notas, `context.md` e session records em domains diferentes.

### Resolva o topic por evidência

Antes de criar path, busque notas relacionadas e leia o `index.md` do domain:

1. Reutilize um topic existente quando ele cobre o mesmo assunto ou entidade dominante.
2. Sem topic compatível, derive um nome curto e específico das entities centrais e crie
   a pasta de assunto já na primeira nota, junto com seu `index.md`.
3. Se dois topics existentes forem igualmente plausíveis e a escolha mudar a
   interpretação, pergunte uma vez; não escolha por similaridade lexical superficial.
4. `type` não determina o diretório. Ele continua metadata do conceito; o mesmo topic
   pode conter decisions, procedures, references e components.
5. Subpastas físicas por type são opcionais e só existem por decisão explícita de layout
   registrada no `index.md` do topic. Nunca surgem por contagem de notas.

Relacionamentos como depende-de, causou, substitui e opera são links Markdown no corpo,
não diretórios. Mantenha no máximo dois níveis semânticos abaixo do domain
(`topic[/subtopic]`); profundidade maior pede links ou revisão do domain.

### Preserve o path

No OKF, o path relativo é o Concept ID. Nunca mova ou renomeie uma nota durante uma
escrita normal. Reorganização é uma migração explícita: valide e reescreva links,
`index.md` e payloads Qdrant de todos os conceitos afetados antes de concluir. O UUID
da extensão oh-my-harness não torna uma mudança de path invisível a consumidores OKF.

## 2. Os dois eixos de classificação

Toda nota responde **duas** perguntas diferentes, e por muito tempo respondemos só uma:

| Campo | Pergunta | Valores |
|---|---|---|
| `type` | **Que entidade ou conceito é este?** | String livre e autoexplicativa: `system`, `person`, `team`, `ritual`, `metric`, `component`, `decision`... Exigido pelo OKF. |
| `knowledge_type` | **Como eu sei disso?** — a natureza epistêmica | Enum **fechado**: `decision \| event \| procedure \| reference \| conversation`. Extensão nossa. |

O OKF deixa `type` livre de propósito. Use um substantivo de domínio estável e
autoexplicativo, mas não derive o path dele: topic organiza pertencimento temático;
`type` e `knowledge_type` organizam filtros e views.

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

## 5. Extraindo `entities` e `tags`

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

`tags` é o campo **transversal** do OKF: recortes que atravessam bounded contexts
(`["custo", "segurança"]`). Se a tag só faz sentido dentro de um contexto, ela não é
tag — é entidade. De zero a três tags; a maioria das notas não precisa de nenhuma.

## 6. Relacionamentos — links markdown, não campo estruturado

Antes de escrever, **busque via `kb-retrieval`** com o tema da nova nota (use
`top_k >= 10`). Notas relevantes que aparecerem viram **links markdown no corpo**, na
frase que explica a relação:

```markdown
Substitui o fluxo definido em [rotação de chave KMS](/work/projects/api-gateway/security/2026-03-11--kms-rotation.md),
que assumia chave única por ambiente.

Motivada pelo incidente de [2026-05-30](/work/projects/api-gateway/delivery/2026-05-30--cache-deprecation.md).
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
  by: knowledge-base/4.1        # o agent que escreveu
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

### Destilação de sessão longa em várias notas

Quando o usuário ou outro agent pedir explicitamente para **destilar a sessão inteira**,
combine o corpus integral produzido por `kb-session` com este workflow. A atualização
automática do session record **não cria notas automaticamente**: memória episódica e
conhecimento curado continuam separados.

1. Exija o relatório de cobertura de `kb-session`. Se houver intervalo não processado,
   transcript ausente ou provenance inválida, não afirme completude; registre o gap e
   prossiga somente com a parcela que possa ser identificada sem ambiguidade.
2. Agrupe candidatos por domain, topic e entidade dominante. Quebre cada grupo em
   conhecimentos atômicos; uma nota por conhecimento, mesmo que vários tenham surgido
   na mesma conversa.
3. Para cada candidato, derive `distillation_key` como SHA-256 de um JSON UTF-8 canônico
   com estes campos, serializados com chaves em ordem lexicográfica: `algorithm` fixo em
   `omh-kb-distillation-v1`, `evidence` como array de ids ou pares de offsets ordenados
   numericamente, `harness`, `knowledge_type`, `session_id`, `topic` e `concept_key`.
   Normalize strings em Unicode NFC, converta line endings para LF, colapse whitespace
   interno em um espaço e remova whitespace nas pontas; serialize sem indentação nem
   espaços entre tokens e sem escaping ASCII. `concept_key` é uma identidade curta em
   kebab-case baseada na entidade dominante e na alegação atômica, não no texto
   parafraseado da nota. A mesma evidência e o mesmo conceito devem produzir os mesmos
   bytes em qualquer execução. Faça primeiro uma busca exata em disco por essa chave e
   só então execute `kb-retrieval`. Classifique a ação no
   **plano de notas** como `create | supersede | skip`, citando a evidência da sessão e
   a nota vigente relacionada. Chave já presente, duplicata semântica ou conteúdo
   transitório resultam em `skip`; nunca dependa apenas do Qdrant para idempotência.
   Ao encontrar a chave em disco, antes do `skip`, valide e repare o `index.md` do topic,
   os índices ancestrais e a indexação Qdrant pendente. A nota permanece imutável; apenas
   estruturas mutáveis ou derivadas são reconciliadas, e o manifesto registra
   `reconciled` ou a pendência que ainda falhou.
4. Defina os links entre candidatos somente quando houver relação semântica explícita
   — por exemplo, uma decisão motivada por um evento — e preserve o limite de cinco
   links por nota. Ordem cronológica ou tema parecido, sozinhos, não criam relação. Um
   link só pode ser publicado quando o destino já existe em disco. Ordene a escrita
   para publicar primeiro os destinos; se um destino falhar ou houver ciclo entre
   candidatos novos, omita a relação e registre a pendência no manifesto.
5. Escreva e indexe cada nota como uma unidade independente. Uma falha não apaga as
   notas concluídas: reporte por candidato `written`, `indexed`, `pending` ou `failed`.
6. Torne a operação idempotente: numa reexecução sobre a mesma sessão e o mesmo
   conhecimento, a busca exata em disco por `distillation_key` deve impedir outra nota
   e levar à reconciliação descrita acima, seguida de `skip`, inclusive se o Qdrant
   continuar indisponível. Só use `supersede` quando a sessão realmente altera
   conhecimento vigente; a nova versão recebe uma chave distinta porque seu
   fingerprint ou sua evidência mudou.
7. Encerre com um manifesto: intervalo e fonte cobertos, topics encontrados, candidatos
   por ação, paths criados, links estabelecidos e pendências. Contagens incluem unidade,
   população, janela, fonte e método; nunca use “tudo” quando a cobertura tiver gap.

---

## 9. Mecânica — o arquivo e o índice

### Arquivo em disco (fonte da verdade)

Cada nota é um Markdown em
`~/knowledge-base/<domain>/<topic>/[<subtopic>/]<YYYY-MM-DD>--<short-slug>.md`
(`mkdir -p` se preciso):

Para projetos, o caso canônico é
`work/projects/<project>/<topic>/<YYYY-MM-DD>--<short-slug>.md`.

- **Nome do arquivo**: `<YYYY-MM-DD>--<short-slug>.md`, com um slug lowercase-kebab de
  **2 a 6 termos substantivos** que identifiquem o conceito sem repetir o título
  inteiro. A data permite navegação cronológica. No OKF, o path relativo é o Concept
  ID; o UUID do frontmatter é a identidade do índice derivado, não substitui o path.
- **Frontmatter**:

```markdown
---
# --- OKF v0.2 ---
type: <substantivo autoexplicativo da entidade ou conceito>
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
distillation_key: <sha256 determinístico, ou null fora de destilação de sessão>
knowledge_type: decision | event | procedure | reference | conversation
domain: <caminho do bounded context, relativo à raiz do bundle>
topic: <assunto estável em lowercase-kebab, relativo ao domain>
created_at: <ISO 8601 UTC — nascimento da nota; é o que vai ao payload>
entities: [<2-6 substantivos de domínio>]
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

- **`index.md`** — listagem do diretório, para navegação progressiva sem busca. Em toda
  escrita, atualize atomicamente o `index.md` do topic para listar o conceito e os
  índices ancestrais relevantes para listar topics ou subtopics novos. Ao criar um
  topic ou subtopic, crie seu `index.md` na mesma operação, descrevendo o escopo do
  assunto e listando seus conceitos ou filhos. Uma nota só conta como concluída depois
  dessa reconciliação; falha preserva a versão anterior dos índices e entra no
  manifesto. Por convenção nossa (o spec apenas
  permite), o `index.md` da **raiz do bundle** declara
  `okf_version: "0.2"` e é o único que carrega essa chave.
- **`log.md`** — histórico cronológico do bounded context, agrupado por data, mais
  recente no topo. É o mesmo padrão da timeline do `context.md` mantido pelo `explorer`.

Nenhum dos dois carrega frontmatter de conceito, e nenhum é indexado como nota.

### Indexação no Qdrant (índice derivado)

Após gravar o arquivo, indexe na collection `knowledge-base` (desenho em `kb-infra`):
embede o **summary** com bge-m3 (dense 1024 + sparse) e faça upsert com o `id` da nota
como point id e payload `kind: "note"`, `id`, `title`, `type`, `knowledge_type`,
`domain`, `topic`, `distillation_key`, `created_at`, `summary`, `path` (absoluto),
`supersedes`, `archived: false`,
`harness`, `session_id`, `session_name`, `app_name`, `cwd`, `transcript_path`,
`machine_id`, `machine_label`, `hostname` e `username`. Os campos nullable permanecem
no payload com valor nulo; não os omita.
Ao superseder, faça as duas coisas: vire o `status` da nota antiga para `deprecated` no
frontmatter dela (a única mutação permitida — ver seção 3) e atualize o payload dela
para `archived: true`. O corpo da nota antiga nunca muda.

Se o Qdrant estiver fora do ar: **o arquivo em disco é escrito mesmo assim** e a
indexação fica pendente — informe explicitamente e lembre que o reindex de `kb-infra`
reconcilia depois. Nunca deixe de registrar conhecimento por falta de índice.

### Compatibilidade com notas legadas

Notas históricas na raiz do domain ou em pastas orientadas por type continuam legíveis
e reindexáveis com `topic: null`. Uma escrita normal nunca as move ou rebatiza. Quando
conhecimento legado for supersedido, a nota nova segue o routing topic-first e cria um
link explícito para o path antigo. Reorganizar o corpus existente exige uma migração
separada e auditável, não faz parte de uma captura comum.

## Regras de execução

1. **Nota é imutável** — correção = nota nova com `supersedes`. A **única** edição
   permitida num arquivo existente é virar o `status` dela para `deprecated` durante um
   supersede; corpo, título e summary nunca mudam.
2. **Escrita só em `~/knowledge-base/`** — nunca no repo do usuário.
3. **`type` descreve a entidade; `knowledge_type` é o enum fechado.** Ambos são metadata
   obrigatória e nenhum deles determina o diretório.
4. **Relacionamento é link markdown no corpo**, com caminho absoluto ao bundle e a
   relação explicada na prosa. `links_out` não existe mais.
5. **Summary 200–800 chars, ≠ título, ≠ `description`, prosa sem bullets** — é o
   contrato de recall.
6. **`generated` e `provenance` completos em toda nota; `verified` só com confirmação
   humana real.** Proveniência obrigatória ausente bloqueia a escrita; nunca invente
   metadata para satisfazer o schema.
7. **Route topic-first e preserve paths.** Crie topic e `index.md` na primeira nota;
   use no máximo `topic[/subtopic]`. Diretório por type só existe por layout explícito.
8. **Uma nota, um conhecimento** — natureza mista vira duas notas linkadas.
9. **Busque antes de escrever** — para descobrir relacionamentos e evitar duplicar nota
   vigente.
10. **Date tudo que pode driftar** — versões, custos, valores de config: use
    `stale_after` no frontmatter e a data de observação no corpo.
