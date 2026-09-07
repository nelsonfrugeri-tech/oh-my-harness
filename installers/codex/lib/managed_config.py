from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Final, Optional, Type, cast

from lib.atomic_file import atomic_write
from lib.capability_table import preserve_machine_capabilities
from lib.layout import InstallLayout


_START: Final = "<!-- omh-managed:start -->"
_END: Final = "<!-- omh-managed:end -->"
_HOOK_MARKER: Final = "omh-managed: context"


class ManagedConfig:
    def __init__(
        self,
        layout: InstallLayout,
        conflict: Type[RuntimeError],
        replace_global_agents: bool,
    ) -> None:
        self._layout = layout
        self._conflict = conflict
        self._replace_global_agents = replace_global_agents

    def install(self) -> tuple[str, ...]:
        return self._merge_global_agents(), self._merge_hooks()

    def preflight(self) -> None:
        target = self._layout.global_agents_file
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        if self._replace_global_agents and _START not in current and _END not in current:
            current = ""
        self._replace_managed_block(current, self._source_agents(current))
        self._source_hooks()
        hooks_target = self._layout.hooks_file
        if hooks_target.exists():
            self._hook_data(hooks_target.read_text(encoding="utf-8"))

    def validate(self) -> tuple[str, ...]:
        return self._check_managed_block(), self._check_hook()

    def _merge_global_agents(self) -> str:
        target = self._layout.global_agents_file
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        if self._replace_global_agents and _START not in current and _END not in current:
            current = ""
        source = self._source_agents(current)
        return self._write_if_changed(target, self._replace_managed_block(current, source))

    def _source_agents(self, current: str) -> str:
        source = self._layout.adapter.joinpath("AGENTS.md").read_text(encoding="utf-8").strip()
        managed = self._managed_content(current)
        if managed is None:
            return source
        return preserve_machine_capabilities(source, managed)

    def _merge_hooks(self) -> str:
        source = self._source_hooks()
        target = self._layout.hooks_file
        current = (
            self._hook_data(target.read_text(encoding="utf-8"))
            if target.exists()
            else {"hooks": {}}
        )
        hooks = current.setdefault("hooks", {})
        for event in tuple(hooks):
            retained = [
                group
                for candidate in hooks[event]
                if (group := self._without_managed_handlers(candidate)) is not None
            ]
            if retained:
                hooks[event] = retained
            else:
                del hooks[event]
        for event, groups in source["hooks"].items():
            hooks[event] = [*hooks.get(event, []), *groups]
        rendered = json.dumps(current, indent=2, ensure_ascii=False) + "\n"
        return self._write_if_changed(target, rendered)

    def _source_hooks(self) -> dict[str, object]:
        text = self._layout.adapter.joinpath("hooks.json").read_text(encoding="utf-8")
        return self._hook_data(text.replace("{codex_home}", str(self._layout.codex_home)))

    def _hook_data(self, text: str) -> dict[str, object]:
        data = json.loads(text)
        if not isinstance(data, dict) or not isinstance(data.get("hooks"), dict):
            raise self._conflict("hooks.json deve conter um objeto hooks")
        hooks = cast(dict[object, object], data["hooks"])
        for event, groups in hooks.items():
            if not isinstance(event, str) or not isinstance(groups, list):
                raise self._conflict("todo evento de hook deve conter uma lista de grupos")
            for group in groups:
                if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                    raise self._conflict("todo grupo de hook deve conter uma lista hooks")
        return cast(dict[str, object], data)

    def _replace_managed_block(self, current: str, source: str) -> str:
        block = f"{_START}\n{source}\n{_END}"
        has_start, has_end = _START in current, _END in current
        if has_start != has_end:
            raise self._conflict("AGENTS.md global contém um bloco gerenciado incompleto")
        if not has_start:
            prefix = current.rstrip()
            return f"{prefix}\n\n{block}\n" if prefix else f"{block}\n"
        before, remainder = current.split(_START, 1)
        _, after = remainder.split(_END, 1)
        suffix = after.lstrip("\n")
        return f"{before}{block}\n{suffix}" if suffix else f"{before}{block}\n"

    def _managed_content(self, content: str) -> Optional[str]:
        if _START not in content or _END not in content:
            return None
        return content.split(_START, 1)[1].split(_END, 1)[0].strip()

    def _write_if_changed(self, target: Path, content: str) -> str:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_text(encoding="utf-8") == content:
            return f"ok: {target}"
        if target.exists():
            backup = target.with_suffix(target.suffix + ".omh.bak")
            if not backup.exists():
                shutil.copy2(target, backup)
        atomic_write(target, content)
        return f"atualizado: {target}"

    def _without_managed_handlers(self, group: object) -> object:
        if not isinstance(group, dict):
            return group
        handlers = group.get("hooks")
        if not isinstance(handlers, list):
            return group
        retained = [
            item
            for item in handlers
            if not isinstance(item, dict) or _HOOK_MARKER not in str(item.get("command", ""))
        ]
        if not retained:
            return None
        return {**group, "hooks": retained}

    def _check_managed_block(self) -> str:
        content = self._layout.global_agents_file.read_text(encoding="utf-8")
        if _START not in content or _END not in content:
            raise self._conflict("bloco gerenciado do AGENTS.md global está ausente")
        managed = cast(str, self._managed_content(content))
        expected = self._source_agents(content)
        if managed != expected:
            raise self._conflict("bloco gerenciado do AGENTS.md global está desatualizado")
        return f"ok: {self._layout.global_agents_file}"

    def _check_hook(self) -> str:
        source_data = self._source_hooks()
        target_data = self._hook_data(self._layout.hooks_file.read_text(encoding="utf-8"))
        source_hooks = cast(dict[str, list[object]], source_data["hooks"])
        target_hooks = cast(dict[str, list[object]], target_data["hooks"])
        missing = (
            group not in target_hooks.get(event, [])
            for event, groups in source_hooks.items()
            for group in groups
        )
        if any(missing):
            raise self._conflict("hook SessionStart gerenciado está ausente ou desatualizado")
        stale = (
            handler
            for groups in target_hooks.values()
            for group in groups
            if isinstance(group, dict)
            for handler in group.get("hooks", [])
            if isinstance(handler, dict) and _HOOK_MARKER in str(handler.get("command", ""))
        )
        if any(stale):
            raise self._conflict("hook SessionStart global duplica o hook do plugin")
        return f"ok: {self._layout.hooks_file}"
