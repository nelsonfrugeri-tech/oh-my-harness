from pathlib import Path
import unittest

_ROOT = Path(__file__).resolve().parents[2]


class KnowledgeRetirementTest(unittest.TestCase):
    def test_retired_writer_and_test_are_absent(self) -> None:
        retired = 'kb' + '-session'
        self.assertFalse((_ROOT / 'core/skills' / retired).exists())
        self.assertFalse((_ROOT / 'tests/codex' / ('test_kb_' + 'session_distillation_contract.py')).exists())

    def test_operational_surfaces_do_not_route_to_retired_writer(self) -> None:
        retired = 'kb' + '-session'
        roots = ['core/agents', 'agents', 'harness/codex/agents', 'core/skills',
                 'core/evals', 'website/src', 'architecture/presentation']
        for root in roots:
            for path in (_ROOT / root).rglob('*'):
                if path.is_file() and path.suffix in {'.md', '.json', '.toml', '.ts', '.astro', '.svg', '.excalidraw'}:
                    with self.subTest(path=path):
                        self.assertNotIn(retired, path.read_text(encoding='utf-8'))

    def test_both_harnesses_require_review_and_preserve_transcripts(self) -> None:
        for relative in ['harness/claude/CLAUDE.md', 'harness/codex/AGENTS.md']:
            text = (_ROOT / relative).read_text()
            with self.subTest(path=relative):
                for contract in ['`pending`', 'aprovação explícita', '`.history/`',
                                 'Não crie JSON de sessão', '`backup/INSTRUCTION.md`']:
                    self.assertIn(contract, text)


if __name__ == '__main__':
    unittest.main()
