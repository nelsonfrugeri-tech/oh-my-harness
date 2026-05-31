# oh-my-kb

Their knowledge is their universe. A programmatic, agnostic knowledge base exposed via MCP, with markdown notes indexed in Qdrant for hybrid search.

## Architecture

Domain logic lives in `oh_my_kb/core/` with no MCP, CLI, or network dependencies. The MCP server (`oh_my_kb/mcp/`) and CLI (`oh_my_kb/cli/`) are thin adapters over `core`, so a future `o-kb-sdk` can reuse the same logic.

```
oh_my_kb/
  core/   # pure domain logic — no MCP / CLI / network
  mcp/    # MCP server adapter
  cli/    # CLI adapter
tests/
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## Running tests

```bash
uv run pytest
```

## Lint & type-check

```bash
uv run ruff check .
uv run mypy oh_my_kb
```
