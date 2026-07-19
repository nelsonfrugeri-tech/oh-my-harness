---
version: 1.0.0
name: kb-retrieval
description: |
  Recuperação de conhecimento da knowledge base: busca semântica híbrida no Qdrant
  (query → embedding BAAI/bge-m3 dense+sparse → dois prefetch fundidos com Reciprocal
  Rank Fusion), filtros por type/project/data via payload, navegação estruturada dos
  diretórios ~/knowledge-base/ como fallback sem Qdrant, resolução de cadeias
  supersedes (sempre preferir a nota mais recente da cadeia) e montagem de resposta com
  citação das notas-fonte. Invocada pelo agent `knowledge-base` quando a intenção é
  buscar/recuperar conhecimento — também usada por kb-write para descobrir links.
type: capability
---

# KB Retrieval — Recuperação de Conhecimento

Você responde perguntas a partir da knowledge base em `~/knowledge-base/`, com duas
vias: **busca semântica** (Qdrant saudável) e **navegação estruturada em disco**
(fallback sempre disponível). Toda resposta cita as notas-fonte.

---

## 1. Busca semântica híbrida (via principal)

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

## 2. Navegação estruturada em disco (fallback sem Qdrant)

O disco é a fonte da verdade e não depende de infra nenhuma. Layout:

```
~/knowledge-base/
  {project}/
    context.md                      # contexto vivo do projeto (mantido pela skill explorer)
    notes/
      <YYYY-MM-DD>--<slug>.md       # uma nota por arquivo, frontmatter + corpo
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

Ao usar o fallback, **diga explicitamente** que a busca foi estrutural (grep/data), não
semântica — e ofereça subir a infra via `kb-infra` se o volume de notas justificar.

## 3. Resolução de cadeias `supersedes`

Antes de montar a resposta, resolva as cadeias:

1. Para cada nota candidata, verifique se **outra nota a superseda** (alguma nota com
   `supersedes: <id-da-candidata>`). No Qdrant, notas supersedidas já têm
   `archived: true` e são excluídas por padrão; em disco, grep por
   `supersedes: <id>` nos frontmatters.
2. Siga a cadeia até a ponta: **sempre prefira a nota mais recente da cadeia** — ela é
   o conhecimento vigente.
3. As versões antigas são história: cite-as apenas se o usuário pedir a evolução da
   decisão ("por que mudamos?"), deixando claro o que está arquivado.

## 4. Montagem da resposta

- Responda a pergunta em prosa direta, sintetizando o conteúdo das notas — não despeje
  arquivos inteiros.
- **Cite as notas-fonte** ao final, cada uma com título, tipo, data e path absoluto:

```
Fontes:
- [decision] Adoção de OIDC com PKCE (2026-05-12) — ~/knowledge-base/api-gateway/notes/2026-05-12--oidc-pkce.md
```

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
   como vigente.
4. **Toda resposta cita as fontes** — título, tipo, data, path.
5. **Fallback explícito** — sem Qdrant, navegue o disco e declare que a busca não foi
   semântica.
6. **Scripts efêmeros via heredoc** com o venv de `kb-infra` — nunca crie arquivos de
   script no projeto do usuário.
