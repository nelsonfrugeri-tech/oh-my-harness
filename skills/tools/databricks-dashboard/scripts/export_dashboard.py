#!/usr/bin/env python3
"""Export a Lakeview draft as a reusable native dashboard definition."""

from __future__ import annotations

import argparse
import json

from dashboard_cli import JsonArgumentParser
from databricks_rest import DatabricksClient, validated_resource_id


def parse_args() -> argparse.Namespace:
    parser = JsonArgumentParser()
    parser.add_argument("--dashboard-id", required=True)
    parser.add_argument("--token-env", default="DATABRICKS_TOKEN")
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        dashboard_id = validated_resource_id(args.dashboard_id, "dashboard ID")
        client = DatabricksClient.from_environment(args.token_env)
        response = client.request("GET", f"/api/2.0/lakeview/dashboards/{dashboard_id}")
        serialized = response.get("serialized_dashboard", "")
        if not isinstance(serialized, str) or not serialized:
            raise ValueError("dashboard response has no serialized_dashboard")
        definition = {
            "display_name": response.get("display_name", dashboard_id),
            "warehouse_id": response.get("warehouse_id", ""),
            "parent_path": response.get("parent_path", "/"),
            "serialized_dashboard": json.loads(serialized),
            "etag": response.get("etag", ""),
        }
        print(json.dumps(definition, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (
        json.JSONDecodeError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        print(json.dumps({"state": "error", "errors": [str(error)]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
