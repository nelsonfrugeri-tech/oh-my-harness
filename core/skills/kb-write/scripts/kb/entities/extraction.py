import re

from .currencies import ISO_CURRENCIES
from .kinds import EntityKind
from .model import Candidate, CandidateKind
from .numbers import parse_number

_URL = re.compile(r'https?://[^\s<>"`]+')
_PATH = re.compile(r'(?<![\w:/])(?:~/|/|\./|\.\./)[^\s<>"`|]+')
_REPO = re.compile(r'git@[\w.-]+:[\w./-]+|\b[\w.-]+/[\w.-]+\.git\b')
_EMAIL = re.compile(r'\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b')
_DATE = re.compile(r'\b(?:\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))?|\d{2}/\d{2}/\d{4})\b')
_NUMBER = r'[+-]?\d[\d.,]*(?:\s*(?:milhões|milhão|mil)\b)?'
_MONEY = re.compile(rf'(R\$|US\$|€|\b[A-Z]{{3}})\s*({_NUMBER})|({_NUMBER})\s*([A-Z]{3})\b')
_MEASURE = re.compile(rf'({_NUMBER})\s*(%|pontos\b|kg\b|km\b|ms\b|horas?\b|dias?\b|GB\b|MB\b)')


def extract(prose: str) -> tuple[Candidate, ...]:
    """Extract syntactically recognizable addresses, dates and measured amounts."""
    candidates: list[Candidate] = []
    remaining = prose
    for kind, pattern in ((EntityKind.URLS, _URL), (EntityKind.REPOS, _REPO),
                          (EntityKind.EMAILS, _EMAIL), (CandidateKind.DATE, _DATE),
                          (EntityKind.PATHS, _PATH)):
        for match in pattern.finditer(remaining):
            candidates.append(Candidate(kind, match.group().rstrip('.,;:)]')))
        remaining = pattern.sub(lambda match: ' ' * len(match.group()), remaining)
    for match in _MONEY.finditer(remaining):
        unit, value, reverse_value, reverse_unit = match.groups()
        value = value or reverse_value
        unit = {'R$': 'BRL', 'US$': 'USD', '€': 'EUR'}.get(unit, unit) or reverse_unit
        amount = parse_number(value.rstrip('.,'))
        if amount is not None and unit in ISO_CURRENCIES:
            candidates.append(Candidate(CandidateKind.FIGURE, f'{amount.normalize():f} {unit}'))
    remaining = _MONEY.sub('', remaining)
    for match in _MEASURE.finditer(remaining):
        amount = parse_number(match[1].rstrip('.,'))
        if amount is not None:
            candidates.append(Candidate(CandidateKind.FIGURE, f'{amount.normalize():f} {match[2]}'))
    return tuple(dict.fromkeys(candidates))
