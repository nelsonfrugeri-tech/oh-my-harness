from __future__ import annotations

import json
from typing import Final, cast

from lib.config_writer import ConfigWriter
from lib.layout import InstallLayout
from lib.regular_config import require_regular_config

_HOOK_MARKER: Final = "omh-managed: context"


class ManagedHooks:
    def __init__(
        self, layout: InstallLayout, conflict: type[RuntimeError], writer: ConfigWriter
    ) -> None:
        self._layout = layout
        self._conflict = conflict
        self._writer = writer

    def preflight(self) -> None:
        self._source()
        target = self._layout.hooks_file
        require_regular_config(target, "global hooks.json", self._conflict)
        if target.exists():
            self._data(target.read_text(encoding="utf-8"))

    def install(self) -> str:
        source = self._source()
        target = self._layout.hooks_file
        current = (
            self._data(target.read_text(encoding="utf-8"))
            if target.exists()
            else {"hooks": {}}
        )
        hooks = cast(dict[str, list[object]], current["hooks"])
        source_hooks = cast(dict[str, list[object]], source["hooks"])
        for event, groups in source_hooks.items():
            retained = tuple(
                group
                for candidate in hooks.get(event, [])
                if (group := self._without_managed(candidate)) is not None
            )
            hooks[event] = [*retained, *groups]
        rendered = json.dumps(current, indent=2, ensure_ascii=False) + "\n"
        return self._writer.write_if_changed(target, rendered)

    def validate(self) -> str:
        source = cast(dict[str, list[object]], self._source()["hooks"])
        target = self._layout.hooks_file
        require_regular_config(target, "global hooks.json", self._conflict)
        installed = cast(
            dict[str, list[object]],
            self._data(target.read_text(encoding="utf-8"))["hooks"],
        )
        if any(
            group not in installed.get(event, [])
            for event, groups in source.items()
            for group in groups
        ):
            raise self._conflict("managed SessionStart hook is missing or stale")
        return f"ok: {target}"

    def _source(self) -> dict[str, object]:
        text = self._layout.adapter.joinpath("hooks.json").read_text(encoding="utf-8")
        return self._data(text.replace("{codex_home}", str(self._layout.codex_home)))

    def _data(self, text: str) -> dict[str, object]:
        data = json.loads(text)
        if not isinstance(data, dict) or not isinstance(data.get("hooks"), dict):
            raise self._conflict("hooks.json must contain a hooks object")
        hooks = cast(dict[object, object], data["hooks"])
        for event, groups in hooks.items():
            if not isinstance(event, str) or not isinstance(groups, list):
                raise self._conflict("every hook event must contain a list of groups")
            if any(
                not isinstance(group, dict) or not isinstance(group.get("hooks"), list)
                for group in groups
            ):
                raise self._conflict("every hook group must contain a hooks list")
        return cast(dict[str, object], data)

    @staticmethod
    def _without_managed(group: object) -> object | None:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            return group
        retained = [
            item
            for item in group["hooks"]
            if not isinstance(item, dict)
            or _HOOK_MARKER not in str(item.get("command", ""))
        ]
        return {**group, "hooks": retained} if retained else None
