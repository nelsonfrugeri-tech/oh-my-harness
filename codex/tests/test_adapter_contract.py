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
        guidance = _ROOT.joinpath("codex/AGENTS.md").read_text(encoding="utf-8")

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
        self.assertEqual(["./skills/", "./codex/skills/"], codex["skills"])
        self.assertEqual(["./claude-code/skills/"], claude["skills"])
        self.assertTrue(_ROOT.joinpath("hooks/hooks.json").is_file())

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
            path for path in _ROOT.joinpath("skills").iterdir() if path.is_dir()
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
                for path in _ROOT.joinpath("skills").iterdir()
                if path.is_dir()
            }
            codex_skills = {
                path.name
                for path in _ROOT.joinpath("codex/skills").iterdir()
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
            self.assertTrue(installed.joinpath("codex/skills/codex/SKILL.md").is_file())
            didactic_visual = installed.joinpath(
                "skills/didactic-visual/SKILL.md"
            ).read_text(encoding="utf-8")
            self.assertIn("ausência não é um blocker", didactic_visual)
            self.assertTrue(installed.joinpath("hooks/hooks.json").is_file())

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
                {"preToolUse", "sessionStart"},
                {hook["eventName"] for hook in plugin_hooks},
            )
            quality_gate = next(
                hook for hook in plugin_hooks if hook["eventName"] == "preToolUse"
            )
            self.assertEqual("Bash", quality_gate["matcher"])
            self.assertIn(str(installed), quality_gate["command"])
            self.assertNotIn("CLAUDE_PLUGIN_ROOT", quality_gate["command"])

    def test_plugin_hooks_use_the_codex_schema_and_standalone_instructions(self) -> None:
        hooks = json.loads(_ROOT.joinpath("hooks/hooks.json").read_text(encoding="utf-8"))
        handlers = [
            handler
            for groups in hooks["hooks"].values()
            for group in groups
            for handler in group["hooks"]
        ]
        context_loader = _ROOT.joinpath("hooks/context-load.sh").read_text(encoding="utf-8")

        quality_gate = next(
            handler for handler in handlers if "quality-gate.sh" in handler["command"]
        )
        self.assertEqual("Bash(git commit*)", quality_gate["if"])
        self.assertIn("Execute a skill `explorer`", context_loader)
        self.assertIn("modo **FULL**", context_loader)
        self.assertNotIn("Run the `explorer` skill", context_loader)

    def test_codex_global_guidance_is_pt_br_and_below_the_default_limit(self) -> None:
        guidance = _ROOT.joinpath("codex/AGENTS.md").read_text(encoding="utf-8")

        self.assertLessEqual(len(guidance.encode("utf-8")), 32 * 1024)
        self.assertIn("## Idioma", guidance)
        self.assertIn("## Nunca poluir um projeto com arquivos que não são do produto", guidance)
        self.assertIn("## Ambiente e adapters de capability", guidance)
        self.assertIn("### Fatos vinculantes do ambiente", guidance)
        self.assertIn("### Regras de conhecimento", guidance)
        self.assertIn("## Autoavaliação antes de responder", guidance)
        self.assertIn("## Padrões de código obrigatórios", guidance)
        self.assertIn("## Fluxo de commit", guidance)
        self.assertIn("## Trabalho de longa duração", guidance)
        portuguese_prose = (
            "Na dúvida, busque antes de responder.",
            "Antes de escrever, modificar ou revisar código",
            "Quando o usuário pedir um commit:",
            "Delegue uma tarefa substancial, bem delimitada e não interativa",
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
            for path in _ROOT.glob("agents/**/*.md")
            if path.name != "claude-code.md"
        }
        adapters = {
            self._toml_name(path)
            for path in _ROOT.glob("codex/agents/*.toml")
            if path.name != "codex.toml"
        }
        self.assertEqual(shared, adapters)

    def test_skill_leaf_names_are_unique_for_codex(self) -> None:
        sources = (
            *_ROOT.glob("skills/**/SKILL.md"),
            *_ROOT.glob("codex/skills/**/SKILL.md"),
        )
        names = [path.parent.name for path in sources]
        self.assertEqual(len(names), len(set(names)))

    def test_feature_skill_uses_portable_orchestration(self) -> None:
        content = _ROOT.joinpath("skills/feature/SKILL.md").read_text(encoding="utf-8")
        forbidden = ("Workflow({", "AskUserQuestion", "use the tool `Agent`")
        self.assertFalse(any(token in content for token in forbidden))
        self.assertIn("Portable orchestration contract", content)

    def test_engineering_agents_load_the_evidence_skill(self) -> None:
        roles = ("ai-engineer", "architect", "developer", "qa", "sre", "tech-pm")

        for role in roles:
            with self.subTest(role=role):
                shared = _ROOT.joinpath(f"agents/engineers/{role}.md").read_text(
                    encoding="utf-8"
                )
                codex = _ROOT.joinpath(f"codex/agents/{role}.toml").read_text(
                    encoding="utf-8"
                )
                self.assertIn("  - evidence", shared)
                self.assertIn("`evidence`", codex)

    def test_langchain_agents_reference_the_official_skills_and_docs(self) -> None:
        roles = ("ai-engineer", "developer", "architect")
        required = (
            "`langchain-skills`",
            "`langchain-mcp`",
            "confirme que eles aparecem entre as skills e tools disponíveis no runtime",
            "não tente usá-lo nem diga que o usou",
            "langchain-skills:ecosystem-primer",
            "langchain-skills:langchain-fundamentals",
            "langchain-skills:langgraph-fundamentals",
            "langchain-skills:deep-agents-core",
            "langchain-skills:langchain-python-quickstart",
            "langchain-skills:eval-engineering",
            "langchain-skills:swarm",
        )

        for role in roles:
            with self.subTest(role=role):
                content = _ROOT.joinpath(f"codex/agents/{role}.toml").read_text(
                    encoding="utf-8"
                )
                self.assertTrue(all(skill in content for skill in required))

    def test_qa_agent_guards_unavailable_langchain_integrations(self) -> None:
        content = _ROOT.joinpath("codex/agents/qa.toml").read_text(encoding="utf-8")
        self.assertIn("`langchain-skills:*`", content)
        self.assertIn("`langchain-mcp`", content)
        self.assertIn("não tente usá-lo nem diga que o usou", content)

    def test_eval_agents_guard_and_route_to_the_official_skills(self) -> None:
        roles = ("ai-engineer", "developer", "architect", "qa")
        required = (
            "`evals:*` aparece entre as skills disponíveis no runtime",
            "não tente invocá-la nem diga que a usou",
            "`evals:start`",
            "`evals:eval-audit`",
            "`evals:error-discovery`",
            "`evals:generate-synthetic-data`",
            "`evals:write-judge-prompt`",
            "`evals:validate-evaluator`",
            "`evals:evaluate-rag`",
            "`evals:build-review-interface`",
        )

        for role in roles:
            with self.subTest(role=role):
                content = _ROOT.joinpath(f"codex/agents/{role}.toml").read_text(
                    encoding="utf-8"
                )
                self.assertTrue(all(skill in content for skill in required))

    def test_shared_agents_route_langchain_work_to_the_official_skills(self) -> None:
        # The shared agents carry the same routing as the Codex TOMLs, but they name most
        # skills inside a table under a stated `langchain-skills:` prefix instead of
        # repeating the prefix on every entry. Pinning the bare names is what the file
        # actually contains; requiring the prefixed form would fail on correct content.
        roles = ("ai-engineer", "architect", "developer")
        required = (
            "`langchain-skills`",
            "`langchain-mcp`",
            "langchain-skills:ecosystem-primer",
            "`langchain-fundamentals`",
            "`langchain-rag`",
            "`langgraph-fundamentals`",
            "`deep-agents-core`",
            "`langchain-python-quickstart`",
            "`eval-engineering`",
            "`swarm`",
        )

        for role in roles:
            content = _ROOT.joinpath(f"agents/engineers/{role}.md").read_text(
                encoding="utf-8"
            )
            for skill in required:
                with self.subTest(role=role, skill=skill):
                    self.assertIn(skill, content)

    def test_shared_agents_route_llm_evaluation_to_the_official_skills(self) -> None:
        roles = ("ai-engineer", "qa")
        required = (
            "`evals`",
            "evals:start",
            "`error-discovery`",
            "`eval-audit`",
            "`write-judge-prompt`",
            "`validate-evaluator`",
            "`generate-synthetic-data`",
            "`build-review-interface`",
            "`evaluate-rag`",
        )

        for role in roles:
            content = _ROOT.joinpath(f"agents/engineers/{role}.md").read_text(
                encoding="utf-8"
            )
            for skill in required:
                with self.subTest(role=role, skill=skill):
                    self.assertIn(skill, content)

    def test_ai_engineer_separates_the_two_evaluation_toolchains(self) -> None:
        # `ai-engineer` is the only agent that routes to both eval toolchains, so it is where
        # picking the wrong one is likeliest. The disambiguation is the load-bearing part of
        # that section: without it the agent has two plausible routes and no rule to choose.
        # Asserted against whitespace-normalized text so re-wrapping the paragraph, which
        # changes no meaning, cannot fail the test.
        content = _ROOT.joinpath("agents/engineers/ai-engineer.md").read_text(
            encoding="utf-8"
        )
        flat = " ".join(content.split())

        self.assertIn("`langchain-skills:eval-engineering`", flat)
        self.assertIn("agnóstica de framework", flat)
        self.assertIn("O discriminador é o Harbor", flat)

    def test_agents_routing_to_third_party_plugins_declare_the_degraded_path(self) -> None:
        # Every agent that routes to a third-party plugin states what to do when the plugin
        # is absent, because absence is what actually happens: an uninstalled or failed
        # plugin contributes no skills and raises no error, so the routing prose would
        # otherwise send the agent after something that is silently not there.
        roles = ("ai-engineer", "qa", "architect", "developer")

        for role in roles:
            with self.subTest(role=role):
                flat = " ".join(
                    _ROOT.joinpath(f"agents/engineers/{role}.md")
                    .read_text(encoding="utf-8")
                    .split()
                )
                self.assertIn("não há erro, só ausência", flat)
                self.assertIn("nunca cite como usada uma skill que não carregou", flat)
                self.assertIn("declare a integração pendente", flat)
                self.assertIn("Passo 5 da skill `claude-code`", flat)

    def test_codex_agents_use_pt_br_operational_prose(self) -> None:
        required = {
            "ai-engineer": "Você é um senior AI/ML engineer",
            "architect": "Você é um senior software architect",
            "codex": "Use a skill instalada `codex` como runbook.",
            "context": "Você orquestra o ciclo de vida",
            "developer": "Você é um senior software engineer",
            "evidence-reviewer": "Realize uma auditoria independente",
            "graphify": "Você orquestra graphify",
            "knowledge-base": "Você orquestra a knowledge base",
            "qa": "Você é um quality assurance engineer",
            "site": "Use a skill instalada `site-report`",
            "sre": "Você é um site reliability engineer",
            "tech-pm": "Você é um technical product manager",
        }

        for role, prose in required.items():
            with self.subTest(role=role):
                content = _ROOT.joinpath(f"codex/agents/{role}.toml").read_text(
                    encoding="utf-8"
                )
                self.assertIn(prose, content)
                self.assertNotIn("You are ", content)

    def test_kb_write_requires_machine_and_session_provenance(self) -> None:
        content = _ROOT.joinpath("skills/kb-write/SKILL.md").read_text(
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
        self.assertIn("não escreva a nota", " ".join(content.split()))
        self.assertIn("MAC address bruto", content)

    def test_kb_session_record_carries_nullable_runtime_metadata(self) -> None:
        content = _ROOT.joinpath("skills/kb-session/SKILL.md").read_text(
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
        self.assertIn("campos existem no schema mesmo quando o valor é `null`", content)
        self.assertIn("contiver apenas whitespace", content)
        self.assertIn("todo path não nulo devem ser absolutos", content)

    def test_kb_legacy_session_records_have_a_lossless_v3_migration(self) -> None:
        session = _ROOT.joinpath("skills/kb-session/SKILL.md").read_text(
            encoding="utf-8"
        )
        infra = _ROOT.joinpath("skills/kb-infra/SKILL.md").read_text(
            encoding="utf-8"
        )
        session_flat = " ".join(session.split())
        infra_flat = " ".join(infra.split())
        for phrase in (
            "projeta cada campo ausente no payload Qdrant como `null`",
            "nunca reescreve o JSON histórico",
            "nunca atribui a máquina atual a uma sessão passada",
            "promova-o ao schema v3 somente com valores observados",
            "preserve o record legacy sem alteração",
        ):
            self.assertIn(phrase, session_flat)
        self.assertIn("continue o lote", infra_flat)
        self.assertIn("O reindex nunca modifica o JSON", infra_flat)

    def test_kb_session_schema_matches_qdrant_provenance_payload(self) -> None:
        session = _ROOT.joinpath("skills/kb-session/SKILL.md").read_text(
            encoding="utf-8"
        )
        infra = _ROOT.joinpath("skills/kb-infra/SKILL.md").read_text(
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
            r'\| Payload por ponto \(`kind: "session"`\) \| ([^|]+) \|', infra
        )

        self.assertIsNotNone(schema_match)
        self.assertIsNotNone(payload_match)
        schema_fields = set(json.loads(schema_match.group(1)))
        payload_fields = set(re.findall(r"`([^`]+)`", payload_match.group(1)))
        expected_payload_fields = (schema_fields - {"description", "resume"}) | {"kind"}

        self.assertTrue(provenance_fields <= schema_fields)
        self.assertEqual(expected_payload_fields, payload_fields)

    def test_kb_qdrant_indexes_provenance_fields(self) -> None:
        content = _ROOT.joinpath("skills/kb-infra/SKILL.md").read_text(
            encoding="utf-8"
        )
        indexed_fields = (
            '"harness"',
            '"session_id"',
            '"session_name"',
            '"machine_id"',
            '"machine_label"',
        )

        self.assertTrue(all(field in content for field in indexed_fields))
        self.assertIn("PayloadSchemaType.KEYWORD", content)

    def test_kb_retrieval_can_filter_by_provenance(self) -> None:
        content = _ROOT.joinpath("skills/kb-retrieval/SKILL.md").read_text(
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
        self.assertIn("Pontos legacy", content)

    def test_kb_agents_enforce_provenance_before_writing(self) -> None:
        shared = _ROOT.joinpath("agents/tools/knowledge-base.md").read_text(
            encoding="utf-8"
        )
        codex = _ROOT.joinpath("codex/agents/knowledge-base.toml").read_text(
            encoding="utf-8"
        )

        for content in (shared, codex):
            self.assertIn("provenance", content)
            self.assertIn("identity.json", content)
            self.assertIn("não escreva", content)

    def test_site_skills_are_harness_neutral(self) -> None:
        paths = (
            _ROOT / "skills/site-report/SKILL.md",
            _ROOT / "skills/site-expose/SKILL.md",
        )
        content = "\n".join(path.read_text(encoding="utf-8") for path in paths)

        self.assertFalse(any(token in content for token in ("CLAUDE.md", "Explore", "dataviz")))
        self.assertIn("abstract `tunnel` capability", content)
        self.assertIn("[a-z0-9]+(?:-[a-z0-9]+)*", content)
        self.assertIn("https://", content)

    def test_codex_adapter_does_not_duplicate_the_plugin_session_start(self) -> None:
        data = json.loads(_ROOT.joinpath("codex/hooks.json").read_text(encoding="utf-8"))
        self.assertEqual({}, data["hooks"])

    def test_context_loader_is_shared_and_executable(self) -> None:
        loader = _ROOT / "hooks/context-load.sh"
        claude_adapter = _ROOT / "claude-code/hooks/context-load.sh"

        self.assertTrue(loader.is_file())
        self.assertTrue(loader.stat().st_mode & 0o111)
        self.assertIn("../../hooks/context-load.sh", claude_adapter.read_text(encoding="utf-8"))

    def test_context_agents_resolve_the_git_root(self) -> None:
        shared = _ROOT.joinpath("agents/tools/context.md").read_text(encoding="utf-8")
        codex = _ROOT.joinpath("codex/agents/context.toml").read_text(encoding="utf-8")

        self.assertIn("git rev-parse --show-toplevel", shared)
        self.assertIn("git rev-parse --show-toplevel", codex)

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
