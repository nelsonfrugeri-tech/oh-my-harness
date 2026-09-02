from pathlib import Path
import unittest


_ROOT = Path(__file__).resolve().parents[2]


class KnowledgeBaseSessionDistillationContractTests(unittest.TestCase):
    def _read(self, relative_path: str) -> str:
        return _ROOT.joinpath(relative_path).read_text(encoding="utf-8")

    def test_session_domain_uses_git_root_instead_of_current_directory(self) -> None:
        session = " ".join(self._read("skills/kb-session/SKILL.md").split())

        self.assertIn("git -C <cwd> rev-parse --show-toplevel", session)
        self.assertIn("basename da raiz", session)
        self.assertIn("nunca o basename do `cwd`", session)
        self.assertIn("inclusive quando a sessão começa num subdiretório", session)
        self.assertIn("reutilize o slug canônico já registrado", session)
        self.assertIn("nunca desvie seu session record", session)

    def test_long_session_distillation_has_complete_auditable_coverage(self) -> None:
        session = self._read("skills/kb-session/SKILL.md")
        normalized = " ".join(session.split())
        write = self._read("skills/kb-write/SKILL.md")
        agents = (
            self._read("agents/tools/knowledge-base.md"),
            self._read("codex/agents/knowledge-base.toml"),
        )

        self.assertIn("Destilação integral de sessão", session)
        self.assertIn("ledger de cobertura", session)
        self.assertIn("intervalos cronológicos", session)
        self.assertIn("nenhum intervalo não processado", normalized)
        self.assertIn("parsing failure ou registro não classificado", session)
        self.assertIn("população total de registros", session)
        self.assertIn("detecte credentials, tokens, secrets, personal data", session)
        self.assertIn("obtenha confirmação humana antes de escrever", normalized)
        self.assertIn("collision gate de `kb-write`", session)
        self.assertIn("plano de notas", write)
        self.assertIn("create | supersede | skip", write)
        self.assertIn("idempotente", write)
        self.assertIn("distillation_key", write)
        self.assertIn("omh-kb-distillation-v1", write)
        self.assertIn("JSON UTF-8 canônico", write)
        self.assertIn("busca exata em disco", write)
        self.assertIn("destino já existe", write)
        self.assertIn("índices ancestrais", write)
        self.assertIn("estruturas mutáveis ou derivadas são reconciliadas", write)
        self.assertIn("seguida de `skip`", write)
        self.assertIn("uma nota por conhecimento", write)
        self.assertIn("`distillation_key`", self._read("skills/kb-infra/SKILL.md"))
        for agent in agents:
            with self.subTest(agent=agent[:80]):
                self.assertIn("destilar a sessão inteira", agent)
                self.assertIn("não cria notas automaticamente", agent)

    def test_readme_blocks_canonical_domain_collisions(self) -> None:
        readme = " ".join(self._read("README.md").split())

        self.assertIn("collision at the canonical domain blocks writes", readme)
        self.assertIn(
            "persistent resolver shared by note, context, and session writers",
            readme,
        )
        self.assertIn("a local alias is never created", readme)


if __name__ == "__main__":
    unittest.main()
