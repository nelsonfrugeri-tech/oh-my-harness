from pathlib import Path
import os
import subprocess
import tempfile
import unittest

_ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return _ROOT.joinpath(path).read_text(encoding='utf-8')


class KnowledgeLayoutContractTest(unittest.TestCase):
    def test_user_approved_layout_and_identity_replace_topic_routing(self) -> None:
        text = read('core/skills/kb-write/SKILL.md')
        for rule in ('<scope>/<domain>/<entities...>/<name>/<name>.md',
                     'at most three words', 'without repeating the parent',
                     '`type` does not select the directory', 'identity/identity.md',
                     '`type: reference`', '`repository_path`', '`remote_url`', '`default_branch`'):
            self.assertIn(rule, text)

    def test_pending_review_and_frozen_history_are_binding(self) -> None:
        text = read('core/skills/kb-write/SKILL.md')
        for rule in ('principal session shows the entire note', 'explicit user approval',
                     'Changed content needs renewed', 'Pending is excluded',
                     '.history/<YYYY-MM-DD>--v<N>--<name>.md', 'superseded_reason',
                     'preserving id', 'created_at', 'increments version'):
            self.assertIn(rule, text)

    def test_generated_agents_share_collision_and_publication_rules(self) -> None:
        for path in ('agents/knowledge-base.md', 'harness/codex/agents/knowledge-base.toml'):
            text = read(path)
            with self.subTest(path=path):
                for rule in ('block domain collisions', 'instead of inventing alternate slugs',
                             'principal session', 'explicit user approval', 'kb.py',
                             'backup/INSTRUCTION.md', 'session-memory'):
                    self.assertIn(rule, text)


class KnowledgeEvidenceContractTest(unittest.TestCase):
    def test_structured_entities_keep_prose_and_transcript_evidence(self) -> None:
        text = read('core/skills/kb-write/SKILL.md')
        for rule in ('all thirteen keys', 'Entities row', 'role and relationship',
                     'transcript evidence', 'ISO 4217', 'RFC 3339', 'Inherited entities',
                     'new entities need current', 'Secrets', '--approved-degraded'):
            self.assertIn(rule, text)

    def test_sensitive_remote_policy_survives_all_boundaries(self) -> None:
        for skill in ('explorer', 'kb-write', 'kb-retrieval'):
            text = ' '.join(read(f'core/skills/{skill}/SKILL.md').split())
            for rule in ('HTTP(S) userinfo', 'query string', 'fragment', 'signed URL',
                         'ambiguous parsing', 'SSH/SCP transport username', '`remote_url: null`'):
                with self.subTest(skill=skill, rule=rule):
                    self.assertIn(rule, text)

    def test_exact_resolution_and_backup_instruction_precede_content(self) -> None:
        text = read('core/skills/kb-retrieval/SKILL.md')
        self.assertLess(text.index('## Resolve exact'), text.index('## Run the retrieval'))
        for rule in ('Multiple matches require disambiguation', 'never select the first match',
                     'Zero matches', 'Read `backup/INSTRUCTION.md` before any other file',
                     'only the first YAML frontmatter block', 'yaml.safe_load'):
            self.assertIn(rule, text)


class KnowledgeDiskNavigationTest(unittest.TestCase):
    def test_documented_inventory_prunes_history_pending_and_backup(self) -> None:
        text = read('core/skills/kb-retrieval/SKILL.md')
        command = next(line.strip().strip('`.') for line in text.splitlines()
                       if line.startswith('`KB_ROOT="$(python3') and 'find "$KB_ROOT/<domain>"' in line)
        command = command.replace('<skill-dir>', str(_ROOT / 'core/skills/kb-write'))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ('entity/note/note.md', 'entity/note/.history/old.md',
                             'entity/note/.pending/note.md', 'backup/old.md', 'index.md'):
                path = root / 'domain' / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            result = subprocess.run(command.replace('<domain>', 'domain'), shell=True, capture_output=True,
                                    text=True, check=True, env={**os.environ, 'OMH_KB_ROOT': str(root)})
            self.assertEqual([str(root / 'domain/entity/note/note.md')], result.stdout.splitlines())


if __name__ == '__main__':
    unittest.main()
