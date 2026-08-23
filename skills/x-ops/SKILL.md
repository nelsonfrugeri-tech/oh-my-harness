---
version: 1.0.0
name: x-ops
description: |
  Playbooks de operação da plataforma X (Twitter) pela capability `social-x`. Cobre: a
  descoberta de tools em runtime (o servidor MCP gera as tools do OpenAPI spec da X API —
  nunca hardcode nomes); a guarda de custo obrigatória (pay-as-you-go: $0.005 por post
  lido, $0.015 por post criado, $0.20 com link) com estimativa antes e prestação de contas
  depois; a linguagem de query da busca (operadores from/to/url/lang/has/is, booleanos,
  negação, janelas temporais) e a diferença entre recent e full-archive; reconstrução de
  thread por conversation_id; leitura de perfil, trends/news e bookmarks; o protocolo de
  publicação com confirmação explícita por post; e como resumir a plataforma sem inventar
  conteúdo. Invocada pelo agent `x-social` quando a intenção é ler ou publicar — não
  destinada a invocação direta solta.
type: capability
---

# X Ops — Operando a Plataforma X

Você lê e publica no X em nome do usuário. Três princípios governam toda operação:

1. **Cada chamada custa.** A X API é pay-as-you-go. Volume é decisão do usuário, não sua.
2. **Publicar é irreversível e público.** Confirmação explícita, um post de cada vez.
3. **O que você não leu, você não afirma.** Nunca invente post, autor ou métrica.

---

## 1. Descubra as tools em runtime

O servidor MCP oficial carrega o **OpenAPI spec da X API no startup** e converte cada operação
numa tool. O conjunto muda quando a API muda.

**Nunca hardcode um nome de tool.** Liste o que a capability `social-x` expõe, leia as
descrições e escolha a operação pela semântica. Se a tool estiver deferida, carregue-a via
`ToolSearch` antes de chamar.

As áreas cobertas hoje: **posts**, **busca full-archive**, **users**, **bookmarks**,
**news/trends** e **Articles**.

Se nenhuma tool corresponder à intenção, diga isso — não improvise com uma operação vizinha
que devolve outra coisa.

---

## 2. Guarda de custo (fato vinculante)

| Operação | Preço |
|---|---|
| Post lido | $0.005 |
| Post criado | $0.015 |
| Post criado **com link** | $0.20 |

O protocolo, em toda operação de leitura:

1. **Estime antes.** `max_results` é o multiplicador direto do custo. 100 resultados ≈ $0.50.
2. **Peça autorização acima do limiar.** Qualquer leitura projetada em **mais de ~$0.25**
   (≈ 50 posts) só roda com o usuário sabendo o número. Abaixo disso, execute e informe.
3. **Preste contas depois.** Diga quantos itens vieram e o custo incorrido.

Regras de economia, nesta ordem:

- **Sempre passe `max_results` explícito.** Nunca aceite o default do servidor às cegas.
- **Estreite a query antes de aumentar o volume.** Um operador a mais custa nada; cem posts a
  mais custam $0.50.
- **Prefira `recent` a `full-archive`** quando a pergunta é sobre os últimos dias.
- **Não repita a mesma leitura.** Se você já leu esses posts nesta sessão, reuse o que está no
  contexto — reler é pagar duas vezes pelo mesmo dado.
- **Nunca pagine "até acabar".** Pare no volume autorizado e ofereça continuar.

Em loop automatizado (cron, workflow) não há quem autorize — então a autorização tem que ter
sido dada **antes**, como número. Só leia se a automação declarar um **orçamento por ciclo**;
sem orçamento declarado, **não leia** — reporte que a leitura ficou pendente de um teto. Nunca
exceda o orçamento do ciclo, e reporte o gasto acumulado a cada volta. "Use o mínimo" não é
salvaguarda: leituras pequenas repetidas de hora em hora somam uma fatura real no fim do mês.

---

## 3. Busca

### Operadores

Combine operadores para estreitar antes de aumentar volume:

| Operador | Efeito |
|---|---|
| `from:handle` / `to:handle` | autoria / resposta dirigida |
| `@handle` | menções |
| `#hashtag` | hashtag |
| `url:"dominio.com"` | posts que linkam um domínio |
| `lang:pt` | idioma (código ISO) |
| `conversation_id:<id>` | todos os posts de uma thread |
| `has:links` · `has:media` · `has:images` · `has:videos` | filtros de conteúdo |
| `is:retweet` · `is:reply` · `is:quote` | tipo do post |
| `-<termo>` ou `-is:retweet` | negação |
| `"frase exata"` | correspondência literal |
| `(a OR b) c` | booleanos com agrupamento |

`OR` precisa ser maiúsculo; termos justapostos são `AND` implícito.

**Receita padrão para sinal limpo:** `-is:retweet -is:reply` corta eco e ruído de conversa,
normalmente derrubando o volume — e o custo — pela metade sem perder o conteúdo original.

```
(claude OR anthropic) lang:pt -is:retweet -is:reply has:links
```

### Recent × full-archive

| | Janela | Quando usar |
|---|---|---|
| **Recent** | últimos ~7 dias | "o que estão falando agora", monitoramento |
| **Full-archive** | histórico completo | pesquisa histórica, "quando foi a primeira vez que…" |

Full-archive é a ferramenta mais cara que você tem. Só dispare com janela temporal
(`start_time`/`end_time`) **e** `max_results` acordados com o usuário.

### Campos

Peça só os campos que você vai usar. Trazer o objeto inteiro de autor, mídia e métricas em
100 posts infla o payload sem melhorar a resposta. Para citar um post você precisa de: id,
texto, autor e timestamp.

---

## 4. Leitura

**Post único** — de uma URL `x.com/<handle>/status/<id>`, o id é o último segmento. Busque o
post por id, não por busca textual.

**Thread** — pegue o `conversation_id` do post raiz e busque `conversation_id:<id>`; ordene
por tempo. Autorize o volume antes: threads longas custam por post lido. Se a thread for maior
que o autorizado, leia o raiz e os primeiros N, e diga quantos ficaram de fora.

**Perfil** — resolva o handle para o objeto de usuário; só então busque posts com `from:`. Um
handle não é um id, e nem todo perfil é público.

**Trends / news** — leitura barata e ampla, boa para orientação antes de uma busca cara. Trend
é sinal de volume, não de veracidade: nunca apresente um trend como fato.

**Bookmarks** — exige contexto de usuário (OAuth). Em auth app-only, diga que está
indisponível em vez de tentar.

---

## 5. Publicação

### Protocolo (fato vinculante)

Antes de **todo** post, reply, repost, delete ou Article:

1. **Apresente o texto final exato**, com:
   - contagem de caracteres
   - se contém link (**custa $0.20 em vez de $0.015** — 13× mais)
   - a quem responde / o que cita, se for o caso
2. **Espere um "sim" explícito para este post.** Aprovação a um rascunho anterior, "ficou bom"
   ou um "pode postar" dado a outro post **não valem**.
3. **Publique** e devolva a URL do post criado e o custo.

Uma autorização = uma publicação. **Exceção única:** uma thread aprovada **como conjunto** —
a autorização cobre exatamente os posts mostrados, com o custo total informado antes; alterou
o texto de qualquer um deles, a autorização caiu. Sem humano no loop, **não publique**:
entregue o rascunho pronto e reporte como pendente de aprovação.

### Redação

- **Não invente a voz do usuário.** Sem um estilo declarado ou exemplos que ele forneceu,
  escreva neutro e deixe ele ajustar. Um post soa como a pessoa, não como um assistente.
- **Idioma do post = idioma do público**, não o desta conversa. Pergunte se não estiver óbvio.
- **Sem hashtag decorativa e sem emoji de preenchimento** a menos que ele peça.
- **Link cobra caro** — se o link não é o ponto do post, sugira tirá-lo.
- **Thread** é uma sequência de publicações, cada uma com seu custo: mostre a thread **inteira**
  e obtenha uma autorização para o conjunto, informando o custo total antes.

### Delete

Deletar também é irreversível — o conteúdo não volta, e o post pode já ter sido visto ou
citado. Mesmo protocolo: mostre o post que será apagado, confirme, execute.

---

## 6. Reportando

Ao resumir a plataforma:

- **Cite a URL** de todo post que você atribuir a alguém.
- **Separe leitura de inferência.** "3 dos 20 posts lidos criticam X" é leitura; "a comunidade
  está dividida" é inferência sobre uma amostra — rotule como tal.
- **Declare a amostra.** Quantos posts, que query, que janela. Uma conclusão sem denominador é
  ruído com formatação bonita.
- **Nunca produza número que você não leu.** Se a métrica de engajamento não veio no payload,
  ela não existe na sua resposta.
- **Feche com o custo** da operação e o que ficou de fora do volume autorizado.
