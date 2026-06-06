# oh-my-kb

A programmatic, agnostic knowledge base exposed via MCP. Notes live as plain markdown on disk
and are indexed in Qdrant for **hybrid search** (dense + sparse via bge-m3) plus graph
navigation (`links_out`) and temporal recall (`created_at`). The harness never reads files
directly — it calls MCP tools; the tools handle embedding, retrieval and file I/O.

The knowledge base is "agnostic" in two senses: it is not tied to any particular AI harness
(Claude Code, Claude Desktop, or any MCP-compatible client), and it imposes no domain model
on the user — any kind of knowledge fits inside the five note types.

---

## Prerequisites

| Tool | Why |
|------|-----|
| Python 3.12+ | Required by the package |
| [uv](https://docs.astral.sh/uv/) | Dependency and virtualenv management |
| Docker + Docker Compose | Runs the local Qdrant instance |
| `make` | Wraps every common workflow |

---

## Onboarding

### 1. Clone and install

```bash
git clone https://github.com/nelsonfrugeri-tech/oh-my-kb.git
cd oh-my-kb
make install          # uv sync — creates .venv and installs all deps
```

### 2. Start Qdrant and provision the default universe

```bash
docker compose up -d  # starts Qdrant on localhost:6333
omk install           # brings Qdrant up (idempotent), caches bge-m3,
                      # creates the 'default' universe at ~/oh-my-kb/default/
```

`omk install` is idempotent: running it again just confirms the current state.

The first run downloads ~2 GB of bge-m3 model weights into `~/.cache/huggingface`.
Subsequent runs reuse the cache — model loading adds ~5 s to the first MCP request.

### 3. Connect your harness

**Option A — `omk bootstrap` (automatic, recommended)**

If you are using Claude Code or Claude Desktop:

```bash
omk bootstrap --harness claude-code   # injects the kb-mcp rules block into CLAUDE.md
```

This command (implemented in `oh_my_kb/agents/bootstrap.py`) writes the MCP server
configuration and the usage rules for all five tools into your project's `CLAUDE.md`.
It is idempotent — re-running replaces the block in place.

**Option B — manual configuration**

If `omk bootstrap` does not support your harness yet, add the MCP server by hand:

```bash
# Claude Code (CLI):
claude mcp add o-kb-mcp -- uv run o-kb-mcp
```

Then add a rules block to your `CLAUDE.md` (or equivalent) instructing the assistant
to use the five tools before answering knowledge-related questions:

```
## oh-my-kb — knowledge base rules

Before answering any question that may be covered by the knowledge base:
1. Call kb_search with a natural-language query (or kb_tree for structural exploration).
2. Call kb_expand on any promising hit to read the full note body.
3. Call kb_recent when the question is about recency or time windows.
4. Call kb_write to record every significant decision, event, or procedure.

Read skill://scribe/SKILL.md before every kb_write call.
```

### 4. Using the knowledge base

The assistant calls the MCP tools on your behalf. You do not interact with `omk`
or `o-kb-mcp` directly during a session — just ask questions or give instructions,
and the harness will search, navigate, and write notes as needed.

---

## Universe management

A **universe** is an isolated knowledge domain: one Qdrant collection +
one directory of markdown files. Use multiple universes for completely
separate contexts (e.g. `work` vs `personal`).

```bash
omk universe create <name>        # create a new universe
omk universe list                 # list configured universes (* = active)
omk universe use <name>           # switch active universe
```

Config lives at `~/.config/oh-my-kb/config.toml` (XDG hidden).
Note data lives at `~/oh-my-kb/<universe>/` (visible, no dotfile — easy to
open in an editor or commit to git).

---

## MCP tools — reference

Five tools are exposed by the MCP server. Each has a specific purpose;
the rule of thumb is **navigate vs. search vs. temporal**:

| Tool | When to use |
|------|-------------|
| `kb_write` | Record a new decision, event, procedure, reference, or conversation. |
| `kb_search` | Find notes by semantic similarity — "what do we know about X?" |
| `kb_tree` | Get a structural map of the universe — "what exists in project Y?" |
| `kb_expand` | Open a specific note in full and follow its outbound links. |
| `kb_recent` | Recall notes by creation time — "what happened last week?" |

### Navigate vs. search vs. recent

- **`kb_search`** — use when you have a topic or question and want the most
  semantically relevant notes regardless of when they were created.
- **`kb_tree`** — use on small or well-structured universes where you want
  a bird's-eye view grouped by project. Returns only payload data (no file reads).
- **`kb_expand`** — use after search or tree to read the full body of a note
  and see what it links to. Follows one hop of the knowledge graph per call.
- **`kb_recent`** — use when recency matters: "last 7 days", "latest decisions
  on project X". Supports optional `topic` for semantic ranking within the window.

### Accepted `since` formats for `kb_recent`

| Format | Example |
|--------|---------|
| Relative days | `"7d"` |
| Relative weeks | `"2w"` |
| Relative hours | `"24h"` |
| Relative minutes | `"90m"` |
| ISO date | `"2026-06-01"` |
| ISO datetime (tz-aware) | `"2026-06-01T00:00:00+00:00"` |

---

## Directory layout

```
oh-my-kb/
  oh_my_kb/
    core/        # pure domain — Note model, serialization, slug
    storage/     # Qdrant adapter
    embedding/   # bge-m3 via FlagEmbedding (abstract Embedder interface)
    services/    # Indexer, SearchService, NavigationService, RecentService, reindex
    cli/         # omk CLI — install, universe, bootstrap, reindex
    mcp/
      server.py  # MCP entry point (o-kb-mcp)
      tools/     # kb_write, kb_search, kb_tree, kb_expand, kb_recent
      skills/    # scribe playbook (SKILL.md + template.md per locale)
  tests/
  docker-compose.yml
  Makefile
```

Config: `~/.config/oh-my-kb/config.toml`
Data:   `~/oh-my-kb/<universe>/`

---

## Scribe skill

The MCP server exposes a **scribe playbook** as resources the harness can read:

- `skill://scribe/SKILL.md` — when to create vs. supersede, how to pick `type`,
  how to write a summary that retrieves well, how to extract `entities` and
  discover `links_out`.
- `skill://scribe/template.md` — the required body structure per note type.

The harness should read `skill://scribe/SKILL.md` **before every `kb_write`** call.
Server-side validation enforces a summary length of 200–800 chars and rejects
summaries identical to the title; violations return a clear tool error.

---

## Moving files and `omk reindex`

The Indexer keeps Qdrant and disk in sync when notes are written through
`kb_write`. If you move or rename `.md` files manually (e.g. to reorganise
project directories), the Qdrant payload will have a stale path.

Run `omk reindex` to reconcile:

```bash
omk reindex                    # reindex active universe
omk reindex --universe work    # reindex a specific universe
```

`omk reindex` is **fully idempotent** — it is safe to run multiple times.
What it does:

1. Scans every `.md` under the universe's notes directory (recursively).
2. Parses each file, re-embeds the summary, and upserts the Qdrant point
   with the **current path** (correcting any stale entries).
3. Removes Qdrant points whose `.md` no longer exists on disk (orphan cleanup).

The filesystem is the source of truth: if a file is on disk, it gets indexed;
if its point exists in Qdrant but the file is gone, the point is removed.

---

## Running tests

```bash
make test                       # run the full suite
uv run pytest -m "not slow"    # fast loop — skip the real bge-m3 load
uv run pytest -m slow          # slow tests only (loads bge-m3, ~5 s warm-up)
make check                     # CI gate: lint + typecheck + test
```

- **Unit and integration tests** use `QdrantStore(':memory:')` and `StubEmbedder` —
  no Docker, no model. Runs in under 2 s.
- **Slow tests** (`@pytest.mark.slow`) load the real bge-m3 model and run the
  full end-to-end smoke test (`tests/test_mvp_smoke.py`). The first run
  downloads model weights; subsequent runs use the `~/.cache/huggingface` cache.

---

## Architecture

Domain logic lives in `oh_my_kb/core/` with no MCP, CLI, or network dependencies.
The MCP server (`oh_my_kb/mcp/`) and CLI (`oh_my_kb/cli/`) are thin adapters,
so the same services can be reused by any future SDK or automation layer.

Hybrid retrieval uses bge-m3 to produce a 1 024-dim dense vector and a sparse
lexical vector from a single model pass. Qdrant fuses the two ranked candidate
lists using **Reciprocal Rank Fusion** server-side. Filters (`project`,
`archived`) are pushed down as payload conditions before fusion.

Each universe maps to one Qdrant collection (`kb_<slug(universe)>`). Search
never crosses universe boundaries; isolation is at the collection level.
