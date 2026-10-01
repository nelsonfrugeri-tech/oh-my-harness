import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import parse_qsl, unquote, urlsplit


class SecretKind(str, Enum):
    CREDENTIAL = 'credential'
    TOKEN = 'token'
    CARD = 'card'
    CPF = 'cpf'
    PRIVATE_KEY = 'private-key'


@dataclass(frozen=True)
class SecretFinding:
    kind: SecretKind
    start: int
    end: int


_CREDENTIAL = re.compile(r'''(?ix)\b(?:senha|password|passwd|token|api[_-]?key|secret|authorization)\b["']?\s*[:=]\s*["']?[^\s"',}]+''')
_TOKEN = re.compile(r'\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|eyJ[\w-]+\.[\w-]+\.[\w-]+)\b')
_SENSITIVE_QUERY = re.compile(r'token|secret|password|passwd|api.?key|credential|signature|auth|sig', re.I)


def find_secrets(text: str) -> tuple[SecretFinding, ...]:
    """Return secret categories and offsets; never copy secrets into diagnostics."""
    found: list[SecretFinding] = []
    for kind, pattern in ((SecretKind.CREDENTIAL, _CREDENTIAL), (SecretKind.TOKEN, _TOKEN),
                          (SecretKind.PRIVATE_KEY, re.compile(r'-----BEGIN (?:\w+ )?PRIVATE KEY-----'))):
        found.extend(SecretFinding(kind, m.start(), m.end()) for m in pattern.finditer(text))
    for match in re.finditer(r'https?://[^\s<>"`]+', text):
        try:
            url = urlsplit(match.group())
            sensitive = url.username or url.password or any(
                _SENSITIVE_QUERY.search(key) for key, _ in parse_qsl(url.query + '&' + url.fragment))
        except ValueError:
            sensitive = True
        if sensitive:
            found.append(SecretFinding(SecretKind.CREDENTIAL, match.start(), match.end()))
        elif _CREDENTIAL.search(unquote(match.group())):
            found.append(SecretFinding(SecretKind.CREDENTIAL, match.start(), match.end()))
    for match in re.finditer(r'(?<!\d)(?:\d[ .-]?){10,18}\d(?!\d)', text):
        digits = re.sub(r'\D', '', match.group())
        kind = SecretKind.CPF if len(digits) == 11 and _cpf(digits) else None
        if 13 <= len(digits) <= 19 and _luhn(digits):
            kind = SecretKind.CARD
        if kind is not None:
            found.append(SecretFinding(kind, match.start(), match.end()))
    return tuple(dict.fromkeys(found))


def _luhn(digits: str) -> bool:
    if len(set(digits)) == 1:
        return False
    total = 0
    for position, digit in enumerate(reversed(digits)):
        value = int(digit) * (2 if position % 2 else 1)
        total += value - 9 if value > 9 else value
    return total % 10 == 0


def _cpf(digits: str) -> bool:
    if len(set(digits)) == 1:
        return False
    for length in (9, 10):
        total = sum(int(digit) * (length + 1 - i) for i, digit in enumerate(digits[:length]))
        check = (total * 10 % 11) % 10
        if check != int(digits[length]):
            return False
    return True
