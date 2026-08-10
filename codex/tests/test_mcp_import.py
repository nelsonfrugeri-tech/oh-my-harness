from __future__ import annotations

import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from import_mcps import main
from lib.atomic_file import atomic_write
from lib.mcp_import import McpImport, import_legacy_mcps
from lib.mcp_config import write_config
from lib.toml_backend import TomlBackend


class TomlBackendTest(unittest.TestCase):
    @patch(
        "lib.toml_backend.importlib.import_module",
        side_effect=ModuleNotFoundError("blocked for test"),
    )
    def test_missing_parsers_report_explicit_bootstrap_without_installing(
        self, importer: object
    ) -> None:
        with self.assertRaisesRegex(
            RuntimeError, "requirements-mcp-import.txt"
        ) as failure:
            TomlBackend.load()

        self.assertIn("pip install", str(failure.exception))
        self.assertFalse(TomlBackend.available())



class McpImportTest(unittest.TestCase):
    def setUp(self) -> None:
        if not TomlBackend.available():
            self.skipTest("optional full TOML parser is not bootstrapped")
        self._temporary = tempfile.TemporaryDirectory()
        self._root = Path(self._temporary.name)
        self._home = self._root / "home"
        self._codex_home = self._root / "codex"

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def test_import_adds_missing_http_and_stdio_servers(self) -> None:
        self._write_legacy(
            '{"mcpServers":{"remote":{"url":"https://mcp.example"},'
            '"local":{"command":"node","args":["server.js"],"cwd":"/tmp"}}}',
        )

        result = import_legacy_mcps(self._home, self._codex_home)
        self.assertEqual(("local", "remote"), result.added)
        self.assertTrue(result.backup)
        text = (self._codex_home / "config.toml").read_text(encoding="utf-8")
        self.assertIn('[mcp_servers."remote"]', text)
        self.assertIn('command = "node"', text)
        self.assertEqual(0o600, result.backup.stat().st_mode & 0o777)
        self.assertEqual(
            0o600,
            (self._codex_home / "config.toml").stat().st_mode & 0o777,
        )

    def test_sensitive_config_is_private_before_atomic_publication(self) -> None:
        target = self._codex_home / "config.toml"
        observed_modes: list[int] = []
        replace = os.replace
        target.parent.mkdir(parents=True)

        def inspect_mode(source: object, destination: object) -> None:
            observed_modes.append(Path(source).stat().st_mode & 0o777)
            replace(source, destination)

        with patch("lib.atomic_file.os.replace", side_effect=inspect_mode):
            write_config(target, '[mcp_servers.private]\ncommand = "tool"\n')

        self.assertEqual([0o600], observed_modes)

    def test_import_preserves_existing_name_even_when_transport_differs(self) -> None:
        self._write_legacy('{"mcpServers":{"gitlab":{"command":"node","args":["a"]}}}')
        self._write_config('[mcp_servers.gitlab]\ncommand = "node"\nargs = ["b"]\n')

        result = import_legacy_mcps(self._home, self._codex_home)
        self.assertEqual((), result.added)
        self.assertEqual(("gitlab",), result.skipped_existing)
        self.assertEqual(
            '[mcp_servers.gitlab]\ncommand = "node"\nargs = ["b"]\n', self._config()
        )

    def test_identity_never_equates_stdio_executable_with_different_arguments(
        self,
    ) -> None:
        incoming = McpImport("server", {"command": "npx", "args": ["one"]})
        existing = {"command": "npx", "args": ["two"]}

        self.assertFalse(incoming.matches(existing))

    def test_import_adds_server_when_existing_executable_has_different_arguments(
        self,
    ) -> None:
        self._write_legacy('{"mcpServers":{"second":{"command":"npx","args":["two"]}}}')
        self._write_config('[mcp_servers.first]\ncommand = "npx"\nargs = ["one"]\n')

        result = import_legacy_mcps(self._home, self._codex_home)
        self.assertEqual(("second",), result.added)
        repeated = import_legacy_mcps(self._home, self._codex_home)
        self.assertEqual(("second",), repeated.skipped_existing)
        self.assertIsNone(repeated.backup)

    def test_same_transport_with_different_environment_is_not_equivalent(self) -> None:
        self._write_legacy(
            '{"mcpServers":{"second":{"command":"npx","args":["server"],'
            '"env":{"TOKEN":"new"}}}}'
        )
        self._write_config(
            '[mcp_servers.first]\ncommand = "npx"\nargs = ["server"]\n'
            '[mcp_servers.first.env]\nTOKEN = "existing"\n'
        )

        result = import_legacy_mcps(self._home, self._codex_home)

        self.assertEqual(("second",), result.added)
        self.assertIn('[mcp_servers."second"]', self._config())

    def test_atomic_write_failure_preserves_original_config(self) -> None:
        self._write_legacy('{"mcpServers":{"new":{"command":"tool"}}}')
        original = '[mcp_servers.existing]\ncommand = "existing"\n'
        self._write_config(original)

        writes = 0

        def fail_target_write(path: Path, content: str, **options: object) -> None:
            nonlocal writes
            writes += 1
            if writes == 2:
                raise OSError("failed")
            atomic_write(path, content, **options)

        with (
            patch("lib.mcp_config.atomic_write", side_effect=fail_target_write),
            self.assertRaisesRegex(OSError, "failed"),
        ):
            import_legacy_mcps(self._home, self._codex_home)

        self.assertEqual(original, self._config())
        backups = tuple((self._codex_home / "backups").glob("*/config.toml"))
        self.assertEqual(1, len(backups))
        self.assertEqual(original, backups[0].read_text(encoding="utf-8"))

    def test_import_refuses_symlinked_config_without_replacing_or_mutating_it(self) -> None:
        self._write_legacy('{"mcpServers":{"new":{"command":"tool"}}}')
        external = self._root / "external-config.toml"
        original = '[mcp_servers.existing]\ncommand = "existing"\n'
        external.write_text(original, encoding="utf-8")
        self._codex_home.mkdir(parents=True)
        target = self._codex_home / "config.toml"
        target.symlink_to(external)

        with self.assertRaisesRegex(ValueError, "symbolic link"):
            import_legacy_mcps(self._home, self._codex_home)

        self.assertTrue(target.is_symlink())
        self.assertEqual(original, external.read_text(encoding="utf-8"))

    @patch(
        "lib.toml_backend.importlib.import_module",
        side_effect=ModuleNotFoundError("blocked for test"),
    )
    def test_missing_parser_never_changes_active_config(self, importer: object) -> None:
        self._write_legacy('{"mcpServers":{"new":{"command":"tool"}}}')
        original = '[mcp_servers.existing]\ncommand = "existing"\n'
        self._write_config(original)

        with self.assertRaisesRegex(RuntimeError, "pip install"):
            import_legacy_mcps(self._home, self._codex_home)

        self.assertEqual(original, self._config())
        self.assertFalse((self._codex_home / "backups").exists())

    @patch(
        "lib.toml_backend.importlib.import_module",
        side_effect=ModuleNotFoundError("blocked for test"),
    )
    def test_cli_reports_missing_parser_without_traceback(self, importer: object) -> None:
        self._write_legacy('{"mcpServers":{"new":{"command":"tool"}}}')
        original = '[mcp_servers.existing]\ncommand = "existing"\n'
        self._write_config(original)
        errors = StringIO()

        with redirect_stderr(errors):
            exit_code = main(
                [
                    "--home",
                    str(self._home),
                    "--codex-home",
                    str(self._codex_home),
                ]
            )

        self.assertEqual(1, exit_code)
        self.assertIn("pip install", errors.getvalue())
        self.assertNotIn("Traceback", errors.getvalue())
        self.assertEqual(original, self._config())

    def test_dry_run_and_check_never_write_or_create_backup(self) -> None:
        self._write_legacy(
            '{"mcpServers":{"remote":{"url":"https://mcp.example","env":{"TOKEN":"super-secret"}}}}',
        )

        dry_run = import_legacy_mcps(self._home, self._codex_home, dry_run=True)
        checked = import_legacy_mcps(self._home, self._codex_home, check=True)
        self.assertEqual(("remote",), dry_run.added)
        self.assertEqual(("remote",), checked.added)
        self.assertIsNone(dry_run.backup)
        self.assertFalse((self._codex_home / "config.toml").exists())

    def test_rendered_result_and_summary_never_expose_environment_values(self) -> None:
        self._write_legacy(
            '{"mcpServers":{"private":{"command":"tool","env":{"TOKEN":"super-secret"}}}}',
        )

        result = import_legacy_mcps(self._home, self._codex_home, dry_run=True)
        self.assertNotIn("super-secret", result.summary())

    def test_import_writes_environment_config_without_reporting_values(self) -> None:
        self._write_legacy(
            '{"mcpServers":{"private":{"command":"tool","env":{"TOKEN":"super-secret"}}}}',
        )

        result = import_legacy_mcps(self._home, self._codex_home)
        self.assertIn("super-secret", self._config())
        self.assertNotIn("super-secret", result.summary())

    def test_cli_uses_codex_home_environment_variable(self) -> None:
        self._write_legacy(
            '{"mcpServers":{"remote":{"url":"https://mcp.example","env":{"TOKEN":"super-secret"}}}}',
        )
        output = StringIO()
        with (
            patch.dict("os.environ", {"CODEX_HOME": str(self._codex_home)}),
            redirect_stdout(output),
        ):
            exit_code = main(["--home", str(self._home), "--dry-run"])
        self.assertEqual(0, exit_code)
        self.assertNotIn("super-secret", output.getvalue())
        self.assertFalse((self._codex_home / "config.toml").exists())

    def test_cli_treats_blank_codex_home_as_unset(self) -> None:
        output = StringIO()
        with (
            patch.dict("os.environ", {"CODEX_HOME": "  "}),
            patch.object(Path, "home", return_value=self._home),
            patch("import_mcps.import_legacy_mcps") as importer,
            redirect_stdout(output),
        ):
            importer.return_value.summary.return_value = "ok"
            exit_code = main(["--home", str(self._home), "--dry-run"])

        self.assertEqual(0, exit_code)
        self.assertEqual((self._home / ".codex").resolve(), importer.call_args.args[1])

    def test_cli_rejects_relative_and_source_owned_codex_homes(self) -> None:
        source_owned = Path(__file__).resolve().parents[2] / "private-codex"

        for codex_home in ("relative", str(source_owned)):
            with self.subTest(codex_home=codex_home):
                self.assertEqual(
                    1,
                    main(
                        [
                            "--home",
                            str(self._home),
                            "--codex-home",
                            codex_home,
                            "--dry-run",
                        ]
                    ),
                )

    def test_cli_check_reports_pending_changes_with_nonzero_exit(self) -> None:
        self._write_legacy('{"mcpServers":{"remote":{"url":"https://mcp.example"}}}')

        pending = main(
            [
                "--home",
                str(self._home),
                "--codex-home",
                str(self._codex_home),
                "--check",
            ]
        )
        self.assertEqual(1, pending)

        self._write_config('[mcp_servers.remote]\nurl = "https://mcp.example"\n')
        clean = main(
            [
                "--home",
                str(self._home),
                "--codex-home",
                str(self._codex_home),
                "--check",
            ]
        )
        self.assertEqual(0, clean)

    def _write_legacy(self, content: str) -> None:
        path = self._home / ".claude.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_config(self, content: str) -> None:
        self._codex_home.mkdir(parents=True, exist_ok=True)
        (self._codex_home / "config.toml").write_text(content, encoding="utf-8")

    def _config(self) -> str:
        return (self._codex_home / "config.toml").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
