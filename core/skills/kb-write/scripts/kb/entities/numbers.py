import re
from decimal import Decimal, InvalidOperation


def parse_number(value: str) -> Decimal | None:
    text = value.strip().lower().replace('\u00a0', ' ')
    match = re.fullmatch(r'([+-]?\d[\d.,]*)(?:\s*(mil|milhão|milhões))?', text)
    if match is None:
        return None
    number, scale = match.groups()
    if ',' in number and '.' in number:
        if number.rfind(',') > number.rfind('.'):
            number = number.replace('.', '').replace(',', '.')
        else:
            number = number.replace(',', '')
    elif ',' in number:
        number = number.replace(',', '.')
    elif re.fullmatch(r'[+-]?\d{1,3}(?:\.\d{3})+', number):
        number = number.replace('.', '')
    try:
        result = Decimal(number)
    except InvalidOperation:
        return None
    return result * (1000 if scale == 'mil' else 1000000 if scale else 1)
