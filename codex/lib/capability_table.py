from __future__ import annotations

from typing import Final


_MACHINE_CAPABILITIES: Final = frozenset(
    {"code-host", "ci", "memory", "social-x", "tunnel"}
)


def preserve_machine_capabilities(source: str, installed: str) -> str:
    providers = _providers(installed)
    return "\n".join(_merge_row(line, providers) for line in source.splitlines())


def _providers(content: str) -> dict[str, str]:
    providers = {}
    for line in content.splitlines():
        cells = _cells(line)
        if len(cells) != 3:
            continue
        capability = cells[0].strip("`")
        if capability in _MACHINE_CAPABILITIES:
            providers[capability] = cells[2]
    return providers


def _merge_row(line: str, providers: dict[str, str]) -> str:
    cells = _cells(line)
    if len(cells) != 3:
        return line
    provider = providers.get(cells[0].strip("`"))
    if provider is None:
        return line
    return f"| {cells[0]} | {cells[1]} | {provider} |"


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]
