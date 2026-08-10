#!/usr/bin/env python3
"""Publish a Lakeview dashboard only with an explicit authorization flag."""

from __future__ import annotations

import argparse
import json

from dashboard_cli import JsonArgumentParser
from databricks_rest import DatabricksClient, validated_resource_id


def parse_args() -> argparse.Namespace:
    parser = JsonArgumentParser()
    parser.add_argument("--dashboard-id", required=True)
    parser.add_argument("--authorize-publish", action="store_true")
    parser.add_argument("--embed-credentials", action="store_true")
    parser.add_argument("--token-env", default="DATABRICKS_TOKEN")
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        dashboard_id = validated_resource_id(args.dashboard_id, "dashboard ID")
    except ValueError as error:
        print(json.dumps({"state": "error", "errors": [str(error)]}, indent=2))
        return 1
    if not args.authorize_publish:
        print(
            json.dumps(
                {
                    "state": "refused",
                    "errors": ["publication requires explicit user authorization"],
                },
                indent=2,
            )
        )
        return 2
    try:
        client = DatabricksClient.from_environment(args.token_env)
        response = client.request(
            "POST",
            f"/api/2.0/lakeview/dashboards/{dashboard_id}/published",
            {"embed_credentials": args.embed_credentials},
        )
        print(
            json.dumps(
                {
                    "dashboard_id": dashboard_id,
                    "url": f"{client.host}/dashboardsv3/{dashboard_id}/published",
                    "state": "published",
                    "response": response,
                },
                indent=2,
            )
        )
        return 0
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(json.dumps({"state": "error", "errors": [str(error)]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
