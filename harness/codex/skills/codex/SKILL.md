---
name: codex
description: "Install, synchronize, verify, or diagnose oh-my-harness Codex integration while preserving user configuration and authorization boundaries."
---

# Codex Integration

Repository content is source of truth; installed plugin/adapter copies are derived. Use plugin for
shared skills/hooks and codex adapter for agents, managed instructions, and local integrations.
Discover commands from checked-in installer help.

Never overwrite unowned files. Stop with exact conflict and non-destructive choices. Backups do not
grant replacement authority. Preserve unrelated hooks/configuration.

Graphify is vendored derived content; do not edit it here. Preserve a non-link installation only when
marker/full tree match. Deja owns transcript index, MCP wiring, and hooks; preserve them and use Deja
only for session-memory, never a second curated store.

Run installer check and report states independently: installed, configured, authorized, reachable,
and healthy after a probe. Configured never proves authorization, reachability, or health. Missing
optional providers are degraded capabilities, not failed filesystem installation.

Markdown/JSON remain knowledge source of truth. Qdrant, Deja indexes, Graphify graphs, installed
copies, and provider state are derived/provider-owned. Keep credentials, account IDs, executable
paths, and personal directories out of repository. Keep diagnostics outside projects and do not
modify Claude adapter files during Codex-only work.

## Package migration to 2.0.1

The hook descriptor and commands move to `harness/codex/hooks/` and `core/hooks/`.
After upgrading from the old layout, open `/hooks` and review both `SessionStart` and the commit
gate again. Previous approval does not authorize changed definitions. Verify runtime trust before
reporting either hook as active; `install.py --check` validates adapter files, not hook trust.
The installer does not grant trust on the user's behalf. Use `installers/codex/install.py` from
the repository root to synchronize the global adapter.
