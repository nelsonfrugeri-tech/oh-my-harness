---
version: 1.0.0
name: kb-retrieval
description: |
  Recuperação de conhecimento da knowledge base como uma escada de 3 degraus: (1) busca
  semântica híbrida no Qdrant sobre notas E session records (query → embedding
  BAAI/bge-m3 dense+sparse → dois prefetch fundidos com Reciprocal Rank Fusion, filtros
  por kind/type/project/data via payload); (2) navegação estruturada dos diretórios
  ~/knowledge-base/ — notes/ e sessions/ — como fallback sem Qdrant; (3) deep search na
  session memory bruta do harness via kb-session, quando os degraus anteriores não
  respondem. Cobre também resolução de cadeias supersedes (sempre preferir a nota mais
  recente da cadeia) e montagem de resposta com citação das fontes. Invocada pelo agent
  `knowledge-base` quando a intenção é buscar/recuperar conhecimento — também usada por
  kb-write para descobrir links.
type: capability
---

# KB Retrieval — Recuperação de Conhecimento

Você responde perguntas a partir da knowledge base em `~/knowledge-base/`, subindo uma
**escada de 3 degraus** — do mais barato ao mais profundo:

| Degrau | Via | Quando descer para o próximo |
|---|---|---|
| **1** | Busca semântica híbrida no Qdrant — notas **e** session records | Qdrant fora do ar → degrau 2. Resposta ausente ou parcial com Qdrant saudável → degrau 3. |
| **2** | Navegação estruturada em disco — `notes/` **e** `sessions/` | Resposta ausente ou parcial → degrau 3 (usando os session records achados em disco). |
| **3** | Deep search na session memory bruta do harness, via `kb-session` | Último degrau — se nada, diga que não foi encontrado. |

Duas obrigações transversais: **anuncie na resposta qual degrau a respondeu** (a
diferença entre "busca semântica", "grep estrutural" e "trecho do transcript de uma
sessão" importa para o leitor) e **nunca escale silenciosamente** — a descida de degrau
é sempre declarada, nunca disfarçada de resultado do degrau anterior.

---

## 1. Degrau 1 — Busca semântica híbrida (via principal)

Desenho validado na era oh-my-kb — espelhe-o:

1. **Embede a query** com bge-m3 (padrão de `kb-infra`): um forward pass produz o vetor
   dense (1024) e o sparse (`indices`/`values`).
2. **Dois prefetch, um por espaço vetorial**, cada um com limite `top_k * 4` (o fusion
   precisa de um candidate set profundo por lista; 4x equilibra recall e custo):
   - dense → named vector `"dense"`
   - sparse → named vector `"sparse"`
3. **Fusão com RRF** (`FusionQuery(fusion=Fusion.RRF)`) e `limit=top_k`.
4. **Filtros server-side no nível do prefetch** (não depois da fusão): `project`
   (match no payload), `type` (match), janela de `created_at` (range DATETIME), e
   `must_not archived=true` por padrão.

A collection indexa **dois kinds** de ponto (payload `kind`, ver `kb-infra`): notas
(`kind: "note"`, embedding do summary) e session records (`kind: "session"`, embedding
de `name + description + resume` — mantidos por `kb-session`). Por padrão busque
**sem filtro de `kind`** — sessões passadas são fonte legítima de resposta; filtre por
`kind` só quando a pergunta é claramente de um lado ("qual o procedimento de X?" →
`note`; "em que sessão falamos de Y?" → `session`). O `must_not archived=true` não
exclui sessões: session records não carregam `archived`.

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition, Filter, Fusion, FusionQuery, MatchValue, Prefetch,
    SparseVector,
)

client = QdrantClient(url="http://localhost:6333")
flt = Filter(
    must=[FieldCondition(key="project", match=MatchValue(value=project))],
    must_not=[FieldCondition(key="archived", match=MatchValue(value=True))],
)
prefetch = [
    Prefetch(query=dense, using="dense", filter=flt, limit=top_k * 4),
    Prefetch(query=SparseVector(indices=idx, values=vals), using="sparse", filter=flt, limit=top_k * 4),
]
points = client.query_points(
    collection_name="knowledge-base",
    prefetch=prefetch,
    query=FusionQuery(fusion=Fusion.RRF),
    limit=top_k,
    with_payload=True,
).points
```

**Interpretação do score**: o score é RRF (`1/(60+rank_a) + 1/(60+rank_b)`), não
similaridade de cosseno — teto teórico ≈ 0.033 com duas listas. Faixas práticas:
`>= 0.025` hit forte nas duas listas; `0.015–0.025` presença moderada; `< 0.015`
provavelmente ruído. Em corpus pequeno (≤ 50 notas) todos os scores ficam altos e o
filtro não discrimina — julgue pela relação semântica real.

Collection inexistente **não é erro** — significa "nenhuma nota indexada ainda":
devolva resultado vazio e sugira o fallback em disco ou o reindex de `kb-infra`.

## 2. Degrau 2 — Navegação estruturada em disco (fallback sem Qdrant)

O disco é a fonte da verdade e não depende de infra nenhuma. Layout:

```
~/knowledge-base/
  {project}/
    context.md                      # contexto vivo do projeto (mantido pela skill explorer)
    notes/
      <YYYY-MM-DD>--<slug>.md       # uma nota por arquivo, frontmatter + corpo
    sessions/
      <session_id>.json             # um session record vivo por sessão (mantido por kb-session)
  .qdrant/                          # volume do Qdrant (índice derivado — não ler à mão)
  .venv/                            # ambiente de embedding
```

Como achar notas sem Qdrant:

- **Por data**: os nomes de arquivo começam com a data — `ls` ordenado já é uma
  timeline. Recentes: `ls -1 ~/knowledge-base/{project}/notes/ | sort -r | head`.
- **Por tipo**: grep no frontmatter — `grep -l "^type: decision" ~/knowledge-base/{project}/notes/*.md`.
- **Por assunto**: grep por termos no `title`/`summary`/`entities` do frontmatter;
  leia só os frontmatters (head) antes de abrir corpos.
- **Cross-project**: o mesmo padrão com glob `~/knowledge-base/*/notes/*.md`.

E os session records: grep por termos nos campos `name`/`description`/`resume` dos
JSONs — `grep -l -i "<termo>" ~/knowledge-base/{project}/sessions/*.json` — e ordene
por `updated_at` para privilegiar sessões recentes.

Ao usar o fallback, **diga explicitamente** que a busca foi estrutural (grep/data), não
semântica — e ofereça subir a infra via `kb-infra` se o volume de notas justificar.

## 3. Degrau 3 — Deep search na session memory (via `kb-session`)

Os degraus 1–2 buscam sobre o que foi **destilado** (summaries de notas, resumes de
sessões). Mas nem tudo que foi dito numa sessão virou nota ou entrou no resume — a
resposta pode existir apenas na **memória bruta** do harness. O degrau 3 vai atrás dela.

**Quando descer** (qualquer um destes):

- Os degraus 1–2 não encontraram **nada** relevante e a pergunta tem cheiro de memória
  episódica ("o que falamos sobre X?", "por que decidimos Y naquela conversa?", "qual
  era o erro que apareceu quando tentamos Z?").
- Os degraus 1–2 responderam **parcialmente** — ex.: uma nota cita a decisão mas não o
  raciocínio, ou um session record indica que o tema foi discutido numa sessão sem que
  exista nota sobre ele.
- O usuário pede explicitamente para buscar em sessões passadas.

**Como descer**:

1. Selecione os **session records mais relevantes** para a query — os hits
   `kind: "session"` do degrau 1, ou os JSONs achados no degrau 2. Poucos candidatos,
   ordenados por relevância (2–3 costumam bastar). Se o degrau 1 não retornou **nenhum**
   hit de sessão (ex.: sessions ainda não indexadas), monte os candidatos com a mecânica
   do degrau 2: liste `sessions/` em disco por `updated_at` e grep nos campos
   `name`/`description`/`resume` dos JSONs.
2. Delegue o mergulho ao **playbook de deep search de `kb-session`** (grep dirigido
   sobre o transcript + leitura por janelas ao redor dos hits — nunca o JSONL inteiro),
   passando a query e os candidatos.
3. Incorpore os trechos recuperados à resposta **com a citação de sessão** exigida por
   `kb-session` (session name + session_id + harness).

**Nunca desça silenciosamente**: anuncie que os degraus estruturados não bastaram e que
o deep search foi acionado — e, se nem ele encontrar, diga que a knowledge base e as
sessões registradas não contêm a resposta.

## 4. Resolução de cadeias `supersedes`

Antes de montar a resposta, resolva as cadeias:

1. Para cada nota candidata, verifique se **outra nota a superseda** (alguma nota com
   `supersedes: <id-da-candidata>`). No Qdrant, notas supersedidas já têm
   `archived: true` e são excluídas por padrão; em disco, grep por
   `supersedes: <id>` nos frontmatters.
2. Siga a cadeia até a ponta: **sempre prefira a nota mais recente da cadeia** — ela é
   o conhecimento vigente.
3. As versões antigas são história: cite-as apenas se o usuário pedir a evolução da
   decisão ("por que mudamos?"), deixando claro o que está arquivado.

## 5. Montagem da resposta

- Responda a pergunta em prosa direta, sintetizando o conteúdo das notas — não despeje
  arquivos inteiros.
- **Cite as notas-fonte** ao final, cada uma com título, tipo, data e path absoluto:

```
Fontes:
- [decision] Adoção de OIDC com PKCE (2026-05-12) — ~/knowledge-base/api-gateway/notes/2026-05-12--oidc-pkce.md
- [session] "Refactor da biblioteca portable" (55cb8ac6…, claude-code) — deep search no transcript
```

- **Anuncie o degrau usado** — "via busca semântica", "via navegação em disco (sem
  Qdrant)", "via deep search na sessão X" — sempre, em toda resposta.

- Siga `links_out` das notas encontradas quando enriquecem a resposta (procedimento
  citado por uma decisão, evento que a motivou) — um salto de profundidade, não uma
  travessia do grafo inteiro.
- Se nada relevante foi encontrado, diga claramente — não invente conhecimento que não
  está registrado.

## Regras de execução

1. **Read-only** — recuperação nunca escreve nada, nem em `~/knowledge-base/`.
2. **Filtros no servidor** — project/type/data/archived via payload filter no prefetch,
   nunca filtragem client-side após a fusão.
3. **Cadeias supersedes sempre resolvidas** — nunca apresente conhecimento arquivado
   como vigente (vale para notas; session records são vivos e não têm cadeia).
4. **Toda resposta cita as fontes** — título, tipo, data, path para notas; session
   name + session_id + harness para trechos de sessão.
5. **Escada explícita, nunca silenciosa** — anuncie o degrau que respondeu; a descida
   ao degrau 2 (disco) ou 3 (deep search via `kb-session`) é sempre declarada.
6. **Scripts efêmeros via heredoc** com o venv de `kb-infra` — nunca crie arquivos de
   script no projeto do usuário.
