---
name: databricks-dashboard
description: Create, investigate, export, validate, update, and publish portable Databricks AI/BI dashboards from native Lakeview definitions. Use for dashboard requests involving serialized_dashboard, dashboard SQL, visual validation, draft updates, publishing, or sharing. Require fresh external policy evidence, validate queries before writes, and keep draft, review, publication, and sharing as separate stages.
---

# Databricks Dashboard

Build dashboards as a portable workflow. Use abstract capabilities: `databricks-sql`,
`databricks-lakeview`, and `browser`. Resolve them through the active harness adapter; use the
universal read/write primitives and bundled REST client when an adapter is unavailable.

For organizations where governance is a security boundary, all reads and Lakeview writes must go
through a trusted server-side adapter. Client-side evidence validation is defense in depth for the
portable fallback, not a substitute for server-side authorization.

## Workflow

1. Read [governance.md](references/governance.md). Obtain fresh, signed policy evidence from the local
   adapter before querying data; definitions cannot authorize their own sources.
2. Capture the question, metric definitions, time window, comparability caveats, and intended audience. Do not infer causality from observational data.
3. Prefer export-first authoring: export a compatible dashboard, preserve its native
   `serialized_dashboard`, then change datasets and widgets. Internal Lakeview schema evolves and
   must not be rebuilt through a lossy serializer.
4. Write the definition and policy evidence outside the user's project unless they are requested
   product artifacts. Follow [lakeview-schema.md](references/lakeview-schema.md).
5. Run `validate_dashboard.py` before any dashboard API write. Add `--smoke` to execute bounded,
   read-only SQL checks.
6. Run `create_dashboard.py` to create a draft. Updating additionally requires `--allow-update`
   and the current `etag`; never overwrite implicitly.
7. Inspect the final draft with the `browser` capability. Apply
   [visualization-quality-gate.md](references/visualization-quality-gate.md), close auxiliary tabs,
   and confirm the visible ID matches the created resource.
8. Publish only when explicitly authorized in the current request. Keep sharing separate and
   obtain distinct authorization before changing permissions.

## Portable adapters

Read [harness-adapters.md](references/harness-adapters.md) when resolving capabilities. The
recommended stack is the official managed SQL MCP when available, plus Lakeview REST/CLI for the
dashboard lifecycle. A custom MCP is optional and must remain a thin capability adapter. Browser
validation stays separate because an API success does not prove a correct rendered dashboard.

## Scripts

```bash
python3 scripts/export_dashboard.py --dashboard-id ID
python3 scripts/validate_dashboard.py --definition /tmp/dashboard.json --policy-evidence /tmp/evidence.json
python3 scripts/validate_dashboard.py --definition /tmp/dashboard.json --policy-evidence /tmp/evidence.json --smoke
python3 scripts/create_dashboard.py --definition /tmp/dashboard.json --policy-evidence /tmp/evidence.json
python3 scripts/create_dashboard.py --definition /tmp/dashboard.json --policy-evidence /tmp/evidence.json --dashboard-id ID --etag ETAG --allow-update
python3 scripts/publish_dashboard.py --dashboard-id ID --authorize-publish
```

All scripts emit JSON containing the dashboard ID and dashboard URL when a remote resource is created or updated. They create no temporary files; callers own the declarative definition and any saved output.

## Constraints

- Treat production data, permission changes, publishing, unpublishing, trashing, and draft
  overwrites as separate actions. This skill does not implement destructive lifecycle actions.
- Use fully qualified table names, explicit filters, and read-only SQL only.
- Present associations, changes, and uncertainty accurately. Label before/after comparisons as observational unless an experimental design supports a causal claim.
- Prefer a small number of decision-oriented widgets over exhaustive charts. Validate period completeness and normalize metrics when volumes differ.
