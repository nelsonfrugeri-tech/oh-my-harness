from __future__ import annotations

from collections.abc import Mapping
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "tools"
    / "databricks-dashboard"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS))

import publish_dashboard
import validate_dashboard
from dashboard_definition import _policy_payload, load_definition, load_policy_evidence
from json_object import JsonObject
from dashboard_validation import extract_sources, validate
from databricks_rest import RejectRedirects, _validate_host, validated_resource_id
from lakeview_serializer import serialized_dashboard


class SuccessfulSqlClient:
    def __init__(self) -> None:
        self.payloads: list[Mapping[str, object]] = []

    def request(
        self, method: str, path: str, payload: Mapping[str, object]
    ) -> dict[str, object]:
        self.payloads.append(payload)
        return {"status": {"state": "SUCCEEDED"}}


class SuccessfulLakeviewClient:
    host = "https://workspace.cloud.databricks.com"

    def request(
        self, method: str, path: str, payload: Mapping[str, object]
    ) -> dict[str, object]:
        return {"published": True}


class DatabricksDashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(
            os.environ,
            {
                "DATABRICKS_POLICY_EVIDENCE_KEY": "test-signing-key",
                "DATABRICKS_POLICY_TRUSTED_ISSUERS": "test-adapter",
            },
        )
        self.environment.start()

    def tearDown(self) -> None:
        self.environment.stop()

    def test_native_dashboard_preserves_rich_lakeview_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            definition_path, evidence_path = self._write_files(Path(directory))
            definition = load_definition(definition_path)
            evidence = load_policy_evidence(evidence_path)

        self.assertEqual(validate(definition, evidence), ())
        serialized = json.loads(serialized_dashboard(definition))
        page = serialized["pages"][0]
        self.assertEqual(page["pageType"], "PAGE_TYPE_CANVAS")
        self.assertEqual(page["layoutVersion"], "GRID_V1")
        self.assertIn("multilineTextboxSpec", page["layout"][0]["widget"])
        color = page["layout"][1]["widget"]["spec"]["encodings"]["color"]
        self.assertEqual(color["fieldName"], "series")

    def test_unapproved_source_cannot_be_hidden_in_a_comment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            definition_path, evidence_path = self._write_files(
                Path(directory),
                sql=(
                    "SELECT value FROM secret.data.table "
                    "WHERE event_date >= DATE '2030-01-01' -- example.analytics.requests"
                ),
            )
            errors = validate(
                load_definition(definition_path), load_policy_evidence(evidence_path)
            )

        self.assertIn("secret.data.table", " ".join(errors))

    def test_expired_policy_evidence_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            definition_path, evidence_path = self._write_files(
                Path(directory), evidence_ttl=timedelta(seconds=-1)
            )
            errors = validate(
                load_definition(definition_path), load_policy_evidence(evidence_path)
            )

        self.assertIn("policy evidence has expired", errors)

    def test_source_extraction_handles_quoted_three_part_names(self) -> None:
        sql = "SELECT x FROM `catalog`.`schema`.`table` WHERE event_date > DATE '2030-01-01'"
        self.assertEqual(extract_sources(sql), ("catalog.schema.table",))

    def test_exported_query_lines_preserve_boundaries(self) -> None:
        sql = (
            "SELECT model\n"
            "FROM example.analytics.requests\n"
            "WHERE event_date >= DATE '2030-01-01'\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            definition_path, _ = self._write_files(Path(directory), sql=sql)
            definition = load_definition(definition_path)

        self.assertEqual(definition.datasets[0].sql, sql)

    def test_loaded_dashboard_json_is_deeply_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            definition_path, _ = self._write_files(Path(directory))
            definition = load_definition(definition_path)

        self.assertIsInstance(definition.serialized_dashboard, JsonObject)
        pages = definition.serialized_dashboard["pages"]
        self.assertIsInstance(pages, tuple)
        with self.assertRaises(TypeError):
            definition.serialized_dashboard["pages"] = ()  # type: ignore[index]

    def test_comma_join_fails_closed(self) -> None:
        sql = (
            "SELECT a.value FROM example.analytics.requests a, secret.data.table_b b "
            "WHERE a.id = b.id"
        )
        with tempfile.TemporaryDirectory() as directory:
            definition_path, evidence_path = self._write_files(Path(directory), sql=sql)
            errors = validate(
                load_definition(definition_path), load_policy_evidence(evidence_path)
            )

        self.assertIn("must use explicit JOIN syntax", " ".join(errors))

        nested_sql = (
            "SELECT a.value FROM (SELECT value FROM example.analytics.requests "
            "WHERE event_date IS NOT NULL) a, secret.data.table_b b "
            "WHERE a.value = b.value"
        )
        with tempfile.TemporaryDirectory() as directory:
            definition_path, evidence_path = self._write_files(
                Path(directory), sql=nested_sql
            )
            nested_errors = validate(
                load_definition(definition_path), load_policy_evidence(evidence_path)
            )
        self.assertIn("must use explicit JOIN syntax", " ".join(nested_errors))

    def test_comma_join_between_ctes_and_subqueries_fails_closed(self) -> None:
        queries = (
            (
                "WITH first_rows AS (SELECT value FROM example.analytics.requests "
                "WHERE event_date IS NOT NULL), second_rows AS (SELECT value FROM "
                "example.analytics.requests WHERE event_date IS NOT NULL) "
                "SELECT first_rows.value FROM first_rows, second_rows "
                "WHERE first_rows.value = second_rows.value"
            ),
            (
                "SELECT first_rows.value FROM (SELECT value FROM "
                "example.analytics.requests WHERE event_date IS NOT NULL) first_rows, "
                "(SELECT value FROM example.analytics.requests "
                "WHERE event_date IS NOT NULL) second_rows "
                "WHERE first_rows.value = second_rows.value"
            ),
        )

        for sql in queries:
            with self.subTest(sql=sql):
                self.assertIn(
                    "must use explicit JOIN syntax",
                    " ".join(self._errors(sql)),
                )

    def test_filter_keywords_in_strings_or_identifiers_do_not_count(self) -> None:
        queries = (
            "SELECT 'WHERE' AS marker FROM example.analytics.requests",
            "SELECT `WHERE` FROM example.analytics.requests",
            'SELECT "WHERE" FROM example.analytics.requests',
        )

        for sql in queries:
            with self.subTest(sql=sql):
                self.assertIn(
                    "must include an explicit filter",
                    " ".join(self._errors(sql)),
                )

    def test_each_query_scope_requires_its_own_filter(self) -> None:
        queries = (
            (
                "SELECT nested.value FROM (SELECT value FROM "
                "example.analytics.requests WHERE event_date IS NOT NULL) nested"
            ),
            (
                "SELECT nested.value FROM (SELECT value FROM "
                "example.analytics.requests) nested WHERE nested.value IS NOT NULL"
            ),
            (
                "WITH local_rows AS (SELECT value FROM example.analytics.requests) "
                "SELECT value FROM local_rows WHERE value IS NOT NULL"
            ),
        )

        for sql in queries:
            with self.subTest(sql=sql):
                self.assertIn(
                    "must include an explicit filter",
                    " ".join(self._errors(sql)),
                )

    def test_commas_outside_from_clause_are_not_joins(self) -> None:
        sql = (
            "SELECT CONCAT(model, 'WHERE, literal') AS label, SUM(cost_usd) AS total "
            "FROM example.analytics.requests WHERE event_date >= DATE '2030-01-01' "
            "GROUP BY model"
        )

        self.assertEqual(self._errors(sql), ())

    def test_sensitive_secret_function_calls_fail_closed(self) -> None:
        calls = (
            "secret('scope', 'key')",
            "TRY_SECRET('scope', 'key')",
            "system.secret('scope', 'key')",
            "`system`.`try_secret`('scope', 'key')",
            '"SYSTEM"."SECRET"(\'scope\', \'key\')',
        )
        for call in calls:
            sql = (
                f"SELECT {call} AS value FROM example.analytics.requests "
                "WHERE event_date IS NOT NULL"
            )
            with self.subTest(call=call):
                self.assertIn(
                    "must not call secret or try_secret functions",
                    " ".join(self._errors(sql)),
                )

        nested = (
            "WITH local_rows AS (SELECT secret('scope', 'key') AS value "
            "FROM example.analytics.requests WHERE event_date IS NOT NULL) "
            "SELECT value FROM local_rows WHERE value IS NOT NULL"
        )
        self.assertIn(
            "must not call secret or try_secret functions",
            " ".join(self._errors(nested)),
        )

    def test_secret_text_and_non_call_identifiers_are_not_function_calls(self) -> None:
        sql = (
            "SELECT 'secret(\"scope\", \"key\")' AS marker, `secret`, "
            '"try_secret" FROM example.analytics.requests '
            "WHERE event_date >= DATE '2030-01-01' /* secret('scope', 'key') */"
        )

        self.assertEqual(self._errors(sql), ())

    def test_dynamic_identifier_calls_fail_closed_in_any_clause(self) -> None:
        calls = (
            "IDENTIFIER('secret')",
            "identifier('secret')('scope', 'key')",
            "system.IDENTIFIER('secret')",
            "`system`.`identifier`('secret')",
            '"SYSTEM"."IDENTIFIER"(\'secret\')',
        )
        for call in calls:
            sql = (
                f"SELECT {call} AS value FROM example.analytics.requests "
                "WHERE event_date >= DATE '2030-01-01'"
            )
            with self.subTest(call=call):
                self.assertIn(
                    "must not use dynamic IDENTIFIER calls",
                    " ".join(self._errors(sql)),
                )

        where_sql = (
            "SELECT value FROM example.analytics.requests WHERE "
            "IDENTIFIER('event_date') >= DATE '2030-01-01'"
        )
        self.assertIn(
            "must not use dynamic IDENTIFIER calls",
            " ".join(self._errors(where_sql)),
        )

    def test_identifier_text_and_non_call_identifiers_are_allowed(self) -> None:
        sql = (
            "SELECT 'IDENTIFIER(\"secret\")' AS marker, `identifier` "
            "FROM example.analytics.requests "
            "WHERE event_date >= DATE '2030-01-01'"
        )

        self.assertEqual(self._errors(sql), ())

    def test_external_source_rejects_tautological_or_textual_time_filters(self) -> None:
        predicates = (
            "1 = 1",
            "'event_date' = 'event_date'",
            "CURRENT_DATE() IS NOT NULL",
            "DATE '2030-01-01' IS NOT NULL",
            "event_date IS NOT NULL",
            "event_date.value IS NOT NULL",
            "value IS NOT NULL",
        )
        for predicate in predicates:
            sql = (
                "SELECT value FROM example.analytics.requests "
                f"WHERE {predicate}"
            )
            with self.subTest(predicate=predicate):
                self.assertIn(
                    "must include a recognized temporal predicate",
                    " ".join(self._errors(sql)),
                )

    def test_external_source_accepts_recognized_temporal_predicates(self) -> None:
        predicates = (
            "created_at >= TIMESTAMP '2030-01-01T00:00:00Z'",
            "`request_timestamp` >= CURRENT_TIMESTAMP() - INTERVAL 7 DAYS",
            "event_ts BETWEEN TIMESTAMP '2030-01-01T00:00:00Z' "
            "AND TIMESTAMP '2030-01-31T23:59:59Z'",
            "DATE '2030-01-01' <= event_date",
        )
        for predicate in predicates:
            sql = (
                "SELECT value FROM example.analytics.requests "
                f"WHERE {predicate}"
            )
            with self.subTest(predicate=predicate):
                self.assertEqual(self._errors(sql), ())

    def test_temporal_self_comparisons_fail_closed(self) -> None:
        predicates = (
            "event_date = event_date",
            "event_date = source.EVENT_DATE",
            "source.EVENT_DATE = event_date",
            "`event_date` = \"EVENT_DATE\"",
            "source.event_ts = source.`EVENT_TS`",
            "event_ts BETWEEN event_ts AND event_ts",
            "`event_ts` BETWEEN source.\"EVENT_TS\" AND end_ts",
        )
        for predicate in predicates:
            sql = (
                "SELECT value FROM example.analytics.requests "
                f"WHERE {predicate}"
            )
            with self.subTest(predicate=predicate):
                self.assertIn(
                    "must not compare a temporal column to itself",
                    " ".join(self._errors(sql)),
                )

    def test_temporal_comparisons_to_distinct_operands_are_allowed(self) -> None:
        predicates = (
            "start_date <= end_date",
            "left_side.event_date = right_side.event_date",
            "event_date >= DATE '2030-01-01'",
            "DATE '2030-01-01' <= event_date",
            ":start_date <= event_date",
            "event_ts BETWEEN start_ts AND end_ts",
            "event_date >= CURRENT_DATE() - INTERVAL 7 DAYS",
        )
        for predicate in predicates:
            sql = (
                "SELECT value FROM example.analytics.requests "
                f"WHERE {predicate}"
            )
            with self.subTest(predicate=predicate):
                self.assertEqual(self._errors(sql), ())

    def test_temporal_operand_expressions_reject_reused_source_column(self) -> None:
        predicates = (
            "event_date >= (event_date - INTERVAL 1 DAY)",
            "(event_date + INTERVAL 1 DAY) <= event_date",
            "source.event_date >= COALESCE((source.\"EVENT_DATE\" - "
            "INTERVAL 1 DAY), CURRENT_DATE())",
            "`event_ts` BETWEEN (`EVENT_TS` - INTERVAL 1 DAY) AND end_ts",
            "source.event_ts BETWEEN (source.`EVENT_TS` - INTERVAL 1 DAY) "
            "AND end_ts",
        )
        for predicate in predicates:
            sql = (
                "SELECT value FROM example.analytics.requests "
                f"WHERE {predicate}"
            )
            with self.subTest(predicate=predicate):
                self.assertIn(
                    "must not compare a temporal column to itself",
                    " ".join(self._errors(sql)),
                )

    def test_temporal_operand_expressions_allow_distinct_references(self) -> None:
        predicates = (
            "event_date >= (start_date - INTERVAL 1 DAY)",
            "(DATE '2030-01-01' - INTERVAL 1 DAY) <= event_date",
            "event_date >= COALESCE(:event_date, CURRENT_DATE())",
            "event_ts BETWEEN (start_ts - INTERVAL 1 DAY) AND end_ts",
            "left_side.event_date >= right_side.event_date",
        )
        for predicate in predicates:
            sql = (
                "SELECT value FROM example.analytics.requests "
                f"WHERE {predicate}"
            )
            with self.subTest(predicate=predicate):
                self.assertEqual(self._errors(sql), ())

    def test_or_predicates_fail_closed_even_when_nested(self) -> None:
        predicates = (
            "event_date >= DATE '2030-01-01' OR 1 = 1",
            "(event_date >= DATE '2030-01-01' OR value IS NOT NULL)",
        )
        for predicate in predicates:
            sql = (
                "SELECT value FROM example.analytics.requests "
                f"WHERE {predicate}"
            )
            with self.subTest(predicate=predicate):
                self.assertIn(
                    "must not use OR predicates",
                    " ".join(self._errors(sql)),
                )

    def test_or_text_in_strings_and_identifiers_is_not_boolean_or(self) -> None:
        sql = (
            "SELECT 'OR' AS marker, `OR` FROM example.analytics.requests "
            "WHERE event_date >= DATE '2030-01-01' AND 'OR' = 'OR'"
        )

        self.assertEqual(self._errors(sql), ())

    def test_comments_and_nested_queries_do_not_hide_sources(self) -> None:
        sql = (
            "SELECT x.value FROM (SELECT value FROM secret.data.table_b "
            "WHERE event_date >= DATE '2030-01-01') x "
            "JOIN /* comment */ example.analytics.requests a ON a.value = x.value "
            "WHERE a.event_date >= DATE '2030-01-01'"
        )
        with tempfile.TemporaryDirectory() as directory:
            definition_path, evidence_path = self._write_files(Path(directory), sql=sql)
            errors = validate(
                load_definition(definition_path), load_policy_evidence(evidence_path)
            )

        self.assertIn("secret.data.table_b", " ".join(errors))

    def test_comment_markers_in_strings_do_not_hide_unapproved_sources(self) -> None:
        queries = (
            (
                "SELECT a.value FROM example.analytics.requests a "
                "JOIN (SELECT '/*' AS marker, value FROM secret.data.table_b "
                "WHERE event_date >= DATE '2030-01-01' AND '*/' = '*/') b "
                "ON a.value = b.value WHERE a.event_date >= DATE '2030-01-01'"
            ),
            (
                "SELECT a.value FROM example.analytics.requests a "
                "JOIN (SELECT '-- not a comment' AS marker, value "
                "FROM secret.data.table_b WHERE event_date >= DATE '2030-01-01') b\n"
                "ON a.value = b.value WHERE a.event_date >= DATE '2030-01-01'"
            ),
        )
        for sql in queries:
            with self.subTest(sql=sql):
                self.assertIn("secret.data.table_b", " ".join(self._errors(sql)))

    def test_nested_source_allows_whitespace_between_identifier_parts(self) -> None:
        sql = (
            "SELECT nested.value FROM (SELECT value FROM "
            "`secret` . `data` . `table_b` WHERE event_date IS NOT NULL) nested "
            "WHERE nested.value IS NOT NULL"
        )

        self.assertEqual(extract_sources(sql), ("secret.data.table_b",))

    def test_comment_markers_inside_quoted_identifiers_are_preserved(self) -> None:
        sql = (
            "SELECT value FROM `catalog.name/*literal*/` . `schema--literal` . `table` "
            "WHERE event_date IS NOT NULL"
        )

        self.assertEqual(
            extract_sources(sql),
            ("catalog.name/*literal*/.schema--literal.table",),
        )

    def test_only_real_comments_are_removed_from_source_inspection(self) -> None:
        queries = (
            "SELECT value FROM example.analytics.requests "
            "/* JOIN secret.data.table_b */ WHERE event_date IS NOT NULL",
            "SELECT value FROM example.analytics.requests "
            "-- JOIN secret.data.table_b\nWHERE event_date IS NOT NULL",
        )
        for sql in queries:
            with self.subTest(sql=sql):
                self.assertEqual(
                    extract_sources(sql),
                    ("example.analytics.requests",),
                )

    def test_carriage_return_ends_a_line_comment(self) -> None:
        sql = (
            "SELECT a.value FROM example.analytics.requests a -- comment\r"
            "JOIN secret.data.table_b b ON a.value = b.value "
            "WHERE a.event_date IS NOT NULL"
        )

        self.assertIn("secret.data.table_b", " ".join(self._errors(sql)))

    def test_partially_qualified_relations_fail_closed(self) -> None:
        relations = (
            "secret_table",
            "secret_data.secret_table",
            "`secret_table`",
            "`secret_data` . `secret_table`",
        )
        for relation in relations:
            sql = (
                "SELECT a.value FROM example.analytics.requests a "
                f"JOIN {relation} b ON a.value = b.value "
                "WHERE a.event_date IS NOT NULL"
            )
            with self.subTest(relation=relation):
                self.assertIn(
                    "must use static catalog.schema.table",
                    " ".join(self._errors(sql)),
                )

    def test_table_valued_functions_fail_closed(self) -> None:
        functions = ("range(10)", "secret.catalog.table_fn(10)")
        for function in functions:
            sql = (
                "SELECT a.value FROM example.analytics.requests a "
                f"JOIN {function} b ON a.value = b.value "
                "WHERE a.event_date IS NOT NULL"
            )
            with self.subTest(function=function):
                self.assertIn("table-valued functions", " ".join(self._errors(sql)))

    def test_cte_names_are_local_but_their_relations_are_inspected(self) -> None:
        approved_sql = (
            "WITH local_rows AS (SELECT value FROM example.analytics.requests "
            "WHERE event_date >= DATE '2030-01-01') "
            "SELECT value FROM local_rows WHERE value IS NOT NULL"
        )
        unapproved_sql = (
            "WITH local_rows AS (SELECT value FROM secret.data.table_b "
            "WHERE event_date >= DATE '2030-01-01') "
            "SELECT value FROM local_rows WHERE value IS NOT NULL"
        )

        self.assertEqual(self._errors(approved_sql), ())
        errors = " ".join(self._errors(unapproved_sql))
        self.assertIn("secret.data.table_b", errors)
        self.assertNotIn("catalog.schema.table: local_rows", errors)

    def test_multiple_and_quoted_cte_names_are_local(self) -> None:
        sql = (
            "WITH first_rows AS (SELECT value FROM example.analytics.requests "
            "WHERE event_date >= DATE '2030-01-01'), "
            "`local rows` AS (SELECT value FROM first_rows WHERE value IS NOT NULL) "
            "SELECT value FROM `local rows` WHERE value IS NOT NULL"
        )

        self.assertEqual(self._errors(sql), ())

    def test_nested_cte_name_does_not_leak_to_outer_scope(self) -> None:
        sql = (
            "SELECT a.value FROM example.analytics.requests a "
            "JOIN (WITH secret_table AS (SELECT value "
            "FROM example.analytics.requests WHERE event_date IS NOT NULL) "
            "SELECT value FROM secret_table WHERE value IS NOT NULL) nested "
            "ON a.value = nested.value JOIN secret_table leaked "
            "ON a.value = leaked.value WHERE a.event_date IS NOT NULL"
        )

        self.assertIn(
            "catalog.schema.table: secret_table",
            " ".join(self._errors(sql)),
        )

    def test_nested_subquery_with_short_relation_fails_closed(self) -> None:
        sql = (
            "SELECT a.value FROM example.analytics.requests a "
            "JOIN (SELECT value FROM secret_table WHERE value IS NOT NULL) b "
            "ON a.value = b.value WHERE a.event_date IS NOT NULL"
        )

        self.assertIn(
            "must use static catalog.schema.table",
            " ".join(self._errors(sql)),
        )

    def test_parenthesized_table_reference_fails_closed(self) -> None:
        sql = (
            "SELECT a.value FROM example.analytics.requests a "
            "JOIN (secret_table) b ON a.value = b.value "
            "WHERE a.event_date IS NOT NULL"
        )

        self.assertIn(
            "parenthesized source must be a SELECT query",
            " ".join(self._errors(sql)),
        )

    def test_from_keyword_inside_expression_is_not_a_relation(self) -> None:
        sql = (
            "SELECT EXTRACT(YEAR FROM event_date) AS event_year "
            "FROM example.analytics.requests WHERE event_date >= DATE '2030-01-01'"
        )

        self.assertEqual(self._errors(sql), ())

    def test_unterminated_quotes_and_block_comments_fail_closed(self) -> None:
        suffixes = ("AND 'unterminated", "/* unterminated")
        for suffix in suffixes:
            sql = (
                "SELECT value FROM example.analytics.requests "
                f"WHERE event_date IS NOT NULL {suffix}"
            )
            with self.subTest(suffix=suffix):
                self.assertIn("has invalid SQL", " ".join(self._errors(sql)))

    def test_dynamic_source_identifier_fails_closed(self) -> None:
        sql = (
            "SELECT value FROM IDENTIFIER(:table) WHERE event_date >= DATE '2030-01-01'"
        )
        with tempfile.TemporaryDirectory() as directory:
            definition_path, evidence_path = self._write_files(Path(directory), sql=sql)
            errors = validate(
                load_definition(definition_path), load_policy_evidence(evidence_path)
            )

        self.assertIn("must not use dynamic source identifiers", " ".join(errors))

    def test_policy_evidence_requires_a_valid_signature(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, evidence_path = self._write_files(Path(directory))
            data = json.loads(evidence_path.read_text(encoding="utf-8"))
            data["signature"] = "invalid"
            evidence_path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "signature is invalid"):
                load_policy_evidence(evidence_path)

    def test_rest_host_rejects_local_and_untrusted_origins(self) -> None:
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            _validate_host("http://localhost:8080", ())
        with self.assertRaisesRegex(ValueError, "not a trusted"):
            _validate_host("https://attacker.example", ())
        _validate_host("https://workspace.cloud.databricks.com", ())

    def test_redirects_and_unsafe_resource_ids_are_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "redirects are refused"):
            RejectRedirects().redirect_request()
        with self.assertRaisesRegex(ValueError, "invalid characters"):
            validated_resource_id("../published")

    def test_smoke_query_cancels_on_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            definition_path, _ = self._write_files(Path(directory))
            raw = json.loads(definition_path.read_text(encoding="utf-8"))
            raw["smoke_parameters"] = [
                {"name": "start_date", "value": "2030-01-01", "type": "DATE"}
            ]
            definition_path.write_text(json.dumps(raw), encoding="utf-8")
            definition = load_definition(definition_path)
        client = SuccessfulSqlClient()

        self.assertEqual(validate_dashboard.smoke(definition, client), ())
        self.assertEqual(client.payloads[0]["on_wait_timeout"], "CANCEL")
        self.assertEqual(client.payloads[0]["parameters"][0]["name"], "start_date")

    def test_all_cli_argument_errors_are_json(self) -> None:
        for script in (
            "validate_dashboard.py",
            "create_dashboard.py",
            "publish_dashboard.py",
            "export_dashboard.py",
        ):
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / script)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                payload = json.loads(result.stdout)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")
                self.assertTrue(payload["errors"])

    def test_publish_without_authorization_returns_json_refusal(self) -> None:
        output = io.StringIO()
        previous = sys.argv
        sys.argv = ["publish_dashboard.py", "--dashboard-id", "dashboard-id"]
        try:
            with redirect_stdout(output):
                status = publish_dashboard.main()
        finally:
            sys.argv = previous

        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output.getvalue())["state"], "refused")

    def test_publish_returns_published_resource_url(self) -> None:
        output = io.StringIO()
        previous = sys.argv
        sys.argv = [
            "publish_dashboard.py",
            "--dashboard-id",
            "dashboard-id",
            "--authorize-publish",
        ]
        try:
            with (
                patch.object(
                    publish_dashboard.DatabricksClient,
                    "from_environment",
                    return_value=SuccessfulLakeviewClient(),
                ),
                redirect_stdout(output),
            ):
                status = publish_dashboard.main()
        finally:
            sys.argv = previous

        result = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(
            result["url"],
            "https://workspace.cloud.databricks.com/dashboardsv3/dashboard-id/published",
        )

    @staticmethod
    def _write_files(
        root: Path,
        sql: str = (
            "SELECT model, SUM(cost_usd) AS cost_usd, 'baseline' AS series "
            "FROM example.analytics.requests WHERE event_date >= DATE '2030-01-01' "
            "GROUP BY model"
        ),
        evidence_ttl: timedelta = timedelta(minutes=15),
    ) -> tuple[Path, Path]:
        now = datetime.now(timezone.utc)
        definition_path = root / "dashboard.json"
        evidence_path = root / "evidence.json"
        definition_path.write_text(
            json.dumps(DatabricksDashboardTests._definition(sql)), encoding="utf-8"
        )
        evidence = {
            "policy": "test-policy",
            "issuer": "test-adapter",
            "generated_at": now.isoformat(),
            "expires_at": (now + evidence_ttl).isoformat(),
            "sources": [
                {
                    "source": "example.analytics.requests",
                    "allowed": True,
                    "reference": "test-decision",
                }
            ],
        }
        evidence["signature"] = hmac.new(
            b"test-signing-key", _policy_payload(evidence), hashlib.sha256
        ).hexdigest()
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        return definition_path, evidence_path

    def _errors(self, sql: str) -> tuple[str, ...]:
        with tempfile.TemporaryDirectory() as directory:
            definition_path, evidence_path = self._write_files(
                Path(directory), sql=sql
            )
            return validate(
                load_definition(definition_path), load_policy_evidence(evidence_path)
            )

    @staticmethod
    def _definition(sql: str) -> dict[str, object]:
        return {
            "display_name": "Cost evidence",
            "warehouse_id": "warehouse",
            "serialized_dashboard": {
                "datasets": [
                    {
                        "name": "cost",
                        "displayName": "Cost",
                        "queryLines": [sql],
                    }
                ],
                "pages": [
                    {
                        "name": "overview",
                        "displayName": "Overview",
                        "pageType": "PAGE_TYPE_CANVAS",
                        "layoutVersion": "GRID_V1",
                        "layout": [
                            {
                                "widget": {
                                    "name": "methodology",
                                    "multilineTextboxSpec": {
                                        "lines": ["# Methodology\n"]
                                    },
                                },
                                "position": {"x": 0, "y": 0, "width": 12, "height": 3},
                            },
                            {
                                "widget": {
                                    "name": "cost-chart",
                                    "queries": [
                                        {
                                            "name": "main_query",
                                            "query": {
                                                "datasetName": "cost",
                                                "fields": [],
                                            },
                                        }
                                    ],
                                    "spec": {
                                        "version": 3,
                                        "widgetType": "bar",
                                        "encodings": {
                                            "x": {"fieldName": "model"},
                                            "y": {"fieldName": "cost_usd"},
                                            "color": {"fieldName": "series"},
                                        },
                                    },
                                },
                                "position": {"x": 0, "y": 3, "width": 12, "height": 6},
                            },
                        ],
                    }
                ],
                "uiSettings": {"theme": {}},
            },
        }
