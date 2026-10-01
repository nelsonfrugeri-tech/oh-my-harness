from dataclasses import replace

from kb.app import pending
from kb.app.context import Context
from kb.app.descriptions import validate_descriptions
from kb.app.outcomes import Approved, Degraded, Rejected
from kb.app.repair import repair
from kb.app.validation import validate_candidate
from kb.note.model import Note
from kb.note.versioning import freeze
from kb.note.vocabulary import Status


def approve(path: str, context: Context, *, transcript: str | None):
    candidate_path, metadata_path = pending.paths(path)
    receipt = metadata_path.replace('metadata.json', 'approved.md')
    if not context.store.exists(metadata_path):
        active = context.store.read(path)
        if active.frontmatter.status == Status.ACTIVE:
            return Approved(path, active.frontmatter.version)
        return Rejected(('No pending operation exists',))
    metadata = pending.load(context.store, path)
    if context.index is None or context.embedder is None:
        return Degraded('Search index and embedder are required to approve')
    if context.store.exists(receipt):
        approved = context.store.read(receipt, path)
    else:
        approved = _prepare(path, context, metadata, transcript)
        if isinstance(approved, Rejected):
            return approved
        context.store.write(approved, receipt)
    context.store.write(approved)
    repair(context, approved, metadata.descriptions, publishing=True)
    approved = context.store.read(path)
    from kb.search.payload import embed_text, point_id
    context.index.upsert(approved, context.embedder.embed(embed_text(approved)))
    if metadata.updating:
        frozen = _frozen_path(path, metadata)
        context.index.set_payload(point_id(approved.frontmatter.id, metadata.base_version),
                                  {'status': 'superseded', 'path': frozen, 'superseded_at': metadata.at,
                                   'superseded_reason': metadata.reason})
    context.store.remove(candidate_path)
    context.store.remove(receipt)
    context.store.remove(metadata_path)
    context.store.prune(metadata.created_dirs)
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
    if previous:
        update = freeze(previous, candidate, at=metadata.at, reason=metadata.reason)
        if not hasattr(update, 'frozen'):
            return Rejected(tuple(str(issue) for issue in update.issues))
        frozen = update.frozen
        if context.store.exists(frozen.relative_path):
            if context.store.read(frozen.relative_path, path) != frozen.note:
                return Rejected(('Frozen version collision',))
        else:
            context.store.write(frozen.note, frozen.relative_path)
        return replace(update.current, frontmatter=replace(update.current.frontmatter,
                                                           status=Status.ACTIVE))
    return replace(candidate, frontmatter=replace(candidate.frontmatter, status=Status.ACTIVE))


def _frozen_path(path: str, metadata: pending.PendingMetadata) -> str:
    folder, name = path.rsplit('/', 1)
    return f'{folder}/.history/{metadata.at[:10]}--v{metadata.base_version}--{name}'
