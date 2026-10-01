import json
from pathlib import Path

from kb.adapters.markdown import parse_note
from kb.adapters.transcript_claude import ClaudeTranscriptSource
from kb.app.outcomes import Rejected
from kb.note.model import NotePath
from kb.note.vocabulary import NoteType, Scope


def dispatch(args, context):
    if args.command == 'template':
        from kb.app.template import template
        return template(NoteType(args.type))
    if args.command == 'check':
        from kb.app.check import check
        return check(context)
    if args.command == 'harvest':
        from kb.app.harvest import harvest
        return harvest(ClaudeTranscriptSource(), args.transcript)
    if args.command in {'write', 'validate', 'approve'}:
        return _publication(args, context)
    if args.command == 'backup':
        from kb.adapters.backup_filesystem import FileBackupStore
        from kb.app.backup import backup
        template = Path(__file__).parent.joinpath('app/assets/backup-instruction.md').read_text()
        return backup(context, FileBackupStore(context.store.root), apply=args.apply,
                      template=template, reason=args.reason, plan=args.plan)
    if args.command == 'search':
        return context.index.search(context.embedder.embed(args.query), json.loads(args.filters),
                                    include_history=args.history, include_legacy=args.legacy)
    return _navigation(args, context)


def _publication(args, context):
    transcript = None
    if args.transcript:
        try:
            transcript = ClaudeTranscriptSource().load(args.transcript)
        except (OSError, ValueError):
            transcript = None
    if args.command == 'approve':
        from kb.app.approve import approve
        return approve(args.path, context, transcript=transcript)
    note = parse_note(Path(args.file).read_text(), args.path)
    if args.command == 'write':
        from kb.app.write import write
        return write(note, context, transcript=transcript, reason=args.reason,
                     descriptions=_descriptions(args.description),
                     approved_degraded=args.approved_degraded)
    from kb.app.validation import validate_candidate
    previous = context.store.read(args.path) if context.store.exists(args.path) else None
    errors = validate_candidate(note, context, transcript=transcript, previous=previous,
                                approved_degraded=args.approved_degraded)
    return Rejected(errors) if errors else {'status': 'Valid', 'path': args.path}


def _navigation(args, context):
    if args.command == 'nav':
        from kb.app.navigate import navigate
        return navigate(args.path, context)
    if args.command == 'reject':
        from kb.app.reject import reject
        return reject(args.path, context)
    if args.command == 'move':
        from kb.app.move import move
        parts = args.to.split('/')
        if len(parts) < 4 or parts[-1] != parts[-2] + '.md':
            raise ValueError('Expected scope/domain/name/name.md')
        target = NotePath(Scope(parts[0]), parts[1], tuple(parts[2:-2]), parts[-2])
        return move(args.path, target, context, descriptions=_descriptions(args.description))
    from kb.app.repair import repair
    repair(context, context.store.read(args.path), _descriptions(args.description))
    return {'status': 'Repaired', 'path': args.path}


def _descriptions(values):
    entries = []
    for value in values:
        path, separator, description = value.partition('=')
        if not separator or not description.strip():
            raise ValueError('Descriptions use path=description')
        entries.append((path, description))
    return tuple(entries)
