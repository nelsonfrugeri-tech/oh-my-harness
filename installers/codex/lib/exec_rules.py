from __future__ import annotations

import shutil
from typing import Type

from lib.atomic_file import atomic_write
from lib.layout import InstallLayout
from lib.shared_policy import RULES_HEADER, load_policy, render_codex_rules


class ManagedExecRules:
    """Own ~/.codex/rules/oh-my-harness.rules, rendered from the canonical permission policy."""

    def __init__(self, layout: InstallLayout, conflict: Type[RuntimeError]) -> None:
        self._target = layout.rules_file
        self._policy = layout.policy_file
        self._conflict = conflict

    def preflight(self) -> None:
        self._render()
        self._require_managed()

    def install(self) -> str:
        rendered = self._render()
        self._require_managed()
        if self._target.exists() and self._target.read_text(encoding="utf-8") == rendered:
            return f"ok: {self._target}"
        self._target.parent.mkdir(parents=True, exist_ok=True)
        self._backup_once()
        atomic_write(self._target, rendered)
        return f"atualizado: {self._target}"

    def validate(self) -> str:
        if not self._target.exists():
            raise self._conflict(f"regras de execução gerenciadas ausentes: {self._target}")
        if self._target.read_text(encoding="utf-8") != self._render():
            raise self._conflict(f"regras de execução gerenciadas desatualizadas: {self._target}")
        return f"ok: {self._target}"

    def _render(self) -> str:
        return render_codex_rules(load_policy(self._policy))

    def _require_managed(self) -> None:
        if not self._target.exists():
            return
        first_line = self._target.read_text(encoding="utf-8").split("\n", 1)[0]
        if first_line != RULES_HEADER:
            raise self._conflict(
                f"recusando substituir {self._target}: arquivo sem o cabeçalho omh-managed"
            )

    def _backup_once(self) -> None:
        if not self._target.exists():
            return
        backup = self._target.with_suffix(self._target.suffix + ".omh.bak")
        if not backup.exists():
            shutil.copy2(self._target, backup)
