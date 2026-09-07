from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Final, Type

from lib.atomic_file import atomic_write
from lib.layout import InstallLayout
from lib.toml_sections import split_root, top_level_lines


_SELECTION_START: Final = "# omh-managed: permissions-selection:start"
_SELECTION_END: Final = "# omh-managed: permissions-selection:end"
_PROFILE_START: Final = "# omh-managed: permissions-profile:start"
_PROFILE_END: Final = "# omh-managed: permissions-profile:end"
_CONFLICTING_ROOT_KEY: Final = re.compile(
    r'''(?mx)^\s*(?:
        default_permissions|approval_policy|approvals_reviewer|sandbox_mode|
        "(?:default_permissions|approval_policy|approvals_reviewer|sandbox_mode)"|
        '(?:default_permissions|approval_policy|approvals_reviewer|sandbox_mode)'
    )\s*='''
)
_CONFLICTING_PROFILE: Final = re.compile(
    r'''(?mx)^\s*(?:\[\[?\s*)?
    (?:permissions|"permissions"|'permissions')\s*\.\s*
    (?:oh-my-harness|"oh-my-harness"|'oh-my-harness')'''
)
_CONFLICTING_PERMISSIONS_ROOT: Final = re.compile(
    r'''(?mx)^\s*(?:
        (?:permissions|"permissions"|'permissions')\s*=|
        \[\[?\s*(?:permissions|"permissions"|'permissions')\s*\]\]?
    )'''
)
_CONFLICTING_LEGACY: Final = re.compile(
    r'''(?mx)^\s*(?:\[\[?\s*)?
    (?:sandbox_workspace_write|"sandbox_workspace_write"|'sandbox_workspace_write')
    \s*(?:[.=]|\])'''
)


class ManagedPermissions:
    def __init__(self, layout: InstallLayout, conflict: Type[RuntimeError]) -> None:
        self._target = layout.config_file
        self._conflict = conflict

    def preflight(self) -> None:
        self._render(self._current())

    def install(self) -> str:
        rendered = self._render(self._current())
        if self._target.exists() and self._target.read_text(encoding="utf-8") == rendered:
            return f"ok: {self._target}"
        self._backup_once()
        atomic_write(self._target, rendered)
        return f"atualizado: {self._target}"

    def validate(self) -> str:
        current = self._current()
        if current != self._render(current):
            raise self._conflict("permission profile gerenciado está ausente ou desatualizado")
        return f"ok: {self._target}"

    def _current(self) -> str:
        return self._target.read_text(encoding="utf-8") if self._target.exists() else ""

    def _backup_once(self) -> None:
        if not self._target.exists():
            return
        backup = self._target.with_suffix(self._target.suffix + ".omh.bak")
        if not backup.exists():
            shutil.copy2(self._target, backup)

    def _render(self, current: str) -> str:
        unmanaged = self._without_managed_blocks(current)
        self._reject_conflicts(unmanaged)
        root, tables = split_root(unmanaged)
        sections = (root.rstrip(), self._selection(), tables.strip(), self._profile())
        return "\n\n".join(section for section in sections if section) + "\n"

    def _without_managed_blocks(self, content: str) -> str:
        result = content
        for start, end in (
            (_SELECTION_START, _SELECTION_END),
            (_PROFILE_START, _PROFILE_END),
        ):
            if (start in result) != (end in result):
                raise self._conflict("config.toml contém um bloco de permissions incompleto")
            if start in result:
                before, remainder = result.split(start, 1)
                _, after = remainder.split(end, 1)
                result = before.rstrip() + "\n" + after.lstrip("\n")
        return result

    def _reject_conflicts(self, content: str) -> None:
        root, _ = split_root(content)
        root_statements = "\n".join(top_level_lines(root))
        statements = "\n".join(top_level_lines(content))
        conflicts = (
            _CONFLICTING_ROOT_KEY.search(root_statements),
            _CONFLICTING_PROFILE.search(statements),
            _CONFLICTING_PERMISSIONS_ROOT.search(statements),
            _CONFLICTING_LEGACY.search(statements),
        )
        if any(conflicts):
            raise self._conflict("config.toml já define uma política de permissions incompatível")

    def _selection(self) -> str:
        return "\n".join(
            (
                _SELECTION_START,
                'default_permissions = "oh-my-harness"',
                'approval_policy = "on-request"',
                'approvals_reviewer = "auto_review"',
                _SELECTION_END,
            )
        )

    def _profile(self) -> str:
        return "\n".join(
            (
                _PROFILE_START,
                "[permissions.oh-my-harness]",
                'description = "Workspace editing plus oh-my-harness knowledge storage."',
                'extends = ":workspace"',
                "",
                "[permissions.oh-my-harness.workspace_roots]",
                '"~/knowledge-base" = true',
                '"~/.local/share/omh-kb" = true',
                _PROFILE_END,
            )
        )
