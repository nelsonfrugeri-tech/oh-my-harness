from kb.app import pending
from kb.app.context import Context
from kb.app.outcomes import Discarded, Rejected
from kb.note.vocabulary import Status


def reject(path: str, context: Context) -> Discarded | Rejected:
    candidate, metadata = pending.paths(path)
    if not context.store.exists(metadata):
        return Rejected(('No pending operation exists',))
    if context.store.exists(metadata.replace('metadata.json', 'approved.md')):
        return Rejected(('Publication already started; resume approve',))
    operation = pending.load(context.store, path)
    target = candidate if operation.updating else path
    if context.store.read(target, path).frontmatter.status != Status.PENDING:
        return Rejected(('Only a pending note can be rejected',))
    context.store.remove(target)
    context.store.remove(metadata)
    context.store.prune(operation.created_dirs)
    return Discarded(path)
