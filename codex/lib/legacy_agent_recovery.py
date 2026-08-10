from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class _Adoption:
    target: Path
    backup: Path
    temporary: Path


class LegacyAgentRecovery:
    """Tracks adopted files so a failed migration can restore every preimage."""

    def __init__(self) -> None:
        self._adoptions: tuple[_Adoption, ...] = ()

    def record(self, target: Path, backup: Path, temporary: Path) -> None:
        self._adoptions = (
            *self._adoptions,
            _Adoption(target, backup, temporary),
        )

    def restore_all(self) -> tuple[str, ...]:
        errors: list[str] = []
        for adoption in reversed(self._adoptions):
            errors.extend(self._restore(adoption))
        return tuple(errors)

    def clear(self) -> None:
        self._adoptions = ()

    def _restore(self, adoption: _Adoption) -> tuple[str, ...]:
        errors: list[str] = []
        try:
            self._restore_target(adoption)
        except OSError as error:
            errors.append(f"restore {adoption.target}: {error}")
        try:
            if adoption.temporary.exists() or adoption.temporary.is_symlink():
                adoption.temporary.unlink()
        except OSError as error:
            errors.append(f"cleanup {adoption.temporary}: {error}")
        return tuple(errors)

    @staticmethod
    def _restore_target(adoption: _Adoption) -> None:
        if not adoption.backup.is_file():
            return
        restored = adoption.target.with_name(f".{adoption.target.name}.omh-restore")
        shutil.copy2(adoption.backup, restored)
        restored.replace(adoption.target)
