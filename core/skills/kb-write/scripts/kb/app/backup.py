import hashlib
import json
from dataclasses import asdict

from kb.app.backup_model import Applied, BackupManifest, BackupStorePort, LegacyPending
from kb.app.backup_model import Blocked, ManifestEntry, Planned
from kb.app.context import Context


MANIFEST_PATH = 'backup/.manifest.json'
COMPLETION_PATH = 'backup/.completed.json'


def backup(context: Context, storage: BackupStorePort, *, apply: bool,
           template: str, reason: str, plan: str):
    if context.store.exists(MANIFEST_PATH):
        saved = json.loads(context.store.read_text(MANIFEST_PATH))
        manifest = BackupManifest(tuple(ManifestEntry(**entry) for entry in saved['entries']))
    else:
        manifest = storage.inventory()
        saved = {'entries': [asdict(entry) for entry in manifest.entries],
                 'at': context.clock.now(), 'reason': reason, 'plan': plan}
    if not apply:
        return Planned(manifest)
    if manifest.unavailable:
        return Blocked('Files are not locally available: ' + ', '.join(manifest.unavailable))
    if any(entry.path == 'INSTRUCTION.md' for entry in manifest.entries):
        return Blocked('Root INSTRUCTION.md conflicts with reserved backup instructions')
    if context.store.exists(COMPLETION_PATH):
        completed = Applied(**json.loads(context.store.read_text(COMPLETION_PATH)))
        if not storage.verify(manifest):
            return Blocked('Completed backup no longer matches its manifest')
        return completed
    encoded = json.dumps(saved, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    context.store.write_text(MANIFEST_PATH, encoded)
    storage.move(manifest)
    if not storage.verify(manifest):
        return Blocked('Backup hash verification failed')
    if context.index is None:
        return LegacyPending(len(manifest.entries), 'Search index unavailable; resume backup')
    try:
        count = context.index.mark_legacy('backup/', source_paths=tuple(entry.path for entry in manifest.entries))
    except (OSError, RuntimeError) as error:
        return LegacyPending(len(manifest.entries), f'{type(error).__name__}: {error}')
    instruction = template.format(at=saved['at'], reason=saved['reason'], plan=saved['plan'],
                                  files=len(manifest.entries), manifest_sha256=digest,
                                  legacy_points=count)
    context.store.write_text('backup/INSTRUCTION.md', instruction)
    result = Applied(len(manifest.entries), digest, count)
    context.store.write_text(COMPLETION_PATH, json.dumps(asdict(result)))
    return result
