import json
import os
from pathlib import Path

from kb.adapters.clock import SystemClock
from kb.adapters.filesystem import FileNoteStore
from kb.app.context import Context


def build_context(args) -> Context:
    root = Path(args.root or os.environ.get('OMH_KB_ROOT', '~/knowledge-base')).expanduser()
    runtime = Path(os.environ.get('OMH_KB_RUNTIME', '~/.local/share/omh-kb')).expanduser()
    machine_id = ''
    if args.command not in {'template', 'harvest', 'backup', 'search'}:
        identity = Path(args.identity) if args.identity else runtime / 'identity.json'
        identity_data = json.loads(identity.read_text())
        machine_id = identity_data.get('id', identity_data.get('machine_id', ''))
        if not machine_id:
            raise ValueError('Machine identity has no id')
    index, embedder = None, None
    if args.command in {'approve', 'backup', 'search', 'repair'}:
        from kb.adapters.qdrant import QdrantIndex
        from kb.adapters.embedder import BgeM3Embedder
        index = QdrantIndex(args.qdrant_url or os.environ.get('OMH_KB_QDRANT_URL', 'http://127.0.0.1:6333'),
                            collection=args.collection or os.environ.get('OMH_KB_COLLECTION', 'knowledge-base'))
        if args.command in {'approve', 'search', 'repair'}:
            index.ensure_collection()
        embedder = BgeM3Embedder()
    return Context(FileNoteStore(root), SystemClock(), machine_id, index, embedder)
