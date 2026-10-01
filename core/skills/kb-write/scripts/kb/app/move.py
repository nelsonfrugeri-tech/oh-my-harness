from dataclasses import replace

from kb.app import pending
from kb.app.context import Context
from kb.app.descriptions import validate_descriptions
from kb.app.outcomes import Moved, Rejected
from kb.note.model import NotePath
from kb.note.naming import check_name


def move(path: str, target: NotePath, context: Context, *,
         descriptions: tuple[tuple[str, str], ...] = ()) -> Moved | Rejected:
    destination = target.relative_path
    metadata_path = pending.paths(path)[1]
    if not context.store.exists(metadata_path):
        return Rejected(('No pending proposal exists',))
    metadata = pending.load(context.store, path)
    old_directories = metadata.created_dirs
    if metadata.updating:
        return Rejected(('Moving an existing active note is outside this operation',))
    if context.store.exists(pending.receipt_path(path)):
        return Rejected(('Publication has started; resume approve',))
    if context.store.exists(destination):
        return Rejected(('Destination already exists',))
    components = (target.domain, *target.entities, target.name)
    for index, component in enumerate(components):
        issues = check_name(component, parent=components[index - 1] if index else None)
        if issues:
            return Rejected(issues)
    note = replace(context.store.read(path), path=target)
    merged = dict(metadata.descriptions)
    merged.update(descriptions)
    metadata = replace(metadata, descriptions=tuple(merged.items()),
                       created_dirs=tuple(set(old_directories) | set(pending.created_dirs(context.store, destination))))
    errors = validate_descriptions(note, context, metadata.descriptions)
    if errors:
        return Rejected(errors)
    pending.save(context.store, destination, metadata)
    context.store.write(note)
    context.store.remove(path)
    context.store.remove(metadata_path)
    context.store.prune(old_directories)
    return Moved(path, destination)
