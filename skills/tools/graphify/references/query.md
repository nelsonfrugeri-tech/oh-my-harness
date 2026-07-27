# graphify reference: query, path, explain

Carregue isto quando o usuário faz uma pergunta contra um grafo existente, ou roda `/graphify path` ou `/graphify explain`. O query stub do core aponta para cá para o fluxo completo de traversal. Esses fluxos usam a CLI `graphify query` quando ela está disponível e caem para uma NetworkX traversal inline caso contrário.

Dois modos de traversal - escolha com base na pergunta:

| Mode | Flag | Best for |
|------|------|----------|
| BFS (default) | _(none)_ | "What is X connected to?" - broad context, nearest neighbors first |
| DFS | `--dfs` | "How does X reach Y?" - trace a specific chain or dependency path |

Primeiro verifique que o grafo existe:
```bash
$(cat graphify-out/.graphify_python) -c "
from pathlib import Path
if not Path('graphify-out/graph.json').exists():
    print('ERROR: No graph found. Run /graphify <path> first to build the graph.')
    raise SystemExit(1)
"
```
Se falhar, pare e diga ao usuário para rodar `/graphify <path>` primeiro.

### Step 0 — Constrained query expansion (OBRIGATÓRIO antes da traversal)

A CLI `query` do graphify casa nodes via case-folded substring + IDF — não há **stemming, synonyms, nem cross-language match** dentro do binário, e o inline fallback abaixo casa da mesma forma. Se a pergunta do usuário usa uma linguagem diferente ou vocabulário de domínio diferente dos labels do grafo (usuário diz "обработчик" / grafo diz "handler"; usuário diz "authentication" / grafo diz "Guardian"), o literal matcher retorna 0 hits e a resposta colapsa a ruído.

Corrija isso **sem inventar tokens** expandindo a query contra o vocabulário real do grafo primeiro:

1. Extraia o token vocabulary dos node labels:
```bash
$(cat graphify-out/.graphify_python) -c "
import json, re
from pathlib import Path
data = json.loads(Path('graphify-out/graph.json').read_text(encoding='utf-8'))
vocab = set()
for n in data['nodes']:
    for c in re.findall(r'[^\W\d_]+', n.get('label','') or '', re.UNICODE):
        parts = re.findall(r'[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+', c) or [c]
        for p in parts:
            t = p.lower()
            if 3 <= len(t) <= 30:
                vocab.add(t)
Path('graphify-out/.vocab.txt').write_text('\n'.join(sorted(vocab)), encoding='utf-8')
print(f'vocab: {len(vocab)} tokens')
"
```

2. Leia `graphify-out/.vocab.txt`. Então para a pergunta do usuário, selecione **até 12 tokens desta lista exata** que semanticamente casam com a intenção da query. Hard constraints:
   - Você DEVE escolher apenas tokens presentes no vocabulary file. NÃO invente tokens.
   - Se um conceito da query não tem token plausível no vocab, pule-o — não substitua por um near-synonym da memória de treino.
   - Se **nenhum** vocab token casa com a query, output uma lista vazia e diga ao usuário que o corpus não tem vocabulário relevante para esta pergunta. Não fabrique uma busca.
   - Traduza cross-language: Russo "аутентификация" → procure por `auth`, `credential`, `token`, `security` SE presente no vocab.
   - Morfologia: "handlers" mapeia para `handler` SE presente; "todos" mapeia para `todo` SE presente.

3. Imprima a seleção explicitamente ao usuário antes de rodar a query, para que a expansão seja auditável:
```
Query expanded to (from graph vocab, N tokens): [token1, token2, ...]
```
Se a lista está vazia, diga isso claramente e pare — não prossiga para a traversal.

### Step 1 — Traversal

Construa a **expanded query string** juntando os tokens selecionados com espaços. Use essa string como `QUESTION` abaixo — NÃO a pergunta original do usuário. (A pergunta original é preservada apenas para `save-result` no final.)

Prefira a CLI quando instalada:
```bash
graphify query "QUESTION"
# or: graphify query "QUESTION" --dfs --budget 3000
```

Se a CLI estiver indisponível, carregue `graphify-out/graph.json` e rode a traversal inline:

1. Encontre os 1-3 nodes cujo label melhor casa com os expanded tokens.
2. Rode a traversal apropriada a partir de cada starting node.
3. Leia o subgraph - node labels, edge relations, confidence tags, source locations.
4. Responda usando **apenas** o que o grafo contém. Cite `source_location` ao referenciar um fato específico.
5. Se o grafo carece de informação suficiente, diga isso - não alucine edges.

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from networkx.readwrite import json_graph
import networkx as nx
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text(encoding='utf-8'))
G = json_graph.node_link_graph(data, edges='links')

question = 'QUESTION'
mode = 'MODE'  # 'bfs' or 'dfs'
terms = [t.lower() for t in question.split() if len(t) >= 3]  # match the vocab threshold; keeps api/jwt/ios (#1392)

# Find best-matching start nodes
scored = []
for nid, ndata in G.nodes(data=True):
    label = ndata.get('label', '').lower()
    score = sum(1 for t in terms if t in label)
    if score > 0:
        scored.append((score, nid))
scored.sort(reverse=True)
start_nodes = [nid for _, nid in scored[:3]]

if not start_nodes:
    print('No matching nodes found for query terms:', terms)
    sys.exit(0)

subgraph_nodes = set()
subgraph_edges = []

if mode == 'dfs':
    # DFS: follow one path as deep as possible before backtracking.
    # Depth-limited to 6 to avoid traversing the whole graph.
    visited = set()
    stack = [(n, 0) for n in reversed(start_nodes)]
    while stack:
        node, depth = stack.pop()
        if node in visited or depth > 6:
            continue
        visited.add(node)
        subgraph_nodes.add(node)
        for neighbor in G.neighbors(node):
            if neighbor not in visited:
                stack.append((neighbor, depth + 1))
                subgraph_edges.append((node, neighbor))
else:
    # BFS: explore all neighbors layer by layer up to depth 3.
    frontier = set(start_nodes)
    subgraph_nodes = set(start_nodes)
    for _ in range(3):
        next_frontier = set()
        for n in frontier:
            for neighbor in G.neighbors(n):
                if neighbor not in subgraph_nodes:
                    next_frontier.add(neighbor)
                    subgraph_edges.append((n, neighbor))
        subgraph_nodes.update(next_frontier)
        frontier = next_frontier

# Token-budget aware output: rank by relevance, cut at budget (~4 chars/token)
token_budget = BUDGET  # default 2000
char_budget = token_budget * 4

# Score each node by term overlap for ranked output
def relevance(nid):
    label = G.nodes[nid].get('label', '').lower()
    return sum(1 for t in terms if t in label)

ranked_nodes = sorted(subgraph_nodes, key=relevance, reverse=True)

lines = [f'Traversal: {mode.upper()} | Start: {[G.nodes[n].get(\"label\",n) for n in start_nodes]} | {len(subgraph_nodes)} nodes']
for nid in ranked_nodes:
    d = G.nodes[nid]
    lines.append(f'  NODE {d.get(\"label\", nid)} [src={d.get(\"source_file\",\"\")} loc={d.get(\"source_location\",\"\")}]')
for u, v in subgraph_edges:
    if u in subgraph_nodes and v in subgraph_nodes:
        _raw = G[u][v]; d = next(iter(_raw.values()), {}) if isinstance(G, nx.MultiGraph) else _raw
        lines.append(f'  EDGE {G.nodes[u].get(\"label\",u)} --{d.get(\"relation\",\"\")} [{d.get(\"confidence\",\"\")}]--> {G.nodes[v].get(\"label\",v)}')

output = '\n'.join(lines)
if len(output) > char_budget:
    output = output[:char_budget] + f'\n... (truncated at ~{token_budget} token budget - use --budget N for more)'
print(output)
"
```

Substitua `QUESTION` pela **expanded** query string, `MODE` por `bfs` ou `dfs`, e `BUDGET` pelo token budget (default `2000`, ou o que `--budget N` especificar). Então responda com base no subgraph output acima, usando apenas o que o grafo contém.

Depois de escrever a resposta, salve-a de volta no grafo para melhorar queries futuras. Inclua os expanded tokens dentro do texto `--answer` (ex.: `"Expanded from original query via vocab: [tokens]. Then traversed..."`) para que o próximo `--update` extraia o expansion history como um graph node:

```bash
$(cat graphify-out/.graphify_python) -m graphify save-result --question "ORIGINAL_QUESTION" --answer "ANSWER" --type query --nodes NODE1 NODE2
```

Substitua `ORIGINAL_QUESTION` pela pergunta verbatim do usuário, `ANSWER` pelo seu texto de resposta completo (contendo o expanded-token trace), `NODE1 NODE2` pela lista de node labels que você citou. Isto fecha o feedback loop: o próximo `--update` vai extrair este Q&A como um node no grafo.

**Work memory (self-improving loop).** Adicione um `--outcome` para que sessões futuras aprendam com esta — apende `--outcome useful|dead_end|corrected` ao comando `save-result` (e `--correction "the right answer"` ao corrigir):

- `useful` — os cited nodes responderam bem a pergunta (eles se tornam *preferred sources*).
- `dead_end` — a pergunta/path não levou a lugar nenhum; não re-derive isso na próxima vez.
- `corrected` — a saved answer estava errada; `--correction` registra o que estava certo.

No **início** do graph work, refresh e leia as lessons: rode `graphify reflect --if-stale` (barato, determinístico, sem LLM; `--if-stale` o torna um no-op quando `LESSONS.md` já está mais novo que todos os inputs, ex.: quando o git hook acabou de refresh). então leia `graphify-out/reflections/LESSONS.md`. Ele lista **preferred sources** (comece por aí), **known dead ends** (pule-os), e **corrections** anteriores. Rodar `reflect` você mesmo mantém as lessons atuais mesmo sem o git hook instalado; se o post-commit hook *está* instalado, `--if-stale` significa que sua run de início-de-sessão custa quase nada.

---

## Para /graphify path

Encontre o shortest path entre dois named concepts no grafo. Prefira a CLI quando instalada:

```bash
graphify path "NODE_A" "NODE_B"
```

Se a CLI estiver indisponível, rode-o inline:

```bash
$(cat graphify-out/.graphify_python) -c "
import json, sys
import networkx as nx
from networkx.readwrite import json_graph
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text(encoding='utf-8'))
G = json_graph.node_link_graph(data, edges='links')

a_term = 'NODE_A'
b_term = 'NODE_B'

def find_node(term):
    term = term.lower()
    scored = sorted(
        [(sum(1 for w in term.split() if w in G.nodes[n].get('label','').lower()), n)
         for n in G.nodes()],
        reverse=True
    )
    return scored[0][1] if scored and scored[0][0] > 0 else None

src = find_node(a_term)
tgt = find_node(b_term)

if not src or not tgt:
    print(f'Could not find nodes matching: {a_term!r} or {b_term!r}')
    sys.exit(0)

try:
    path = nx.shortest_path(G, src, tgt)
    print(f'Shortest path ({len(path)-1} hops):')
    for i, nid in enumerate(path):
        label = G.nodes[nid].get('label', nid)
        if i < len(path) - 1:
            _raw = G[nid][path[i+1]]; edge = next(iter(_raw.values()), {}) if isinstance(G, nx.MultiGraph) else _raw
            rel = edge.get('relation', '')
            conf = edge.get('confidence', '')
            print(f'  {label} --{rel}--> [{conf}]')
        else:
            print(f'  {label}')
except nx.NetworkXNoPath:
    print(f'No path found between {a_term!r} and {b_term!r}')
except nx.NodeNotFound as e:
    print(f'Node not found: {e}')
"
```

Substitua `NODE_A` e `NODE_B` pelos concept names reais do usuário. Então explique o path em linguagem clara - o que cada hop significa, por que é significativo.

Depois de escrever a explicação, salve-a de volta:

```bash
$(cat graphify-out/.graphify_python) -m graphify save-result --question "Path from NODE_A to NODE_B" --answer "ANSWER" --type path_query --nodes NODE_A NODE_B
```

---

## Para /graphify explain

Dê uma explicação em linguagem clara de um único node - tudo conectado a ele. Prefira a CLI quando instalada:

```bash
graphify explain "NODE_NAME"
```

Se a CLI estiver indisponível, rode-o inline:

```bash
$(cat graphify-out/.graphify_python) -c "
import json, sys
import networkx as nx
from networkx.readwrite import json_graph
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text(encoding='utf-8'))
G = json_graph.node_link_graph(data, edges='links')

term = 'NODE_NAME'
term_lower = term.lower()

# Find best matching node
scored = sorted(
    [(sum(1 for w in term_lower.split() if w in G.nodes[n].get('label','').lower()), n)
     for n in G.nodes()],
    reverse=True
)
if not scored or scored[0][0] == 0:
    print(f'No node matching {term!r}')
    sys.exit(0)

nid = scored[0][1]
data_n = G.nodes[nid]
print(f'NODE: {data_n.get(\"label\", nid)}')
print(f'  source: {data_n.get(\"source_file\",\"unknown\")}')
print(f'  type: {data_n.get(\"file_type\",\"unknown\")}')
print(f'  degree: {G.degree(nid)}')
print()
print('CONNECTIONS:')
for neighbor in G.neighbors(nid):
    _raw = G[nid][neighbor]; edge = next(iter(_raw.values()), {}) if isinstance(G, nx.MultiGraph) else _raw
    nlabel = G.nodes[neighbor].get('label', neighbor)
    rel = edge.get('relation', '')
    conf = edge.get('confidence', '')
    src_file = G.nodes[neighbor].get('source_file', '')
    print(f'  --{rel}--> {nlabel} [{conf}] ({src_file})')
"
```

Substitua `NODE_NAME` pelo concept que o usuário perguntou. Então escreva uma explicação de 3-5 frases sobre o que este node é, ao que ele conecta, e por que essas conexões são significativas. Use as source locations como citações.

Depois de escrever a explicação, salve-a de volta:

```bash
$(cat graphify-out/.graphify_python) -m graphify save-result --question "Explain NODE_NAME" --answer "ANSWER" --type explain --nodes NODE_NAME
```
