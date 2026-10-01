import fcntl
import hashlib
import os
from pathlib import Path


class BundleLock:
    def __init__(self, root: Path):
        runtime = Path(os.environ.get('OMH_KB_RUNTIME', '~/.local/share/omh-kb')).expanduser()
        self.path = runtime / 'locks' / (hashlib.sha256(str(root).encode()).hexdigest() + '.lock')
        self.stream = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        self.stream = os.fdopen(descriptor, 'w')
        fcntl.flock(self.stream, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exception):
        fcntl.flock(self.stream, fcntl.LOCK_UN)
        self.stream.close()
