from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write(target: Path, content: str, *, mode: int | None = None) -> None:
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=target.parent, delete=False
    )
    temporary = Path(handle.name)
    try:
        with handle:
            if mode is not None:
                os.fchmod(handle.fileno(), mode)
            handle.write(content)
        publication_mode = (
            mode
            if mode is not None
            else target.stat().st_mode if target.exists() else 0o644
        )
        temporary.chmod(publication_mode)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
