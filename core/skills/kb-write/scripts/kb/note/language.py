import re
import unicodedata

# This deterministic heuristic has no corpus calibration claim.
PORTUGUESE = frozenset('a o as os um uma de da do das dos em no na nos nas para por com sem que e ou '
                       'foi sao ser esta este essa esse isso como quando ao aos pela pelo se sua seu '
                       'mais mas nao uma entre sobre tambem apos antes cada deve pode tem tem que'.split())
ENGLISH = frozenset('the a an and or of to in on for from with without this that these those is are '
                    'was were be been being will would should could can must it its their them '
                    'they we you your our has have had not but when where which while then than'.split())
AMBIGUOUS = PORTUGUESE & ENGLISH
PORTUGUESE = PORTUGUESE - AMBIGUOUS
ENGLISH = ENGLISH - AMBIGUOUS


def _paragraphs(text: str) -> tuple[str, ...]:
    lines: list[str] = []
    fence = ''
    for line in text.splitlines():
        if fence:
            if re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}[ \t]*', line):
                fence = ''
            lines.append('')
            continue
        opening = re.match(r' {0,3}(`{3,}|~{3,})(.*)$', line)
        if opening and not (opening[1].startswith('`') and '`' in opening[2]):
            fence = opening[1]
            lines.append('')
            continue
        if re.match(r'^\s*(?:\||#{1,6}\s|<!--)', line):
            lines.append('')
            continue
        line = re.sub(r'`[^`]*`|https?://\S+|(?:/|~/)[\w./-]+', '', line)
        lines.append(line)
    return tuple(part.strip() for part in re.split(r'\n\s*\n', '\n'.join(lines)) if part.strip())


def is_pt_br(text: str) -> bool:
    for paragraph in _paragraphs(text):
        normalized = unicodedata.normalize('NFKD', paragraph).encode('ascii', 'ignore').decode()
        words = re.findall(r'[a-z]+', normalized.casefold())
        if not words:
            continue
        pt_count = sum(word in PORTUGUESE for word in words)
        en_count = sum(word in ENGLISH for word in words)
        if en_count > pt_count or pt_count == 0:
            return False
    return True
