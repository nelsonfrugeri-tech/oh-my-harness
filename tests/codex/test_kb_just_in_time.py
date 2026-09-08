"""Contract tests for the KB just-in-time rule, session-start pointer, and explorer onboarding.

Covers issue #134 (epic #113, wave 2, group F): a concrete-trigger KB rule in
CLAUDE.md/AGENTS.md, a one-line SessionStart pointer hook, and the explorer agent
as onboarding with a site report and a CLAUDE.md proposal.
"""

from __future__ import annotations

import json
import subprocess
import time
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]

_KB_RULE = (
    "**Consulte a knowledge base antes de responder sempre que o assunto for "
    "interno ou privado, e não público**: conhecimento do usuário, da empresa "
    "ou do projeto que não está no código nem no git; algo **episódico**, o "
    "que já foi feito, tentado ou discutido em sessões anteriores; ou uma "
    "**decisão** já tomada e o motivo dela. Faça isso pelo agent "
    "`knowledge-base`. Se a consulta não encontrar, diga que não encontrou; "
    "nunca preencha com suposição, e nunca responda de memória o que é "
    "privado."
)


class KbRuleContractTests(unittest.TestCase):
    def test_rule_is_identical_in_both_global_guidance_files(self) -> None:
        claude = _ROOT.joinpath("harness/claude/CLAUDE.md").read_text(encoding="utf-8")
        codex = _ROOT.joinpath("harness/codex/AGENTS.md").read_text(encoding="utf-8")

        self.assertIn(_KB_RULE, claude)
        self.assertIn(_KB_RULE, codex)

    def test_rule_lives_under_the_before_answering_heading(self) -> None:
        claude = _ROOT.joinpath("harness/claude/CLAUDE.md").read_text(encoding="utf-8")
        codex = _ROOT.joinpath("harness/codex/AGENTS.md").read_text(encoding="utf-8")

        claude_section = claude.split("## Antes de responder", 1)[1].split("\n---", 1)[0]
        codex_section = codex.split("## Autoavaliação antes de responder", 1)[1].split(
            "\n---", 1
        )[0]
        self.assertIn(_KB_RULE, claude_section)
        self.assertIn(_KB_RULE, codex_section)

    def test_rule_still_routes_public_knowledge_through_web(self) -> None:
        claude = _ROOT.joinpath("harness/claude/CLAUDE.md").read_text(encoding="utf-8")
        codex = _ROOT.joinpath("harness/codex/AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("capability `web`", claude)
        self.assertIn("capability `web`", codex)
        self.assertIn("citando a fonte", claude)
        self.assertIn("cite a fonte", codex)


class KbPointerHookContractTests(unittest.TestCase):
    _HOOK = _ROOT / "core/hooks/kb-pointer.sh"

    def _run(self, cwd: Path, kb_root: Path | None, env_extra: dict[str, str] | None = None):
        env: dict[str, str] = {"PATH": "/usr/bin:/bin:/usr/local/bin"}
        if kb_root is not None:
            env["OMH_KB_ROOT"] = str(kb_root)
        if env_extra:
            env.update(env_extra)
        payload = json.dumps({"cwd": str(cwd)})
        start = time.monotonic()
        result = subprocess.run(
            ["bash", str(self._HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            env=env,
            timeout=5,
        )
        elapsed = time.monotonic() - start
        return result, elapsed

    def _write_project_note(
        self, kb_root: Path, slug: str, name: str, repository_path: Path
    ) -> Path:
        identity_dir = kb_root / "work/projects" / slug / "identity"
        identity_dir.mkdir(parents=True, exist_ok=True)
        note = identity_dir / "2026-09-01--project-identity.md"
        note.write_text(
            "---\n"
            "knowledge_type: project\n"
            f"name: {name}\n"
            "aliases: []\n"
            f"repository_path: {repository_path}\n"
            "remote_url: null\n"
            "default_branch: main\n"
            "created_at: '2026-09-01T10:00:00Z'\n"
            "---\n\n"
            "Project identity note.\n",
            encoding="utf-8",
        )
        return note

    def _write_note(self, kb_root: Path, slug: str, topic: str, name: str, created_at: str) -> None:
        note_dir = kb_root / "work/projects" / slug / topic
        note_dir.mkdir(parents=True, exist_ok=True)
        (note_dir / name).write_text(
            "---\n"
            "knowledge_type: decision\n"
            f"created_at: {created_at}\n"
            "---\n\nBody.\n",
            encoding="utf-8",
        )

    def test_prints_note_count_and_latest_date_when_project_note_exists(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            kb_root = tmp_path / "kb"
            repo = tmp_path / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            self._write_project_note(kb_root, "sample", "sample", repo)
            self._write_note(kb_root, "sample", "decisions", "2026-09-01--a.md", "2026-09-01T10:00:00Z")
            self._write_note(kb_root, "sample", "decisions", "2026-09-03--b.md", "'2026-09-03T10:00:00Z'")

            result, elapsed = self._run(repo, kb_root)

            self.assertEqual(0, result.returncode)
            self.assertLess(elapsed, 2.0)
            line = result.stdout.strip()
            self.assertTrue(line)
            self.assertLess(len(line), 200)
            self.assertIn("KB deste projeto: 2 notas, última em 2026-09-03", line)
            self.assertIn("`knowledge-base`", line)
            self.assertNotIn(str(tmp_path), line)
            self.assertNotIn(str(repo), line)

    def test_falls_back_to_the_directory_named_after_the_repository_basename(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            kb_root = tmp_path / "kb"
            repo = tmp_path / "oh-my-harness"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            self._write_note(kb_root, "oh-my-harness", "decisions", "2026-09-05--a.md", "2026-09-05T10:00:00Z")

            result, elapsed = self._run(repo, kb_root)

            self.assertEqual(0, result.returncode)
            self.assertLess(elapsed, 2.0)
            line = result.stdout.strip()
            self.assertIn("KB deste projeto: 1 notas, última em 2026-09-05", line)
            self.assertNotIn(str(tmp_path), line)

    def test_prints_no_kb_message_when_project_is_not_found(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            kb_root = tmp_path / "kb"
            repo = tmp_path / "unknown-project"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

            result, elapsed = self._run(repo, kb_root)

            self.assertEqual(0, result.returncode)
            self.assertLess(elapsed, 2.0)
            line = result.stdout.strip()
            self.assertEqual(
                "Sem KB para este projeto; o `explorer` cria uma sob demanda", line
            )
            self.assertLess(len(line), 200)

    def test_silent_when_omh_runtime_is_set(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            kb_root = tmp_path / "kb"
            repo = tmp_path / "sample"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            self._write_project_note(kb_root, "sample", "sample", repo)
            self._write_note(kb_root, "sample", "decisions", "2026-09-01--a.md", "2026-09-01T10:00:00Z")

            result, elapsed = self._run(repo, kb_root, env_extra={"OMH_RUNTIME": "1"})

            self.assertEqual(0, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertLess(elapsed, 2.0)

    def test_excludes_index_log_and_legacy_context_notes_from_the_count(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            kb_root = tmp_path / "kb"
            repo = tmp_path / "sample"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            self._write_project_note(kb_root, "sample", "sample", repo)
            self._write_note(kb_root, "sample", "decisions", "2026-09-01--a.md", "2026-09-01T10:00:00Z")
            project_dir = kb_root / "work/projects/sample"
            (project_dir / "index.md").write_text("index\n", encoding="utf-8")
            (project_dir / "log.md").write_text("log\n", encoding="utf-8")
            (project_dir / "context.md").write_text("legacy context\n", encoding="utf-8")

            result, _ = self._run(repo, kb_root)

            self.assertIn("KB deste projeto: 1 notas", result.stdout)

    def test_hook_is_registered_in_both_harness_hooks_json(self) -> None:
        claude_hooks = json.loads(
            _ROOT.joinpath("harness/claude/hooks/hooks.json").read_text(encoding="utf-8")
        )
        codex_hooks = json.loads(
            _ROOT.joinpath("harness/codex/hooks/hooks.json").read_text(encoding="utf-8")
        )
        self.assertEqual(claude_hooks, codex_hooks)

        session_start = claude_hooks["hooks"]["SessionStart"]
        self.assertEqual(1, len(session_start))
        self.assertEqual("startup|resume", session_start[0]["matcher"])
        handler = session_start[0]["hooks"][0]
        self.assertIn("core/hooks/kb-pointer.sh", handler["command"])
        self.assertEqual(2, handler["timeout"])


class ExplorerOnboardingContractTests(unittest.TestCase):
    def _read(self, relative_path: str) -> str:
        return _ROOT.joinpath(relative_path).read_text(encoding="utf-8")

    def test_skill_no_longer_mentions_the_context_snapshot(self) -> None:
        contract = self._read("core/skills/explorer/SKILL.md")
        self.assertNotIn("context.md", contract)
        self.assertNotIn("context-load", contract)

    def test_skill_describes_the_three_onboarding_outputs(self) -> None:
        contract = " ".join(self._read("core/skills/explorer/SKILL.md").split())
        self.assertIn("site-report", contract)
        self.assertIn("CLAUDE.md", contract)
        self.assertIn("knowledge-base", contract)

    def test_skill_requires_approval_before_writing_the_claude_md_proposal(self) -> None:
        contract = " ".join(self._read("core/skills/explorer/SKILL.md").split())
        self.assertIn("approval", contract.lower())
        approval_index = contract.lower().index("approval")
        write_index = contract.lower().index("write")
        self.assertLessEqual(approval_index, contract.lower().rindex("write"))
        self.assertNotEqual(write_index, -1)

    def test_explorer_role_exists_with_the_tools_family(self) -> None:
        manifest = json.loads(_ROOT.joinpath("core/agents/routing.json").read_text(encoding="utf-8"))
        self.assertIn("explorer", manifest["roles"])
        self.assertEqual("tools", manifest["role_families"]["explorer"])
        role = manifest["roles"]["explorer"]
        self.assertEqual(
            ["evidence", "explorer", "site-report", "didactic-visual"],
            role["local_skills"],
        )
        overlay = manifest["adapter_specs"]["shared-markdown"]["overlays"]["explorer"]
        self.assertNotIn("Edit", overlay["tools"])

    def test_explorer_appears_in_the_plugin_agent_manifest(self) -> None:
        plugin = json.loads(_ROOT.joinpath(".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertIn("./harness/claude/agents/tools/explorer.md", plugin["agents"])


if __name__ == "__main__":
    unittest.main()
