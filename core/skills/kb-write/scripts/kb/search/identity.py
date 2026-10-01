from uuid import UUID, uuid5

_NAMESPACE = UUID('0e08fca8-f1cc-5293-99af-b7b465a278f6')


def point_id(identifier: str, version: int) -> str:
    return str(uuid5(_NAMESPACE, f'{identifier}:{version}'))
