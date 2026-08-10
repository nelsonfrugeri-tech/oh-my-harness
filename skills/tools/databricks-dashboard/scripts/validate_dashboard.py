#!/usr/bin/env python3
"""Validate a dashboard definition and optionally smoke-test its SQL."""

from __future__ import annotations

from collections.abc import Mapping
import argparse
import json
from pathlib import Path

from dashboard_cli import JsonArgumentParser
from dashboard_definition import Definition, load_definition, load_policy_evidence
from dashboard_validation import validate
from databricks_rest import DatabricksClient
from lakeview_serializer import serialized_dashboard


def parse_args() -> argparse.Namespace:
    parser = JsonArgumentParser()
    parser.add_argument("--definition", required=True, type=Path)
    parser.add_argument("--policy-evidence", required=True, type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--token-env", default="DATABRICKS_TOKEN")
    return parser.parse_args()


def smoke(definition: Definition, client: DatabricksClient) -> tuple[str, ...]:
    failures: list[str] = []
    for dataset in definition.datasets:
        payload: dict[str, object] = {
            "statement": f"SELECT 1 FROM ({dataset.sql}) AS dashboard_smoke LIMIT 1",
            "warehouse_id": definition.warehouse_id,
            "wait_timeout": "50s",
            "on_wait_timeout": "CANCEL",
            "disposition": "INLINE",
            "format": "JSON_ARRAY",
        }
        if definition.smoke_parameters:
            payload["parameters"] = [
                item.to_builtin() for item in definition.smoke_parameters
            ]
        response = client.request("POST", "/api/2.0/sql/statements", payload)
        if not _statement_succeeded(response):
            failures.append(f"dataset {dataset.name} smoke test did not succeed")
    return tuple(failures)


def _statement_succeeded(response: Mapping[str, object]) -> bool:
    status = response.get("status")
    return isinstance(status, Mapping) and status.get("state") == "SUCCEEDED"


def main() -> int:
    try:
        args = parse_args()
        definition = load_definition(args.definition)
        evidence = load_policy_evidence(args.policy_evidence)
        errors = validate(definition, evidence)
        if args.smoke and not errors:
            errors += smoke(
                definition, DatabricksClient.from_environment(args.token_env)
            )
        result = {
            "valid": not errors,
            "errors": errors,
            "serialized_dashboard": serialized_dashboard(definition),
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if not errors else 1
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(json.dumps({"valid": False, "errors": [str(error)]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
