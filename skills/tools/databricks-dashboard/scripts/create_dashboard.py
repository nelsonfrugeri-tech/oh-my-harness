#!/usr/bin/env python3
"""Create a Lakeview draft or explicitly update a guarded existing draft."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dashboard_cli import JsonArgumentParser
from dashboard_definition import Definition, load_definition, load_policy_evidence
from dashboard_validation import validate
from databricks_rest import DatabricksClient, validated_resource_id
from lakeview_serializer import serialized_dashboard
from validate_dashboard import smoke


def parse_args() -> argparse.Namespace:
    parser = JsonArgumentParser()
    parser.add_argument("--definition", required=True, type=Path)
    parser.add_argument("--policy-evidence", required=True, type=Path)
    parser.add_argument("--dashboard-id", default="")
    parser.add_argument("--etag", default="")
    parser.add_argument("--allow-update", action="store_true")
    parser.add_argument("--token-env", default="DATABRICKS_TOKEN")
    return parser.parse_args()


def payload(definition: Definition, serialized: str, etag: str) -> dict[str, str]:
    result = {
        "display_name": definition.title,
        "warehouse_id": definition.warehouse_id,
        "serialized_dashboard": serialized,
    }
    if etag:
        result["etag"] = etag
    return result


def main() -> int:
    try:
        args = parse_args()
        definition = load_definition(args.definition)
        evidence = load_policy_evidence(args.policy_evidence)
        errors = validate(definition, evidence)
        if errors:
            raise ValueError("validation failed: " + "; ".join(errors))
        if args.dashboard_id and (not args.allow_update or not args.etag):
            raise ValueError("updating a draft requires --allow-update and --etag")
        requested_id = (
            validated_resource_id(args.dashboard_id, "dashboard ID")
            if args.dashboard_id
            else ""
        )
        client = DatabricksClient.from_environment(args.token_env)
        smoke_errors = smoke(definition, client)
        if smoke_errors:
            raise ValueError("smoke validation failed: " + "; ".join(smoke_errors))
        serialized = serialized_dashboard(definition)
        if requested_id:
            response = client.request(
                "PATCH",
                f"/api/2.0/lakeview/dashboards/{requested_id}",
                payload(definition, serialized, args.etag),
            )
        else:
            request = payload(definition, serialized, "")
            request["parent_path"] = definition.parent_path
            response = client.request("POST", "/api/2.0/lakeview/dashboards", request)
        dashboard_id = validated_resource_id(
            str(response["dashboard_id"]), "returned dashboard ID"
        )
        print(
            json.dumps(
                {
                    "dashboard_id": dashboard_id,
                    "url": f"{client.host}/sql/dashboardsv3/{dashboard_id}",
                    "state": "draft",
                },
                indent=2,
            )
        )
        return 0
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(json.dumps({"state": "error", "errors": [str(error)]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
