from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write(target: Path, content: str) -> None:
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False)
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(content)
        temporary.chmod(target.stat().st_mode if target.exists() else 0o644)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
