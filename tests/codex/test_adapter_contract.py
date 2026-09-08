from __future__ import annotations

import json
import os
import re
import select
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]


class AdapterContractTest(unittest.TestCase):
    def test_codex_global_guidance_limits_human_confirmation(self) -> None:
        guidance = _ROOT.joinpath("harness/codex/AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("Peça confirmação ao usuário somente antes de:", guidance)
        self.assertIn("excluir, sobrescrever de forma irrecuperável", guidance)
        self.assertIn("credentials, tokens, senhas, private keys", guidance)
        self.assertIn("imposto pelo runtime", guidance)

    def test_codex_plugin_matches_the_shared_plugin_identity(self) -> None:
        codex = json.loads(
            _ROOT.joinpath(".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        claude = json.loads(
            _ROOT.joinpath(".claude-plugin/plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            _ROOT.joinpath(".claude-plugin/marketplace.json").read_text(encoding="utf-8")
        )

        self.assertEqual(claude["name"], codex["name"])
        self.assertEqual(claude["version"], codex["version"])
        self.assertEqual(claude["version"], marketplace["metadata"]["version"])
        self.assertEqual(["./core/skills/", "./harness/codex/skills/"], codex["skills"])
        self.assertEqual(["./core/skills/", "./harness/claude/skills/"], claude["skills"])
        self.assertEqual("./harness/claude/hooks/hooks.json", claude["hooks"])
        self.assertEqual("./harness/codex/hooks/hooks.json", codex["hooks"])
        declared = {_ROOT / path for path in claude["agents"]}
        on_disk = set(_ROOT.glob("harness/claude/agents/**/*.md"))
        self.assertEqual(on_disk, declared)
        self.assertEqual(len(declared), len(claude["agents"]))
        self.assertTrue(_ROOT.joinpath("harness/claude/hooks/hooks.json").is_file())
        self.assertTrue(_ROOT.joinpath("harness/codex/hooks/hooks.json").is_file())
        self.assertFalse(_ROOT.joinpath("agents").exists())
        self.assertFalse(_ROOT.joinpath("hooks").exists())

    def test_readme_skill_catalog_matches_packaged_skills(self) -> None:
        readme = _ROOT.joinpath("README.md").read_text(encoding="utf-8")
        section = readme.split("### Skills\n", 1)[1].split("### Workflows\n", 1)[0]
        catalog = {
            name
            for line in section.splitlines()
            if line.startswith("**")
            for name in re.findall(
                r"`([^`]+)`", re.sub(r"\([^)]*\)", "", line.split("**", 2)[2])
            )
        }
        manifests = tuple(_ROOT.glob(".*-plugin/plugin.json"))
        self.assertTrue(manifests)
        declared_roots = {
            _ROOT / root
            for manifest in manifests
            for root in json.loads(manifest.read_text(encoding="utf-8"))["skills"]
        }
        existing_roots = {_ROOT / "core/skills", *_ROOT.glob("harness/*/skills")}
        self.assertEqual(existing_roots, declared_roots)
        self.assertTrue(all(root.is_dir() for root in declared_roots))
        packaged = {
            path.parent.name
            for root in declared_roots
            for path in root.glob("*/SKILL.md")
        }

        self.assertEqual(packaged, catalog)
        self.assertIn(f"/badge/skills-{len(packaged)}-", readme)

    def test_codex_marketplace_exposes_the_repository_plugin(self) -> None:
        marketplace = json.loads(
            _ROOT.joinpath(".agents/plugins/marketplace.json").read_text(encoding="utf-8")
        )
        plugin = marketplace["plugins"][0]

        self.assertEqual("oh-my-harness", marketplace["name"])
        self.assertEqual("oh-my-harness", plugin["name"])
        self.assertEqual({"source": "local", "path": "./"}, plugin["source"])
        self.assertEqual("AVAILABLE", plugin["policy"]["installation"])
        self.assertEqual("ON_INSTALL", plugin["policy"]["authentication"])

    def test_shared_skills_are_flat_for_native_plugin_discovery(self) -> None:
        skill_roots = tuple(
            path for path in _ROOT.joinpath("core/skills").iterdir() if path.is_dir()
        )

        self.assertTrue(skill_roots)
        self.assertTrue(all(path.joinpath("SKILL.md").is_file() for path in skill_roots))
        skill_names = {path.name for path in skill_roots}
        self.assertNotIn("claude-code", skill_names)
        self.assertNotIn("codex", skill_names)

    @unittest.skipUnless(shutil.which("codex"), "Codex CLI is not installed")
    def test_codex_cli_discovers_the_expected_skill_inventory(self) -> None:
        manifest = json.loads(
            _ROOT.joinpath(".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )

        with tempfile.TemporaryDirectory() as temporary:
            isolated_home = Path(temporary).joinpath("home")
            codex_home = isolated_home.joinpath("codex-home")
            codex_home.mkdir(parents=True)
            env = {
                **os.environ,
                "HOME": str(isolated_home),
                "CODEX_HOME": str(codex_home),
            }
            self._run_codex(env, "plugin", "marketplace", "add", str(_ROOT))
            self._run_codex(
                env,
                "plugin",
                "add",
                "oh-my-harness@oh-my-harness",
            )
            installed = codex_home.joinpath(
                "plugins/cache/oh-my-harness/oh-my-harness",
                manifest["version"],
            )
            shared_skills = {
                path.name
                for path in _ROOT.joinpath("core/skills").iterdir()
                if path.is_dir()
            }
            codex_skills = {
                path.name
                for path in _ROOT.joinpath("harness/codex/skills").iterdir()
                if path.is_dir()
            }
            expected = shared_skills | codex_skills
            prompt_input = self._run_codex(
                env,
                "debug",
                "prompt-input",
                "probe",
            )
            messages = json.loads(prompt_input.stdout)
            model_input = "\n".join(
                part["text"]
                for message in messages
                for part in message.get("content", ())
                if part.get("type") == "input_text"
            )
            matches = re.findall(
                r"^- oh-my-harness:([a-z0-9-]+):",
                model_input,
                re.MULTILINE,
            )
            discovered = set(matches)

            self.assertEqual(len(matches), len(discovered))
            self.assertEqual(expected, discovered)
            self.assertNotIn("claude-code", discovered)
            self.assertIn("didactic-visual", discovered)
            self.assertIn("evidence", discovered)
            self.assertTrue(installed.joinpath("harness/codex/skills/codex/SKILL.md").is_file())
            didactic_visual = installed.joinpath(
                "core/skills/didactic-visual/SKILL.md"
            ).read_text(encoding="utf-8")
            self.assertIn("absence of", didactic_visual)
            self.assertIn("not a blocker", didactic_visual)
            self.assertTrue(installed.joinpath("harness/codex/hooks/hooks.json").is_file())

            hook_listing = self._run_codex_app_server(
                env,
                {"cwds": [str(_ROOT)]},
            )
            entry = next(
                item
                for item in hook_listing["data"]
                if Path(item["cwd"]).resolve() == _ROOT.resolve()
            )
            plugin_hooks = [
                hook
                for hook in entry["hooks"]
                if hook["source"] == "plugin"
                and hook["pluginId"] == "oh-my-harness@oh-my-harness"
            ]

            self.assertEqual([], entry["warnings"])
            self.assertEqual([], entry["errors"])
            self.assertEqual(
                {"preToolUse"},
                {hook["eventName"] for hook in plugin_hooks},
            )
            quality_gate = next(
                hook for hook in plugin_hooks if hook["eventName"] == "preToolUse"
            )
            self.assertEqual("Bash", quality_gate["matcher"])
            self.assertIn(str(installed), quality_gate["command"])
            self.assertIn("core/hooks/quality-gate.sh", quality_gate["command"])
            self.assertNotIn("CLAUDE_PLUGIN_ROOT", quality_gate["command"])

    def test_plugin_hooks_use_the_codex_schema_and_standalone_instructions(self) -> None:
        hooks = json.loads(_ROOT.joinpath("harness/codex/hooks/hooks.json").read_text(encoding="utf-8"))
        claude_hooks = json.loads(
            _ROOT.joinpath("harness/claude/hooks/hooks.json").read_text(encoding="utf-8")
        )
        self.assertEqual(claude_hooks, hooks)
        handlers = [
            handler
            for groups in hooks["hooks"].values()
            for group in groups
            for handler in group["hooks"]
        ]
        self.assertEqual({"PreToolUse"}, set(hooks["hooks"]))

        # Two PreToolUse handlers now point at quality-gate.sh (Bash `gh pr create` and the
        # GitHub MCP PR-creation tool); disambiguate on the Bash-only `if` condition instead
        # of relying on handler order.
        quality_gate = next(
            handler
            for handler in handlers
            if "quality-gate.sh" in handler["command"] and "if" in handler
        )
        self.assertEqual("Bash(gh pr create*)", quality_gate["if"])

    def test_codex_global_guidance_is_pt_br_and_below_the_default_limit(self) -> None:
        guidance = _ROOT.joinpath("harness/codex/AGENTS.md").read_text(encoding="utf-8")

        self.assertLessEqual(len(guidance.encode("utf-8")), 32 * 1024)
        self.assertIn("## Idioma", guidance)
        self.assertIn("## Nunca poluir o projeto com arquivos que não são do produto", guidance)
        self.assertIn("## Ambiente", guidance)
        self.assertIn("### Fatos vinculantes do ambiente", guidance)
        self.assertIn("### Regras de conhecimento", guidance)
        self.assertIn("## Antes de responder", guidance)
        self.assertIn("## Padrões de código — ativação obrigatória", guidance)
        self.assertIn("## Fluxo de PR", guidance)
        self.assertIn("## Como opero", guidance)
        portuguese_prose = (
            "Na dúvida, busque — nunca responda de memória",
            "Antes de escrever, modificar ou revisar qualquer linha de código",
            "Commit e push são livres",
            "Delegue por padrão.",
        )
        self.assertTrue(all(sentence in guidance for sentence in portuguese_prose))
        english_headings = (
            "## Language",
            "## Never pollute a project with non-product files",
            "## Environment and capability adapters",
            "### Binding environment facts",
            "### Knowledge rules",
            "## Self-evaluation before answering",
            "## Mandatory code standards",
            "## Commit gate",
            "## Long-running work",
        )
        self.assertFalse(any(heading in guidance for heading in english_headings))

    def test_every_portable_agent_has_a_codex_adapter(self) -> None:
        shared = {
            self._yaml_name(path)
            for path in _ROOT.glob("harness/claude/agents/**/*.md")
            if path.name != "claude-code.md"
        }
        adapters = {
            self._toml_name(path)
            for path in _ROOT.glob("harness/codex/agents/*.toml")
            if path.name != "codex.toml"
        }
        self.assertEqual(shared, adapters)

    def test_skill_leaf_names_are_unique_for_codex(self) -> None:
        sources = (
            *_ROOT.glob("core/skills/**/SKILL.md"),
            *_ROOT.glob("harness/codex/skills/**/SKILL.md"),
        )
        names = [path.parent.name for path in sources]
        self.assertEqual(len(names), len(set(names)))

    def test_feature_skill_uses_portable_orchestration(self) -> None:
        content = _ROOT.joinpath("core/skills/feature/SKILL.md").read_text(encoding="utf-8")
        forbidden = ("Workflow({", "AskUserQuestion", "use the tool `Agent`")
        self.assertFalse(any(token in content for token in forbidden))
        self.assertIn("Keep resumable state", content)

    def test_engineering_agents_load_the_evidence_skill(self) -> None:
        roles = (
            "ai-engineer", "architect", "software-engineer", "tech-pm",
        )

        for role in roles:
            with self.subTest(role=role):
                shared = _ROOT.joinpath(f"harness/claude/agents/engineers/{role}.md").read_text(
                    encoding="utf-8"
                )
                codex = _ROOT.joinpath(f"harness/codex/agents/{role}.toml").read_text(
                    encoding="utf-8"
                )
                self.assertIn("  - evidence", shared)
                self.assertIn("`evidence`", codex)


    def test_policy_agents_load_the_evidence_skill(self) -> None:
        for role in ("evidence-reviewer",):
            with self.subTest(role=role):
                shared = _ROOT.joinpath(f"harness/claude/agents/policy/{role}.md").read_text(
                    encoding="utf-8"
                )
                codex = _ROOT.joinpath(f"harness/codex/agents/{role}.toml").read_text(
                    encoding="utf-8"
                )
                self.assertIn("  - evidence", shared)
                self.assertIn("`evidence`", codex)

    def test_kb_write_requires_machine_and_session_provenance(self) -> None:
        content = _ROOT.joinpath("core/skills/kb-write/SKILL.md").read_text(
            encoding="utf-8"
        )
        required = (
            "`provenance.harness.name`",
            "`provenance.harness.session_id`",
            "`provenance.harness.session_name`",
            "`provenance.harness.app_name`",
            "`provenance.execution.cwd`",
            "`provenance.execution.transcript_path`",
            "`provenance.machine.id`",
            "`provenance.machine.label`",
            "`provenance.machine.hostname`",
            "`provenance.machine.username`",
            "~/.local/share/omh-kb/identity.json",
        )

        self.assertTrue(all(field in content for field in required))
        self.assertIn("do not write the note", " ".join(content.split()))
        self.assertIn("raw MAC address", content)

    def test_kb_session_record_carries_nullable_runtime_metadata(self) -> None:
        content = _ROOT.joinpath("core/skills/kb-session/SKILL.md").read_text(
            encoding="utf-8"
        )
        required = (
            '"session_name"',
            '"app_name"',
            '"cwd"',
            '"machine_id"',
            '"machine_label"',
            '"hostname"',
            '"username"',
        )

        self.assertTrue(all(field in content for field in required))
        self.assertIn("fields always exist but may be `null`", " ".join(content.split()))
        self.assertIn("whitespace-only", content)
        self.assertIn("every non-null path must be absolute", " ".join(content.split()))

    def test_kb_legacy_session_records_have_a_lossless_v3_migration(self) -> None:
        session = _ROOT.joinpath("core/skills/kb-session/SKILL.md").read_text(
            encoding="utf-8"
        )
        infra = _ROOT.joinpath("core/skills/kb-infra/SKILL.md").read_text(
            encoding="utf-8"
        )
        session_flat = " ".join(session.split())
        infra_flat = " ".join(infra.split())
        for phrase in (
            "Project missing multi-value fields as `[]` and nullable scalar fields as `null`",
            "never rewrite historical JSON",
            "never assign the current machine to a past session",
            "Promote only the current session to schema v3 and only with values observed",
            "preserve the legacy record unchanged",
        ):
            self.assertIn(phrase, session_flat)
        self.assertIn("continue the batch", infra_flat)
        self.assertIn("Reindexing never modifies source JSON", infra_flat)

    def test_kb_session_schema_matches_qdrant_provenance_payload(self) -> None:
        session = _ROOT.joinpath("core/skills/kb-session/SKILL.md").read_text(
            encoding="utf-8"
        )
        infra = _ROOT.joinpath("core/skills/kb-infra/SKILL.md").read_text(
            encoding="utf-8"
        )
        provenance_fields = {
            "harness",
            "session_id",
            "session_name",
            "app_name",
            "cwd",
            "transcript_path",
            "machine_id",
            "machine_label",
            "hostname",
            "username",
        }
        schema_match = re.search(r"Schema:\n\n```json\n(.*?)\n```", session, re.DOTALL)
        payload_match = re.search(
            r'\| Session point \(`kind: "session"`\) \| ([^|]+) \|', infra
        )

        self.assertIsNotNone(schema_match)
        self.assertIsNotNone(payload_match)
        schema_fields = set(json.loads(schema_match.group(1)))
        payload_fields = set(re.findall(r"`([^`]+)`", payload_match.group(1)))
        disk_only_fields = {
            "description",
            "resume",
            "entity_refs",
            "references",
            "temporal_refs",
        }
        derived_fields = {
            "kind",
            "entity_kinds",
            "entity_keys",
            "reference_targets",
            "temporal_values",
        }
        expected_payload_fields = (schema_fields - disk_only_fields) | derived_fields

        self.assertTrue(provenance_fields <= schema_fields)
        self.assertEqual(expected_payload_fields, payload_fields)

    def test_kb_qdrant_indexes_provenance_fields(self) -> None:
        content = _ROOT.joinpath("core/skills/kb-infra/SKILL.md").read_text(
            encoding="utf-8"
        )
        indexed_fields = (
            "`harness`",
            "`session_id`",
            "`session_name`",
            "`machine_id`",
            "`machine_label`",
        )

        self.assertTrue(all(field in content for field in indexed_fields))
        self.assertIn("PayloadSchemaType.KEYWORD", content)

    def test_kb_retrieval_can_filter_by_provenance(self) -> None:
        content = _ROOT.joinpath("core/skills/kb-retrieval/SKILL.md").read_text(
            encoding="utf-8"
        )
        fields = (
            "`harness`",
            "`session_id`",
            "`session_name`",
            "`machine_id`",
            "`machine_label`",
        )

        self.assertTrue(all(field in content for field in fields))
        self.assertIn("Legacy points", content)

    def test_kb_agents_enforce_provenance_before_writing(self) -> None:
        shared = _ROOT.joinpath("harness/claude/agents/tools/knowledge-base.md").read_text(
            encoding="utf-8"
        )
        codex = _ROOT.joinpath("harness/codex/agents/knowledge-base.toml").read_text(
            encoding="utf-8"
        )

        for content in (shared, codex):
            self.assertIn("provenance", content)
            self.assertIn("identity.json", content)
            self.assertIn("Never write", content)

    def test_site_skills_are_harness_neutral(self) -> None:
        paths = (
            _ROOT / "core/skills/site-report/SKILL.md",
            _ROOT / "core/skills/site-expose/SKILL.md",
        )
        content = "\n".join(path.read_text(encoding="utf-8") for path in paths)

        self.assertFalse(any(token in content for token in ("CLAUDE.md", "Explore", "dataviz")))
        self.assertIn("abstract `tunnel` capability", content)
        self.assertIn("[a-z0-9]+(?:-[a-z0-9]+)*", content)
        self.assertIn("https://", content)

    def test_codex_adapter_does_not_duplicate_the_plugin_session_start(self) -> None:
        data = json.loads(_ROOT.joinpath("harness/codex/adapter-hooks-removal.json").read_text(encoding="utf-8"))
        self.assertEqual({}, data["hooks"])

    def test_quality_gate_is_the_only_shared_hook(self) -> None:
        gate = _ROOT / "core/hooks/quality-gate.sh"

        self.assertEqual([gate], sorted(_ROOT.glob("core/hooks/*.sh")))
        self.assertTrue(gate.stat().st_mode & 0o111)
        self.assertEqual([], list(_ROOT.glob("harness/*/hooks/*.sh")))

    def test_code_craft_contract_is_consistently_repository_first(self) -> None:
        paths = (
            "README.md",
            "harness/claude/CLAUDE.md",
            "harness/codex/AGENTS.md",
            "core/skills/implement/references/code-craft.md",
        )
        combined = chr(10).join(
            _ROOT.joinpath(path).read_text(encoding="utf-8")
            for path in paths
        )

        for path in paths[:3]:
            with self.subTest(path=path):
                document = _ROOT.joinpath(path).read_text(encoding="utf-8")
                self.assertIn("repository-first", document)
        self.assertNotIn("code-craft — inviolable rules", combined)
        self.assertNotIn("design pattern instead of `if/elif` chains", combined)
        self.assertIn("Do not split by a universal line or symbol count", combined)
        self.assertIn("Project contracts override generic preferences", combined)

    def test_external_evals_documentation_uses_the_current_entry(self) -> None:
        readme = _ROOT.joinpath("README.md").read_text(encoding="utf-8")
        installer = _ROOT.joinpath(
            "harness/claude/skills/claude-code/SKILL.md"
        ).read_text(encoding="utf-8")

        for document in (readme, installer):
            self.assertIn("evals >= 0.3.1", document)
            self.assertIn("evals:evals-start", document)
            self.assertIn("claude plugin update evals@ai-evals-course", document)
        self.assertNotIn("/evals:start` respondem", installer)

    def test_qdrant_compose_binds_published_ports_to_loopback(self) -> None:
        compose_path = _ROOT / "core/skills/kb-infra/docker-compose.yml"
        compose = compose_path.read_text(encoding="utf-8")
        expected_bindings = {
            ("127.0.0.1", "6333", 6333),
            ("127.0.0.1", "6334", 6334),
        }

        for host_ip, published, target in expected_bindings:
            self.assertIn(
                f'"{host_ip}:{published}:{target}"',
                compose,
            )
        if shutil.which("docker") is None:
            return

        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(compose_path),
                "config",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        rendered = json.loads(result.stdout)
        ports = rendered["services"]["qdrant"]["ports"]
        actual_bindings = {
            (port.get("host_ip"), port["published"], port["target"])
            for port in ports
        }
        self.assertEqual(expected_bindings, actual_bindings)

    def test_operational_skills_keep_executable_boundaries(self) -> None:
        site = _ROOT.joinpath("core/skills/site-report/SKILL.md").read_text(encoding="utf-8")
        writer = _ROOT.joinpath("core/skills/kb-write/SKILL.md").read_text(encoding="utf-8")
        session = _ROOT.joinpath("core/skills/kb-session/SKILL.md").read_text(encoding="utf-8")
        infra = _ROOT.joinpath("core/skills/kb-infra/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("`${OMH_SITES_ROOT:-$HOME/projects/sites}`", site)
        self.assertIn("Use pt-BR for report prose", " ".join(site.split()))
        slug_pipeline = (
            "tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-\\n' '-' | "
            "sed 's/--*/-/g; s/^-//; s/-$//'"
        )
        self.assertIn(slug_pipeline, " ".join(writer.split()))
        self.assertIn("DEJA_INCLUDE_SUBAGENTS=1", session)
        self.assertIn("~/.claude/projects/<cwd-munged>/<session-id>.jsonl", session)

        bootstrap_contract = (
            'KB_RUNTIME="${OMH_KB_RUNTIME:-$HOME/.local/share/omh-kb}"',
            'KB_VENV="$KB_RUNTIME/venv"',
            'uv venv "$KB_VENV"',
            'uv pip install --python "$KB_VENV/bin/python" FlagEmbedding qdrant-client PyYAML',
            'python3 -m venv "$KB_VENV"',
            '"$KB_VENV/bin/python" -m pip install FlagEmbedding qdrant-client PyYAML',
            '"$KB_VENV/bin/python" - <<',
            'BGEM3FlagModel(',
            'return_colbert_vecs=False',
            'len(output["dense_vecs"][0]) == 1024',
            'len(indices) == len(values) and len(indices) > 0',
            "docker compose -f <resolved-skill-dir>/docker-compose.yml up -d",
        )
        for contract in bootstrap_contract:
            with self.subTest(contract=contract):
                self.assertIn(contract, infra)
        ordered_health = (
            "docker info",
            "docker ps",
            "http://127.0.0.1:6333/healthz",
            "collection/vector/index schema",
            "short embedding",
        )
        positions = [infra.index(token) for token in ordered_health]
        self.assertEqual(sorted(positions), positions)

    def _yaml_name(self, path: Path) -> str:
        match = re.search(r"^name:\s*([^\s]+)", path.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertIsNotNone(match, str(path))
        return match.group(1) if match else ""

    def _toml_name(self, path: Path) -> str:
        match = re.search(r'^name\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertIsNotNone(match, str(path))
        return match.group(1) if match else ""

    def _run_codex(
        self,
        env: dict[str, str],
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ("codex", *arguments),
            cwd=_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)
        return completed

    def _run_codex_app_server(
        self,
        env: dict[str, str],
        params: dict[str, object],
    ) -> dict[str, object]:
        process = subprocess.Popen(
            ("codex", "app-server", "--stdio"),
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        assert process.stdin is not None
        assert process.stdout is not None

        def send(message: dict[str, object]) -> None:
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()

        def receive(response_id: int) -> dict[str, object]:
            while True:
                readable, _, _ = select.select([process.stdout], [], [], 10)
                self.assertTrue(readable, f"timed out waiting for response {response_id}")
                line = process.stdout.readline()
                self.assertTrue(line, f"app-server closed before response {response_id}")
                message = json.loads(line)
                if message.get("id") == response_id:
                    return message

        try:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "clientInfo": {
                            "name": "oh-my-harness-tests",
                            "version": "1.0.0",
                        }
                    },
                }
            )
            initialize = receive(1)
            self.assertNotIn("error", initialize)
            send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "hooks/list",
                    "params": params,
                }
            )
            response = receive(2)
            self.assertNotIn("error", response)
            return response["result"]
        finally:
            process.terminate()
            process.communicate(timeout=5)
