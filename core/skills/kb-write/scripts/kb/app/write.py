from dataclasses import replace

from kb.app import pending
from kb.app.context import Context
from kb.app.descriptions import validate_descriptions
from kb.app.outcomes import Pending, Rejected
from kb.app.validation import validate_candidate
from kb.note.model import Note
from kb.note.vocabulary import Status


def write(note: Note, context: Context, *, transcript: str | None,
          descriptions: tuple[tuple[str, str], ...] = (), reason: str = '',
          approved_degraded: bool = False) -> Pending | Rejected:
    path = note.path.relative_path
    receipt = pending.paths(path)[1].replace('metadata.json', 'approved.md')
    if context.store.exists(receipt):
        return Rejected(('Publication has started; resume approve before proposing another revision',))
    existing = context.store.read(path) if context.store.exists(path) else None
    previous = existing if existing and existing.frontmatter.status == Status.ACTIVE else None
    if previous and not 30 <= len(reason) <= 500:
        return Rejected(('Updates require a reason of 30–500 characters',))
    if previous and (note.frontmatter.id != previous.frontmatter.id
                     or note.frontmatter.created_at != previous.frontmatter.created_at):
        return Rejected(('An update must preserve id and created_at',))
    note = replace(note, frontmatter=replace(note.frontmatter, status=Status.PENDING))
    errors = validate_candidate(note, context, transcript=transcript, previous=previous,
                                approved_degraded=approved_degraded)
    errors += validate_descriptions(note, context, descriptions)
    if not previous and note.frontmatter.version != 1:
        errors += ("A new note starts at version 1",)
    if errors:
        return Rejected(errors)
    created = pending.created_dirs(context.store, path)
    if context.store.exists(pending.paths(path)[1]):
        created = tuple(set(created) | set(pending.load(context.store, path).created_dirs))
    metadata = pending.PendingMetadata(reason, descriptions, approved_degraded,
                                       previous is not None,
                                       previous.frontmatter.id if previous else None,
                                       previous.frontmatter.version if previous else None,
                                       context.clock.now(), created)
    pending.save(context.store, path, metadata)
    context.store.write(note, pending.paths(path)[0] if previous else path)
    return Pending(path, tuple(key for key, _ in descriptions))
