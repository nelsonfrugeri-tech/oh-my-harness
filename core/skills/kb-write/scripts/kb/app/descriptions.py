from kb.app.context import Context
from kb.entities.secrets import find_secrets
from kb.note.model import Note


def validate_descriptions(note: Note, context: Context,
                          descriptions: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    approved = dict(descriptions)
    scope = note.path.scope.value
    domain = f'{scope}/{note.path.domain}'
    required = [(domain, scope + '/index.md', note.path.domain + '/')]
    for depth in range(1, len(note.path.entities) + 1):
        relative = '/'.join(note.path.entities[:depth])
        required.append((domain + '/' + relative, domain + '/index.md', relative + '/'))
    errors = []
    for key, index, link in required:
        listed = context.store.exists(index) and f']({link})' in context.store.read_text(index)
        if not listed and not approved.get(key, '').strip():
            errors.append(f'Approved description required: {key}')
    for key, value in descriptions:
        if '\n' in value or find_secrets(value) or not value.strip():
            errors.append(f'Invalid description: {key}')
    return tuple(errors)
