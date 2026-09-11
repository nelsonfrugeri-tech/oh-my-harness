from __future__ import annotations

import ast
import json
import re
import tokenize
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_PORTUGUESE = re.compile(
    r"[áàâãéêíóôõúç]|"
    r"\b(?:não|você|vocês|usuário|usuários|arquivo|arquivos|projeto|projetos|"
    r"resposta|respostas|quando|sempre|nunca|deve|devem|antes|depois|erro|falha|"
    r"instalar|instalação|sincronizar|configuração|permissão|recusando|gerenciado|"
    r"gerenciados|ausente|desatualizado|desatualizados|contém|incompleto|substituir|"
    r"diretório|alterações|nome|duplicado|duplica|indica|falhou|passou|"
    r"enviado|verificado|usar|responder|incluir|conectar|começar|recusar|omitir|"
    r"explicar|aplicar|declarar|interpretar|fabricar|identificar|considerar|pedir|"
    r"executar|registrar|limitar|classificar|propor|tratar|revalidar|verificar|"
    r"preservar|comparar|criticar|apresentar|oferecer|rejeitar|expor|confirmar|"
    r"exigir|adiar|tornar|separar|definir)\b",
    flags=re.IGNORECASE,
)


def _read(relative: str) -> str:
    return _ROOT.joinpath(relative).read_text(encoding="utf-8")


def _english_instruction_files() -> tuple[Path, ...]:
    files = {
        _ROOT / "README.md",
        _ROOT / "INSTRUCTIONS.md",
        _ROOT / "core/agents/routing.json",
    }
    for pattern in (
        "core/skills/**/*.md",
        "core/skills/**/agents/*.yaml",
        "agents/*.md",
        "harness/claude/skills/**/*.md",
        "harness/codex/agents/**/*.toml",
        "harness/codex/skills/**/*.md",
        "core/evals/*/README.md",
    ):
        files.update(_ROOT.glob(pattern))
    return tuple(
        sorted(
            path
            for path in files
            if "/assets/" not in path.as_posix() and not _belongs_to_vendored_skill(path)
        )
    )


def _belongs_to_vendored_skill(path: Path) -> bool:
    for parent in (path, *path.parents):
        skill = parent if parent.name == "SKILL.md" else parent / "SKILL.md"
        if skill.is_file() and re.search(
            r"(?m)^upstream_version:\s*\S+", skill.read_text(encoding="utf-8")
        ):
            return True
        if parent == _ROOT:
            break
    return False


def _literal_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            value.value
            for value in node.values
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        )
    return None


class LanguagePolicyTest(unittest.TestCase):
    def test_documented_language_matrix_covers_every_artifact_class(self) -> None:
        readme = _read("README.md")
        rows = (
            "| Skills, roles, agents, references, and `routing.json` | English |",
            "| Code, comments, docstrings, test messages, and repository documentation | English |",
            "| `harness/claude/CLAUDE.md` and `harness/codex/AGENTS.md` | pt-BR |",
            "| Text injected into a user session by hooks | pt-BR |",
            "| `prompt` and `required` fields in `core/evals/*/cases.json` | pt-BR |",
            "| Evaluation protocol README files | English |",
            "| Installer error messages shown to users | pt-BR |",
            "| Vendored third-party content | Original upstream language |",
        )

        for row in rows:
            with self.subTest(row=row):
                self.assertIn(row, readme)

    def test_english_instruction_surfaces_reject_portuguese_prose(self) -> None:
        for path in _english_instruction_files():
            with self.subTest(path=path.relative_to(_ROOT)):
                match = _PORTUGUESE.search(path.read_text(encoding="utf-8"))
                self.assertIsNone(match, f"unexpected pt-BR token: {match.group(0) if match else ''}")

    def test_response_language_instruction_is_exact(self) -> None:
        evidence = _read("core/skills/evidence/SKILL.md")

        self.assertEqual(
            1,
            evidence.count(
                "Respond in the user's language; keep established technical terms in English."
            ),
        )

    def test_global_guidance_and_eval_cases_are_pt_br(self) -> None:
        for relative in ("harness/claude/CLAUDE.md", "harness/codex/AGENTS.md"):
            with self.subTest(path=relative):
                self.assertGreaterEqual(len(_PORTUGUESE.findall(_read(relative))), 25)

        for path in sorted((_ROOT / "core/evals").glob("*/cases.json")):
            cases = json.loads(path.read_text(encoding="utf-8"))
            for case in cases:
                values = (case["prompt"], *case["required"])
                for value in values:
                    with self.subTest(path=path.relative_to(_ROOT), case=case["id"], value=value):
                        self.assertRegex(value, _PORTUGUESE)

    def test_every_hook_decision_message_is_explicitly_pt_br(self) -> None:
        hook = _read("core/hooks/quality-gate.sh")
        messages = re.findall(r'(?m)^\s*decide (?:allow|deny) "([^"\n]*)', hook)

        self.assertGreaterEqual(len(messages), 10)
        self.assertEqual(
            len(re.findall(r"(?m)^\s*decide (?:allow|deny)\b", hook)),
            len(messages),
        )
        for message in messages:
            with self.subTest(message=message):
                self.assertRegex(message, _PORTUGUESE)

    def test_installer_exception_messages_are_pt_br(self) -> None:
        messages: list[str] = []
        message_calls = {"InstallConflict", "ValueError", "_conflict"}
        for path in sorted((_ROOT / "installers/codex").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not node.args:
                    continue
                name = (
                    node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else getattr(node.func, "id", "")
                )
                if name not in message_calls:
                    continue
                message = _literal_text(node.args[0])
                if message is not None:
                    messages.append(message)

        self.assertGreaterEqual(len(messages), 20)
        for message in messages:
            with self.subTest(message=message):
                self.assertRegex(message, _PORTUGUESE)

    def test_source_comments_and_python_docstrings_are_english(self) -> None:
        python_files = tuple(sorted((_ROOT / "installers/codex").rglob("*.py")))
        for path in python_files:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            comments = (
                token.string
                for token in tokenize.generate_tokens(iter(source.splitlines(keepends=True)).__next__)
                if token.type == tokenize.COMMENT
            )
            docstrings = (
                value
                for node in ast.walk(tree)
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                if (value := ast.get_docstring(node, clean=False)) is not None
            )
            for prose in (*comments, *docstrings):
                with self.subTest(path=path.relative_to(_ROOT), prose=prose):
                    self.assertIsNone(_PORTUGUESE.search(prose))


if __name__ == "__main__":
    unittest.main()
