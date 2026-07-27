# graphify reference: GitHub clone e cross-repo merge

Carregue isto quando o usuário passou uma ou mais URLs `https://github.com/...`, ou nomeou vários subfolders locais para fazer merge num único grafo.

### Step 0 - Clonar repo(s) do GitHub (só se uma GitHub URL foi dada)

**Repo único:**
```bash
LOCAL_PATH=$(graphify clone <github-url> [--branch <branch>])
# Use LOCAL_PATH as the target for all subsequent steps
```

**Múltiplos repos (cross-repo graph):**
```bash
# Clone each repo, run the full pipeline on each, then merge
graphify clone <url1>   # → ~/.graphify/repos/<owner1>/<repo1>
graphify clone <url2>   # → ~/.graphify/repos/<owner2>/<repo2>
# Run /graphify on each local path to produce their graph.json files
# Then merge:
graphify merge-graphs \
  ~/.graphify/repos/<owner1>/<repo1>/graphify-out/graph.json \
  ~/.graphify/repos/<owner2>/<repo2>/graphify-out/graph.json \
  --out graphify-out/cross-repo-graph.json
```

O graphify clona em `~/.graphify/repos/<owner>/<repo>` e reutiliza clones existentes em runs repetidas. Cada node no grafo merged carrega um atributo `repo` para que você possa filtrar por origem.

**Múltiplos subfolders locais (monorepo ou multi-service layout):**

O pipeline da skill escreve todos os outputs intermediários e finais em `graphify-out/` no current working directory. Rodar a skill em cada subfolder separadamente vai clobber o mesmo output dir. Em vez disso, use a CLI diretamente para cada subfolder — ela coloca `graphify-out/` *dentro* do path escaneado:

```bash
graphify extract ./core/     # → ./core/graphify-out/graph.json
graphify extract ./service/  # → ./service/graphify-out/graph.json
graphify extract ./platform/ # → ./platform/graphify-out/graph.json
# Add --backend gemini|kimi|openai|deepseek|claude-cli depending on which API key you have set

# Then merge at the project root:
graphify merge-graphs \
  ./core/graphify-out/graph.json \
  ./service/graphify-out/graph.json \
  ./platform/graphify-out/graph.json \
  --out graphify-out/graph.json
```

Uma vez que `graphify-out/graph.json` existe, o fast path acima assume: qualquer pergunta sobre o codebase roda `graphify query` diretamente no grafo merged — sem re-extração, sem size gate.
