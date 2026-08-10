# Native Lakeview definition

The portable definition wraps the native `serialized_dashboard` object accepted by Lakeview. The
scripts encode that object as a string only at the REST boundary. They intentionally do not rebuild
or simplify widgets because the internal schema evolves and a lossy serializer can silently drop
markdown, frames, color encodings, grouped or stacked marks, table columns, and layout metadata.

Prefer exporting an existing dashboard from the target workspace and editing the export. For a new
dashboard, start from a known-compatible sanitized fixture, then validate the draft visually.

```json
{
  "display_name": "Model cost overview",
  "warehouse_id": "warehouse-id",
  "parent_path": "/Shared/Analytics",
  "serialized_dashboard": {
    "datasets": [{
      "name": "cost_by_model",
      "displayName": "Cost by model",
      "queryLines": [
        "SELECT model, SUM(cost_usd) AS cost_usd\n",
        "FROM example.analytics.model_usage\n",
        "WHERE event_date >= DATE '2030-01-01'\n",
        "GROUP BY model ORDER BY cost_usd DESC\n"
      ]
    }],
    "pages": [{
      "name": "overview",
      "displayName": "Overview",
      "pageType": "PAGE_TYPE_CANVAS",
      "layoutVersion": "GRID_V1",
      "layout": [{
        "widget": {
          "name": "methodology",
          "multilineTextboxSpec": {
            "lines": ["# Model cost overview\n", "Source and filters are shown here.\n"]
          }
        },
        "position": {"x": 0, "y": 0, "width": 12, "height": 3}
      }]
    }],
    "uiSettings": {"theme": {"widgetHeaderAlignment": "ALIGNMENT_UNSPECIFIED"}}
  }
}
```

Required wrapper fields are `display_name`, `warehouse_id`, and `serialized_dashboard`; `parent_path`
is optional. The native object must contain non-empty `datasets` and `pages`. Every dataset needs a
unique `name` and non-empty `queryLines`. Every page needs layout entries with a native widget and a
grid position. Queries with parameter markers must supply bounded smoke-test values through the
optional wrapper field `smoke_parameters`, using the SQL Statement Execution parameter shape.

Treat the native object as an API artifact, not a stable cross-workspace schema. Preserve unknown
fields. Use the target workspace's exported definition as the compatibility reference and the
rendered draft as the final parser.

## Analytical patterns

- **Cost by model:** total and per-request cost with explicit time filters.
- **Before/after event:** equal windows, request counts, and observational wording.
- **Token analysis:** keep input, output, and total tokens distinct and normalize by request.
- **Three periods:** include period boundaries and a visible partial-period flag.
