import re

_DECLARATIONS = frozenset({'Entities', 'Dates', 'Figures'})


def narrative(text: str) -> str:
    """Exclude declarations, tables and code from narrative-presence evidence."""
    lines: list[str] = []
    declaration = False
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        marker = re.match(r'^(`{3,}|~{3,})', stripped)
        if marker:
            current = marker.group()
            if fence is None:
                fence = current
            elif current[0] == fence[0] and len(current) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        heading = re.fullmatch(r'##\s+(.+?)\s*#*', stripped)
        if heading:
            declaration = heading[1] in _DECLARATIONS
            continue
        if not declaration and not stripped.startswith('|'):
            lines.append(line)
    return '\n'.join(lines)
