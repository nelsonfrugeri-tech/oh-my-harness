import re
import unicodedata

from .kinds import EntityKind, LITERAL_KINDS


def normalize(kind: EntityKind, value: str) -> str:
    if kind in LITERAL_KINDS:
        return value.strip().strip('`')
    ascii_text = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', ascii_text.lower()).strip('-')
