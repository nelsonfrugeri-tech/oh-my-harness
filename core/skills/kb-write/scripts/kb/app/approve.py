from dataclasses import replace

from kb.app import pending
from kb.app.context import Context
from kb.app.descriptions import validate_descriptions
from kb.app.outcomes import Approved, Degraded, Rejected
from kb.app.publication import finish, preserve_previous, retire_previous
from kb.app.repair import repair
from kb.app.repair_queue import resume_repairs
from kb.app.validation import validate_candidate
from kb.note.model import Note
from kb.note.versioning import freeze, needs_new_version
from kb.note.vocabulary import Status
from kb.search.payload import embed_text


def approve(path: str, context: Context, *, transcript: str | None):
    metadata_path = pending.paths(path)[1]
    receipt = pending.receipt_path(path)
    if not context.store.exists(metadata_path):
        if not context.store.exists(path):
            return Rejected(('No pending operation exists',))
        active = context.store.read(path)
        if active.frontmatter.status == Status.ACTIVE:
            finish(path, context)
            return Approved(path, active.frontmatter.version)
        return Rejected(('No pending operation exists',))
    unfinished = pending.other_publication(context.store, path)
    if unfinished:
        return Rejected((f'Resume unfinished approval before publishing another note: {unfinished}',))
    metadata = pending.load(context.store, path)
    if context.index is None or context.embedder is None:
        return Degraded('Search index and embedder are required to approve')
    resume_repairs(context)
    if context.store.exists(receipt):
        approved = context.store.read(receipt, path)
    else:
        approved = _prepare(path, context, metadata, transcript)
        if isinstance(approved, Rejected):
            return approved
        context.store.write(approved, receipt)
    errors = preserve_previous(path, approved, context, metadata)
    if errors:
        return Rejected(errors)
    context.store.write(approved)
    context.index.upsert(approved, context.embedder.embed(embed_text(approved)))
    repair(context, approved, metadata.descriptions, publishing=True)
    retire_previous(path, approved, context, metadata)
    finish(path, context, metadata.created_dirs)
    return Approved(path, approved.frontmatter.version)


def _prepare(path, context, metadata, transcript) -> Note | Rejected:
    candidate_path = pending.paths(path)[0] if metadata.updating else path
    candidate = context.store.read(candidate_path, path)
    previous = context.store.read(path) if metadata.updating else None
    if previous and (previous.frontmatter.id != metadata.base_id
                     or previous.frontmatter.version != metadata.base_version):
        return Rejected(('Active version changed since proposal',))
    errors = validate_candidate(candidate, context, transcript=transcript, previous=previous,
                                approved_degraded=metadata.approved_degraded)
    errors += validate_descriptions(candidate, context, metadata.descriptions)
    if errors:
        return Rejected(errors)
    if previous and needs_new_version(previous, candidate):
        update = freeze(previous, candidate, at=metadata.at, reason=metadata.reason)
        if not hasattr(update, 'frozen'):
            return Rejected(tuple(f'{issue.field}: {issue.message}' for issue in update.issues))
        return update.current
    frontmatter = replace(candidate.frontmatter, status=Status.ACTIVE)
    if previous:
        frontmatter = replace(frontmatter, version=previous.frontmatter.version,
                              updated_at=previous.frontmatter.updated_at)
    return replace(candidate, frontmatter=frontmatter)
