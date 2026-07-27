# graphify reference: exports extras e benchmark

Carregue isto quando o usuário passou uma das export flags (`--wiki`, `--neo4j`, `--neo4j-push`, `--falkordb`, `--falkordb-push`, `--svg`, `--graphml`, `--mcp`), ou quando o corpus é grande o bastante para o token-reduction benchmark. Cada passo roda apenas para sua própria flag.

### Step 6b - Wiki (só se a flag --wiki)

**Rode este passo apenas se `--wiki` foi explicitamente dado no comando original.**

Rode-o antes do Step 9 (cleanup) para que `.graphify_labels.json` ainda esteja disponível.

```bash
graphify export wiki
```

### Step 7 - Neo4j export (só se a flag --neo4j ou --neo4j-push)

**Se `--neo4j`** - gere um Cypher file para import manual:

```bash
graphify export neo4j
```

**Se `--neo4j-push <uri>`** - faça push direto para uma instância Neo4j rodando. Peça as credenciais ao usuário se não forem fornecidas:

```bash
graphify export neo4j --push bolt://localhost:7687 --user neo4j --password PASSWORD
```

URI default é `bolt://localhost:7687`, user default é `neo4j`. Usa MERGE - seguro re-rodar sem criar duplicatas.

### Step 7a - FalkorDB export (só se a flag --falkordb ou --falkordb-push)

**Se `--falkordb`** - gere um Cypher file. Os statements são OpenCypher, mas o `GRAPH.QUERY` do FalkorDB roda um statement por vez (sem bulk script import como o `cypher-shell` do Neo4j), então prefira `--falkordb-push` para carregar um grafo. Use isto apenas quando você quer o artefato portável `cypher.txt`:

```bash
graphify export falkordb
```

**Se `--falkordb-push <uri>`** - faça push direto para uma instância FalkorDB rodando. Credenciais são opcionais; pergunte ao usuário apenas se a instância requer auth:

```bash
graphify export falkordb --push falkordb://localhost:6379
```

URI default é `falkordb://localhost:6379` (o scheme é informativo - `redis://` ou um `host:port` simples também funcionam), auth é opcional, e o target graph faz default para `graphify`. Usa MERGE - seguro re-rodar sem criar duplicatas.

### Step 7b - SVG export (só se a flag --svg)

```bash
graphify export svg
```

### Step 7c - GraphML export (só se a flag --graphml)

```bash
graphify export graphml
```

### Step 7d - MCP server (só se a flag --mcp)

```bash
$(cat graphify-out/.graphify_python) -m graphify.serve graphify-out/graph.json
```

Isto inicia um stdio MCP server que expõe as tools: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`. Adicione ao Claude Desktop ou qualquer MCP-compatible agent orchestrator para que outros agents consultem o grafo ao vivo.

Para configurar no Claude Desktop, adicione a `claude_desktop_config.json`. O Claude Desktop não pode rodar `$(...)`, e sob `uv tool install` o `python3` do sistema não consegue importar graphify — então sete `command` para o **absolute interpreter path** impresso por `cat graphify-out/.graphify_python`:
```json
{
  "mcpServers": {
    "graphify": {
      "command": "<absolute path from: cat graphify-out/.graphify_python>",
      "args": ["-m", "graphify.serve", "/absolute/path/to/graphify-out/graph.json"]
    }
  }
}
```

### Step 8 - Token reduction benchmark (só se total_words > 5000)

Se `total_words` de `graphify-out/.graphify_detect.json` é maior que 5,000, rode:

```bash
graphify benchmark
```

Imprima o output diretamente no chat. Se `total_words <= 5000`, pule silenciosamente - o valor do grafo é clareza estrutural, não compressão de tokens, para corpora pequenos.
