from kb.app import pending
from kb.app.context import Context
from kb.note.model import Note
from kb.note.versioning import freeze, history_path
from kb.search.payload import point_id


def preserve_previous(path: str, approved: Note, context: Context,
                      metadata: pending.PendingMetadata) -> tuple[str, ...]:
    if not metadata.updating or approved.frontmatter.version == metadata.base_version:
        return ()
    frozen_path = history_path(path, metadata.base_version, metadata.at)
    previous = context.store.read(path)
    if previous.frontmatter.id != metadata.base_id:
        return ('Active identity changed during publication',)
    if previous.frontmatter.version == approved.frontmatter.version:
        if not context.store.exists(frozen_path):
            return ('Published revision has no frozen predecessor',)
        return ()
    if (previous.frontmatter.id != metadata.base_id
            or previous.frontmatter.version != metadata.base_version):
        return ('Active version changed during publication',)
    update = freeze(previous, approved, at=metadata.at, reason=metadata.reason)
    if not hasattr(update, 'frozen'):
        return tuple(f'{issue.field}: {issue.message}' for issue in update.issues)
    if context.store.exists(frozen_path):
        if context.store.read(frozen_path, path) != update.frozen.note:
            return ('Frozen version collision',)
    else:
        context.store.write(update.frozen.note, frozen_path)
    return ()


def retire_previous(path: str, approved: Note, context: Context,
                    metadata: pending.PendingMetadata) -> None:
    if not metadata.updating or approved.frontmatter.version == metadata.base_version:
        return
    context.index.set_payload(point_id(approved.frontmatter.id, metadata.base_version),
                              {'status': 'superseded',
                               'path': history_path(path, metadata.base_version, metadata.at),
                               'superseded_at': metadata.at, 'superseded_reason': metadata.reason})


def finish(path: str, context: Context, created_dirs: tuple[str, ...] = ()) -> None:
    candidate, metadata = pending.paths(path)
    # Metadata absence is the durable completion marker; cleanup can be repeated.
    context.store.remove(metadata)
    context.store.remove(candidate)
    context.store.remove(pending.receipt_path(path))
    context.store.prune(created_dirs + (path.rsplit('/', 1)[0] + '/.pending',))
