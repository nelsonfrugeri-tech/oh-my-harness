---
version: 1.0.0
name: kb-infra
description: |
  Sobe, verifica e mantém a infraestrutura da knowledge base: Qdrant local via docker
  (compose embutido nesta skill — container oh-my-harness-qdrant, porta 6333, volume
  persistente em ~/knowledge-base/.qdrant) e o ambiente de embedding BAAI/bge-m3 via
  FlagEmbedding (python, dense 1024-dim + lexical sparse no mesmo forward pass). Cobre
  criação idempotente da collection com named vectors (dense cosine + sparse) e payload
  indexes (created_at, project, kind), health checks (docker up? collection existe?
  modelo responde?), reindex das notas e session records em disco e teardown. Invocada
  pelo agent `knowledge-base` quando a intenção é subir/verificar/derrubar infra — não
  destinada a invocação direta pelo usuário.
type: capability
---

# KB Infra — Infraestrutura da Knowledge Base

Você sobe e mantém a infra que dá busca semântica à knowledge base. Dois componentes:

1. **Qdrant** — vector database local, via docker, com volume persistente.
2. **Embedding** — modelo `BAAI/bge-m3` via `FlagEmbedding` (python), que produz vetor
   **dense 1024-dim** e vetor **lexical sparse** no mesmo forward pass.

Princípios: **idempotência** (rodar duas vezes não quebra nada), **o disco é a fonte da
verdade** (o Qdrant é índice derivado — pode ser destruído e reconstruído a partir de
`~/knowledge-base/`), e **degrade com elegância** (sem docker, reporte o que falta e o
que ainda funciona: escrita e navegação em disco).

> **Modelo de embedding é FIXO** — `BAAI/bge-m3` foi validado e escolhido. Trocá-lo
> exige decisão explícita do usuário (e invalida o índice inteiro: dimensões e scores
> mudam — seria preciso recriar a collection e reindexar tudo).

---

## 1. Qdrant via docker compose

O compose canônico vive **junto desta skill**: `docker-compose.yml` no diretório da
skill (referencie via `${CLAUDE_SKILL_DIR}/docker-compose.yml` para funcionar de
qualquer cwd). Definição:

- Image pinada: `qdrant/qdrant:v1.18.0`
- Container: `oh-my-harness-qdrant`
- Ports: `6333` (HTTP/REST) e `6334` (gRPC)
- Volume persistente: `~/knowledge-base/.qdrant:/qdrant/storage` — o dado do Qdrant
  vive **junto da knowledge base** (global da máquina), nunca no cwd/repo em que o
  usuário estiver. Este é o único desvio deliberado do compose original da era
  oh-my-kb, que montava `./.data/qdrant` relativo ao cwd.
- `restart: unless-stopped` — sobrevive a reboot da máquina.

### Subida (up)

```bash
mkdir -p ~/knowledge-base/.qdrant
docker compose -f "${CLAUDE_SKILL_DIR}/docker-compose.yml" up -d
```

Idempotente: se o container já está rodando, o compose confirma e não recria.

Se o daemon do docker não responder, diagnostique antes de falhar: no macOS/Windows o
Docker Desktop provavelmente não está aberto; no Linux, `systemctl start docker` ou
usuário fora do grupo `docker`. Reporte a causa e o remédio — não apenas o erro.

### Health check

```bash
curl -sf http://localhost:6333/healthz && echo OK
```

Falhou logo após o `up`? Aguarde e tente de novo por até ~30s (o Qdrant demora alguns
segundos para aceitar conexões). Continuou falhando: `docker logs oh-my-harness-qdrant --tail 20`.

### Teardown

```bash
docker compose -f "${CLAUDE_SKILL_DIR}/docker-compose.yml" down
```

O volume em `~/knowledge-base/.qdrant` **não** é apagado — os dados sobrevivem ao
teardown e o próximo `up` volta com o índice intacto. Apagar o volume é ação destrutiva:
só com confirmação explícita do usuário (e é recuperável via reindex, pois o disco é a
fonte da verdade).

---

## 2. Ambiente de embedding — `BAAI/bge-m3` via FlagEmbedding

O embedding roda em python num venv **dedicado à knowledge base**, fora de qualquer
projeto: `~/knowledge-base/.venv`.

### Instalação (idempotente)

```bash
cd ~/knowledge-base
test -d .venv || uv venv .venv
uv pip install --python .venv/bin/python -U FlagEmbedding qdrant-client
```

Sem `uv` na máquina, degrade para `python3 -m venv .venv && .venv/bin/pip install -U FlagEmbedding qdrant-client`.

Na primeira execução o modelo (~2 GB) é baixado para o cache do Hugging Face — avise o
usuário que o primeiro run demora.

### Uso do modelo — padrão obrigatório

O desenho validado na era oh-my-kb (preserve-o):

- **Lazy-load**: instancie `BGEM3FlagModel` uma única vez, no primeiro uso — nunca no
  import. Construção do wrapper é barata; o load do modelo é caro.
- **Um forward pass, dois vetores**: `return_dense=True, return_sparse=True,
  return_colbert_vecs=False`.
- **Adaptação do sparse ao Qdrant**: `lexical_weights` vem como dict
  `{token_id: weight}`; converta para o shape paralelo `indices`/`values` do Qdrant.

```python
from FlagEmbedding import BGEM3FlagModel

_model = None  # lazy singleton — loading is the expensive part

def embed(texts: list[str]) -> list[dict]:
    global _model
    if _model is None:
        _model = BGEM3FlagModel(
            "BAAI/bge-m3", use_fp16=False,
            return_dense=True, return_sparse=True, return_colbert_vecs=False,
        )
    out = _model.encode(texts, return_dense=True, return_sparse=True)
    return [
        {
            "dense": out["dense_vecs"][i].tolist(),  # 1024-dim
            "sparse": {
                "indices": [int(t) for t in out["lexical_weights"][i]],
                "values": [float(w) for w in out["lexical_weights"][i].values()],
            },
        }
        for i in range(len(texts))
    ]
```

Scripts que usam esse padrão rodam via heredoc no `Bash`
(`~/knowledge-base/.venv/bin/python - <<'EOF' ... EOF`) — nunca crie arquivos de script
dentro do projeto do usuário.

### Health check do modelo

Embed de um texto curto e verificação do shape: dense com `len == 1024` e sparse com
`len(indices) == len(values) > 0`. Se o import de `FlagEmbedding` falhar, o venv não
está instalado — volte à instalação.

---

## 3. Collection do Qdrant — desenho espelhado da era oh-my-kb

Uma collection única, `knowledge-base`, em layout de hybrid search com **named
vectors**, com os pontos de todos os projetos separados por payload `project` e dois
**kinds** de ponto convivendo na mesma collection: notas (`kind: "note"`, escritas por
`kb-write`) e session records (`kind: "session"`, mantidos por `kb-session`):

| Item | Valor |
|---|---|
| Collection | `knowledge-base` |
| Named vector dense | `"dense"` — size 1024, distance **Cosine** (casa com o bge-m3) |
| Named vector sparse | `"sparse"` — `SparseVectorParams()` |
| Payload index | `created_at` → `DATETIME` (permite `order_by`/filtros temporais sem full-scan) |
| Payload index | `project` → `KEYWORD` (acelera filtro por projeto) |
| Payload index | `kind` → `KEYWORD` (separa notas de session records no filtro) |
| Payload por ponto (`kind: "note"`) | `kind`, `id`, `title`, `type`, `project`, `created_at`, `summary`, `path`, `supersedes`, `archived` |
| Payload por ponto (`kind: "session"`) | `kind`, `harness`, `session_id`, `project`, `name`, `created_at`, `updated_at`, `transcript_path` |

O payload de session **intencionalmente não carrega** `description`/`resume` nem `path`:
o disco é a fonte da verdade — um hit de sessão leva à leitura do JSON em
`~/knowledge-base/<project>/sessions/<session_id>.json` (path derivável do payload).

Criação convergente (idempotente — o `if not exists` protege a collection; os payload
indexes são reaplicados sempre, pois `create_payload_index` é idempotente no servidor):

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, SparseVectorParams, VectorParams

client = QdrantClient(url="http://localhost:6333")
if not client.collection_exists("knowledge-base"):
    client.create_collection(
        collection_name="knowledge-base",
        vectors_config={"dense": VectorParams(size=1024, distance=Distance.COSINE)},
        sparse_vectors_config={"sparse": SparseVectorParams()},
    )
client.create_payload_index("knowledge-base", "created_at", field_schema=PayloadSchemaType.DATETIME)
client.create_payload_index("knowledge-base", "project", field_schema=PayloadSchemaType.KEYWORD)
client.create_payload_index("knowledge-base", "kind", field_schema=PayloadSchemaType.KEYWORD)
```

---

## 4. Reindex — reconciliar Qdrant com o disco

Quando notas ou session records foram escritos com o Qdrant fora do ar (indexação
pendente), ou o volume foi perdido, reconstrua o índice a partir do disco:

1. Liste as notas (`~/knowledge-base/*/notes/*.md`) **e** os session records
   (`~/knowledge-base/*/sessions/*.json`).
2. Para cada nota, extraia o frontmatter (`id`, `title`, `type`, `project`,
   `created_at`, `summary`, `supersedes`, `archived`) e embede o **summary**
   (dense + sparse), com payload `kind: "note"`. Para cada session record, embede
   `name + "\n" + description + "\n" + resume` com payload `kind: "session"` (campos
   em `kb-session`).
3. Faça upsert no Qdrant usando o UUID como point id (`id` da nota; `session_id` do
   record) — upsert por id é naturalmente idempotente: reindexar duas vezes não
   duplica nada.
4. Reporte: N notas + N sessions em disco, N indexados, divergências encontradas.

---

## 5. Health check completo (ordem de verificação)

Execute nesta ordem e reporte o primeiro elo quebrado com o remédio:

1. **Docker daemon** responde? (`docker info`)
2. **Container** `oh-my-harness-qdrant` rodando? (`docker ps`)
3. **Qdrant** responde? (`curl -sf http://localhost:6333/healthz`)
4. **Collection** `knowledge-base` existe com os named vectors certos?
5. **Venv + modelo** respondem? (embed de teste, shape 1024/sparse)

Para o gate rápido que o agent `knowledge-base` roda antes de write/retrieval, o passo
3 sozinho basta.

## Regras de execução

1. **Idempotência em tudo** — up, instalação, criação de collection, reindex: rodar
   duas vezes nunca quebra nem duplica.
2. **Nada destrutivo sem confirmação** — apagar volume, deletar collection, recriar
   índice do zero: só com pedido explícito do usuário.
3. **Escrita só em `~/knowledge-base/`** — nunca no repo do usuário; scripts efêmeros
   via heredoc.
4. **Modelo fixo** — `BAAI/bge-m3`; qualquer troca é decisão explícita do usuário.
5. **Versões pinadas** — image `qdrant/qdrant:v1.18.0` no compose; para verificar se
   existe versão mais nova, use a capability `web` e **proponha** o bump, nunca aplique
   sozinho.
6. **Degrade com elegância** — sem docker/venv, diga exatamente o que falta, o que
   ainda funciona (disco) e o que ficou pendente (indexação/busca semântica).
