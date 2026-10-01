from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "core/skills/kb-write/scripts/kb"
ALLOWED = {
    "cli": {"cli", "app", "adapters", "note", "entities", "search"},
    "app": {"app", "note", "entities", "search"},
    "adapters": {"adapters", "app", "note", "entities", "search"},
    "note": {"note"},
    "entities": {"entities"},
    "search": {"search", "note", "entities"},
}
FORBIDDEN = {"os", "io", "pathlib", "socket", "subprocess", "urllib.request"}


def violations(source: str, layer: str) -> list[str]:
    tree = ast.parse(source)
    errors = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.end_lineno - node.lineno + 1 > 50:
                errors.append(f"function {node.name} exceeds 50 lines")
        for module in _imports(node, layer):
            if module.startswith("kb."):
                target = module.split(".")[1]
                target = target if target in ALLOWED else "cli"
                if target not in ALLOWED[layer]:
                    errors.append(f"{layer} imports {target}")
            elif layer in {"note", "entities", "search"}:
                if module.split(".")[0] not in sys.stdlib_module_names:
                    errors.append(f"domain imports external {module}")
                if any(module == x or module.startswith(x + ".") for x in FORBIDDEN):
                    errors.append(f"domain imports I/O {module}")
        if isinstance(node, ast.ClassDef):
            errors.extend(_class_errors(node))
    return errors


def _imports(node: ast.AST, layer: str) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom) and node.module:
        if node.level == 1:
            return (f"kb.{layer}.{node.module}",)
        if node.level == 2:
            return (f"kb.{node.module}",)
        return (node.module,)
    return ()


def _class_errors(node: ast.ClassDef) -> list[str]:
    bases = [ast.unparse(base) for base in node.bases]
    if bases and any(base.endswith(("Protocol", "Port")) for base in bases):
        return []
    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)
               and not n.name.startswith("_")
               and not any(isinstance(d, ast.Name) and d.id == "property"
                           for d in n.decorator_list)]
    return [f"class {node.name} exceeds 3 public methods"] if len(methods) > 3 else []


class KnowledgeBaseArchitectureTest(unittest.TestCase):
    def test_package_obeys_declared_dependency_and_size_contract(self):
        self.assertTrue(PACKAGE.is_dir(), "KB package has not been implemented")
        for path in PACKAGE.rglob("*.py"):
            relative = path.relative_to(PACKAGE)
            layer = relative.parts[0] if len(relative.parts) > 1 else "cli"
            with self.subTest(path=str(relative)):
                self.assertEqual([], violations(path.read_text(), layer))

    def test_checker_rejects_outward_imports(self):
        self.assertIn("note imports adapters", violations("import kb.adapters.filesystem", "note"))
        self.assertTrue(violations("import pathlib", "entities"))

    def test_checker_rejects_long_function(self):
        self.assertTrue(violations("def long():\n" + "    pass\n" * 50, "app"))

    def test_checker_rejects_method_cap_and_allows_declared_protocol(self):
        methods = "".join(f"    def method{i}(self): pass\n" for i in range(4))
        self.assertTrue(violations("class Stateful:\n" + methods, "app"))
        self.assertEqual([], violations("class Adapter(StorePort):\n" + methods, "adapters"))
