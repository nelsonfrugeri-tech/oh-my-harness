# Harness adapters

The core workflow speaks only in capabilities. Keep adapter mappings outside the core so one definition and one validation contract work in every harness.

| Capability | Required operation | Portable fallback |
| --- | --- | --- |
| `databricks-sql` | Execute governed, read-only queries and produce policy evidence | Managed Databricks SQL MCP or Statement Execution REST API |
| `databricks-lakeview` | Create, get, update, publish dashboards | Lakeview REST API or Databricks CLI |
| `browser` | Open the final draft and perform visual review | User performs the review manually |

Reading definitions and emitting JSON use the harness's universal filesystem primitives; they are
not adapter capabilities.

Adapters provide workspace authentication, warehouse selection, browser session, and signed policy
evidence without embedding organization details in the portable skill. The policy signing key is an
adapter secret and must not be exposed to the agent or stored in a dashboard definition. For REST, configure
`DATABRICKS_HOST` and `DATABRICKS_TOKEN`; non-standard workspace domains must also appear in
`DATABRICKS_TRUSTED_HOSTS`.

## MCP boundary

Prefer the vendor-managed SQL MCP when the workspace exposes it. Lakeview lifecycle operations may
remain REST/CLI or be wrapped by a thin MCP exposing `get/export`, `create`, `update`, and `publish`.
The MCP must not contain organization policy or dashboard reasoning: those belong to the local
adapter and the portable agent respectively. Keep browser automation separate for visual review.
