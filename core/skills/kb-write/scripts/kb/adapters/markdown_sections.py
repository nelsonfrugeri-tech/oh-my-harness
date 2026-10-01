import re

from kb.note.model import Section


def parse_sections(body: str) -> tuple[Section, ...]:
    sections, lines = [], []
    heading = None
    fence = None
    for line in body.splitlines():
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if marker:
            if fence is None:
                fence = marker[1]
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            lines.append(line)
            continue
        match = re.match(r'^## ([^\n]+)$', line) if fence is None else None
        if match:
            if heading is not None:
                sections.append(Section(heading, '\n'.join(lines).strip()))
            elif any(part.strip() for part in lines):
                raise ValueError('Body must start with a schema section')
            heading, lines = match[1], []
        else:
            lines.append(line)
    if heading is not None:
        sections.append(Section(heading, '\n'.join(lines).strip()))
    elif any(part.strip() for part in lines):
        raise ValueError('Body must start with a schema section')
    return tuple(sections)
