from __future__ import annotations

from pathlib import Path
from typing import Final

from lib.capability_table import preserve_machine_capabilities
from lib.config_writer import ConfigWriter
from lib.layout import InstallLayout
from lib.regular_config import require_regular_config

_START: Final = "<!-- omh-managed:start -->"
_END: Final = "<!-- omh-managed:end -->"


class ManagedAgents:
    def __init__(
        self,
        layout: InstallLayout,
        conflict: type[RuntimeError],
        replace_global_agents: bool,
        writer: ConfigWriter,
    ) -> None:
        self._layout = layout
        self._conflict = conflict
        self._replace_global_agents = replace_global_agents
        self._writer = writer

    def preflight(self) -> None:
        require_regular_config(
            self._layout.global_agents_file, "global AGENTS.md", self._conflict
        )
        current = self._read(self._layout.global_agents_file)
        self._replace_block(self._installation_base(current), self._source(current))

    def install(self) -> str:
        target = self._layout.global_agents_file
        current = self._read(target)
        content = self._replace_block(
            self._installation_base(current), self._source(current)
        )
        return self._writer.write_if_changed(target, content)

    def validate(self) -> str:
        target = self._layout.global_agents_file
        require_regular_config(target, "global AGENTS.md", self._conflict)
        content = target.read_text(encoding="utf-8")
        managed = self._managed_content(content)
        if managed is None:
            raise self._conflict("global AGENTS.md managed block is missing")
        if managed != self._source(content):
            raise self._conflict("global AGENTS.md managed block is stale")
        return f"ok: {target}"

    def _source(self, current: str) -> str:
        source = (
            self._layout.adapter.joinpath("AGENTS.md")
            .read_text(encoding="utf-8")
            .strip()
        )
        managed = self._managed_content(current)
        installed = current if managed is None else managed
        configured = preserve_machine_capabilities(source, installed)
        return self._with_local_overlay(configured)

    def _with_local_overlay(self, source: str) -> str:
        target = self._layout.local_agents_file
        if not target.is_file():
            return source
        overlay = target.read_text(encoding="utf-8").strip()
        return (
            source
            if not overlay
            else f"{source}\n\n---\n\n# Local machine overlay\n\n{overlay}"
        )

    def _installation_base(self, current: str) -> str:
        if (
            self._replace_global_agents
            and _START not in current
            and _END not in current
        ):
            return ""
        return current

    def _replace_block(self, current: str, source: str) -> str:
        block = f"{_START}\n{source}\n{_END}"
        has_start, has_end = _START in current, _END in current
        if has_start != has_end:
            raise self._conflict(
                "global AGENTS.md contains an incomplete managed block"
            )
        if not has_start:
            prefix = current.rstrip()
            return f"{prefix}\n\n{block}\n" if prefix else f"{block}\n"
        before, remainder = current.split(_START, 1)
        _, after = remainder.split(_END, 1)
        suffix = after.lstrip("\n")
        return f"{before}{block}\n{suffix}" if suffix else f"{before}{block}\n"

    @staticmethod
    def _read(target: Path) -> str:
        return target.read_text(encoding="utf-8") if target.exists() else ""

    @staticmethod
    def _managed_content(content: str) -> str | None:
        if _START not in content or _END not in content:
            return None
        return content.split(_START, 1)[1].split(_END, 1)[0].strip()
