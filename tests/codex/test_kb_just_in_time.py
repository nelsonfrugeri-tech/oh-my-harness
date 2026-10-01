"""Contract tests for the KB just-in-time rule, session-start pointer, and explorer onboarding.

Covers issue #134 (epic #113, wave 2, group F): a concrete-trigger KB rule in
CLAUDE.md/AGENTS.md, a one-line SessionStart pointer hook, and the explorer agent
as onboarding with a site report and a CLAUDE.md proposal.
"""

from __future__ import annotations

import json
import re
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
        # Group E (#120) unified the heading: both files now use "Antes de responder".
        codex_section = codex.split("## Antes de responder", 1)[1].split("\n---", 1)[0]
        self.assertIn(_KB_RULE, claude_section)
        self.assertIn(_KB_RULE, codex_section)

    def test_rule_still_routes_public_knowledge_through_web(self) -> None:
        claude = _ROOT.joinpath("harness/claude/CLAUDE.md").read_text(encoding="utf-8")
        codex = _ROOT.joinpath("harness/codex/AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("capability `web`", claude)
        self.assertIn("capability `web`", codex)
        # Group E (#120) made the shared sections byte-identical, so the same
        # sentence must hold in both files.
        self.assertIn("responda citando a fonte", claude)
        self.assertIn("responda citando a fonte", codex)


class KbPointerHookContractTests(unittest.TestCase):
    _HOOK = _ROOT / 'core/hooks/kb-pointer.sh'

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.kb = self.root / 'kb'
        self.repo = self.root / 'project'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=self.repo, check=True)

    def _run(self, **extra):
        import os
        env = dict(os.environ, OMH_KB_ROOT=str(self.kb), **extra)
        start = time.monotonic()
        result = subprocess.run(['bash', str(self._HOOK)], input=json.dumps({'cwd': str(self.repo)}),
                                text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(time.monotonic() - start, 2)
        return result.stdout

    def _note(self, relative, *, status='active', date='2026-10-01T10:00:00Z', repository=None):
        path = self.kb / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        text = f'---\ntype: reference\nstatus: {status}\ncreated_at: "{date}"\n'
        if repository:
            text += f'repository_path: "{repository}"\n'
        path.write_text(text + '---\n\nA nota do projeto.\n')
        return path

    def test_repository_identity_precedes_directory_basename(self):
        self._note('work/different/identity/identity.md', repository=self.repo)
        self._note('work/different/notes/a/a.md')
        self._note('work/project/notes/b/b.md')
        output = self._run()
        self.assertIn('KB deste projeto: 2 notas, última em 2026-10-01', output)
        self.assertNotIn(str(self.root), output)

    def test_person_scope_and_canonical_repository_symlink_resolve(self):
        link = self.root / 'repo-link'
        link.symlink_to(self.repo, target_is_directory=True)
        self._note('person/personal/identity/identity.md', repository=link)
        self.assertIn('KB deste projeto: 1 notas', self._run())

    def test_directory_fallback_is_explicit(self):
        self._note('work/project/notes/a/a.md')
        self.assertIn('KB deste projeto (por diretório, sem nota de identidade): 1 notas', self._run())

    def test_only_active_reference_identity_resolves(self):
        for status in ('pending', 'deprecated', 'superseded'):
            self._note('work/other/identity/identity.md', repository=self.repo, status=status)
            self.assertIn('Sem KB para este projeto', self._run())

    def test_ambiguous_identity_and_directory_never_guess(self):
        for scope in ('work', 'person'):
            self._note(f'{scope}/other/identity/identity.md', repository=self.repo)
        self.assertIn('Sem KB para este projeto', self._run())
        for scope in ('work', 'person'):
            self._note(f'{scope}/project/a/a.md')
        self.assertIn('Sem KB para este projeto', self._run())

    def test_pending_warning_excludes_history_backup_and_reserved_files(self):
        self._note('work/project/identity/identity.md', repository=self.repo)
        self._note('work/project/new/new.md', status='pending')
        self._note('work/project/identity/.pending/identity.md', status='pending')
        self._note('work/project/old/.history/frozen.md', status='pending')
        self._note('work/project/backup/old/old.md', status='pending')
        self._note('work/project/index.md')
        self._note('work/project/INSTRUCTION.md')
        output = self._run()
        self.assertIn('1 notas, última em 2026-10-01', output)
        self.assertIn('2 notas pendentes de revisão', output)
        self.assertLess(len(output.strip()), 200)

    def test_only_pending_project_still_warns(self):
        self._note('work/project/new/new.md', status='pending')
        self.assertIn('1 notas pendentes de revisão', self._run())

    def test_impossible_dates_do_not_replace_latest_valid_date(self):
        self._note('work/project/first/first.md', date='2026-09-20T10:00:00Z')
        self._note('work/project/invalid/invalid.md', date='2026-99-99T10:00:00Z')
        self.assertIn('última em 2026-09-20', self._run())

    def test_nested_symlinks_are_not_traversed(self):
        self._note('work/project/a/a.md')
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'outside.md').write_text('---\nstatus: pending\n---\n')
        (self.kb / 'work/project/external').symlink_to(outside, target_is_directory=True)
        self.assertNotIn('pendentes', self._run())

    def test_runtime_is_silent(self):
        self.assertEqual('', self._run(OMH_RUNTIME='1'))

    def test_hundred_identity_notes_finish_within_hook_budget(self):
        for number in range(100):
            self._note(f'work/noise-{number}/identity/identity.md', repository=f'/missing/{number}')
        self._note('work/match/identity/identity.md', repository=self.repo)
        self.assertIn('KB deste projeto: 1 notas', self._run())

    def test_session_hook_is_registered_identically(self):
        paths = ('harness/claude/hooks/hooks.json', 'harness/codex/hooks/hooks.json')
        manifests = [json.loads((_ROOT / path).read_text()) for path in paths]
        self.assertEqual(manifests[0], manifests[1])
        hook = manifests[0]['hooks']['SessionStart'][0]
        self.assertEqual('startup|resume', hook['matcher'])
        self.assertEqual(2, hook['hooks'][0]['timeout'])


class ExplorerOnboardingContractTests(unittest.TestCase):
    def _read(self, relative_path: str) -> str:

        return _ROOT.joinpath(relative_path).read_text(encoding="utf-8")
    def test_global_guidance_separates_explorer_from_kb_ownership(self) -> None:
        explorer_row = (
            "| `explorer` | Mapear um repositório desconhecido e entregar site, proposta "
            "de `CLAUDE.md` e handoff de conhecimento | `explorer`, `site-report` |"
        )
        for guidance_path in ("harness/claude/CLAUDE.md", "harness/codex/AGENTS.md"):
            guidance = self._read(guidance_path)
            kb_row = next(line for line in guidance.splitlines() if line.startswith('| `knowledge-base` |'))
            for required in ('`kb-infra`', '`kb-write`', '`kb-retrieval`', 'versões'):
                self.assertIn(required, kb_row)
            self.assertNotIn('session records', kb_row)
            self.assertIn(explorer_row, guidance)

    def test_runbooks_distinguish_the_pointer_from_automatic_retrieval(self) -> None:
        claude_runbook = self._read("harness/claude/skills/claude-code/SKILL.md")
        codex_runbook = self._read("harness/codex/README.md")
        project_readme = self._read("README.md")

        self.assertNotIn("no longer provides any session-opening hook", claude_runbook)
        self.assertIn("plugin now provides the content-free KB pointer", claude_runbook)
        self.assertIn(
            "native plugin now supplies the content-free KB pointer", codex_runbook
        )
        self.assertIn("automatic content retrieval", project_readme)


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

    def test_skill_states_it_never_writes_the_claude_md_proposal_itself(self) -> None:
        contract = " ".join(self._read("core/skills/explorer/SKILL.md").split())
        self.assertIn("the calling thread writes the approved proposal, this skill never does", contract)

    def test_explorer_role_and_adapters_never_write_inside_the_repository(self) -> None:
        manifest = json.loads(_ROOT.joinpath("core/agents/routing.json").read_text(encoding="utf-8"))
        role = manifest["roles"]["explorer"]
        joined_contract = " ".join(role["operating_contract"]).lower()
        joined_boundaries = " ".join(role["boundaries"]).lower()
        self.assertIn("write only the external site", joined_contract)
        self.assertIn("never write it yourself", joined_contract)
        self.assertNotIn("write only the external site and, after explicit approval", joined_contract)
        self.assertIn(
            "do not write anything inside the analyzed repository", joined_boundaries
        )
        overlay = manifest["adapter_specs"]["shared-markdown"]["overlays"]["explorer"]
        self.assertIn("Write", overlay["tools"])
        self.assertNotIn("Edit", overlay["tools"])

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

    def test_explorer_is_discovered_by_the_plugin(self) -> None:
        plugin = json.loads(_ROOT.joinpath(".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("agents", plugin)
        self.assertTrue(_ROOT.joinpath("agents/explorer.md").is_file())


if __name__ == "__main__":
    unittest.main()
