from __future__ import annotations

import importlib
import shlex
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import cast

_PARSERS = ("tomllib", "tomli")


@dataclass(frozen=True)
class TomlBackend:
    """Provides a complete TOML parser without coupling the core installer to it."""

    _loads: Callable[[str], dict[str, object]]

    @classmethod
    def load(cls) -> "TomlBackend":
        for name in _PARSERS:
            try:
                return cls(cls._loader(importlib.import_module(name)))
            except ModuleNotFoundError:
                continue
        raise RuntimeError(cls._bootstrap_message())

    @classmethod
    def available(cls) -> bool:
        try:
            cls.load()
        except RuntimeError:
            return False
        return True

    def parse(self, content: str) -> dict[str, object]:
        return self._loads(content)

    @staticmethod
    def _loader(module: ModuleType) -> Callable[[str], dict[str, object]]:
        loads = getattr(module, "loads", None)
        if not callable(loads):
            raise RuntimeError(f"full TOML parser has no loads function: {module}")
        return cast(Callable[[str], dict[str, object]], loads)

    @staticmethod
    def _bootstrap_message() -> str:
        requirements = Path(__file__).resolve().parents[1] / "requirements-mcp-import.txt"
        executable = shlex.quote(sys.executable)
        dependency_file = shlex.quote(str(requirements))
        return (
            "full TOML parser unavailable; no files were changed. "
            "Install the pinned optional dependency explicitly with: "
            f"{executable} -m pip install --requirement {dependency_file}"
        )
