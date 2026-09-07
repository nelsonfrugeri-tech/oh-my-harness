from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Type

from lib.atomic_file import atomic_write
from lib.layout import InstallLayout
from lib.link_manifest import ManagedLinkManifest


class ManagedAgentCopies:
    def __init__(self, layout: InstallLayout, conflict: Type[RuntimeError]) -> None:
        self._layout = layout
        self._conflict = conflict
        self._links = ManagedLinkManifest(layout, conflict)

    def preflight(self) -> None:
        records = self._records()
        expected = {self._target(source) for source in self._layout.agent_sources()}
        for target, (_, digest) in records.items():
            if target not in expected and self._digest(target) != digest:
                raise self._conflict(f"recusando remover agent modificado: {target}")
        for source in self._layout.agent_sources():
            self._check_available(source, self._target(source), records)

    def install(self) -> tuple[str, ...]:
        records = self._records()
        expected = {self._target(source) for source in self._layout.agent_sources()}
        results = [self._remove(target) for target in records if target not in expected]
        results.extend(self._copy(source, self._target(source)) for source in self._layout.agent_sources())
        results.append(self._write_manifest())
        return tuple(results)

    def validate(self) -> tuple[str, ...]:
        results = []
        for source in self._layout.agent_sources():
            target = self._target(source)
            if target.is_symlink() or not target.is_file() or target.read_bytes() != source.read_bytes():
                raise self._conflict(f"agent gerenciado inválido ou ausente: {target}")
            results.append(f"ok: {target}")
        manifest = self._layout.agents_manifest
        if not manifest.exists() or self._manifest_content() != manifest.read_text(encoding="utf-8"):
            raise self._conflict("manifesto de agents gerenciados ausente ou desatualizado")
        return tuple(results)

    def _check_available(
        self,
        source: Path,
        target: Path,
        records: dict[Path, tuple[Path, str]],
    ) -> None:
        self._check_parent_directory(target)
        if not target.exists() and not target.is_symlink():
            return
        if target.is_symlink():
            if self._links.owns(target, source):
                return
            raise self._conflict(f"recusando substituir path existente: {target}")
        if not target.is_file():
            raise self._conflict(f"recusando substituir path existente: {target}")
        if target.read_bytes() == source.read_bytes():
            return
        recorded = records.get(target)
        if recorded is None or self._digest(target) != recorded[1]:
            raise self._conflict(f"recusando substituir agent modificado: {target}")

    def _copy(self, source: Path, target: Path) -> str:
        target.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_text(encoding="utf-8")
        if target.is_file() and not target.is_symlink() and target.read_text(encoding="utf-8") == content:
            return f"ok: {target}"
        atomic_write(target, content)
        return f"copiado: {target}"

    def _remove(self, target: Path) -> str:
        target.unlink(missing_ok=True)
        return f"agent gerenciado desatualizado removido: {target}"

    def _records(self) -> dict[Path, tuple[Path, str]]:
        path = self._layout.agents_manifest
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise self._invalid_manifest() from error
        if not isinstance(data, dict) or data.get("version") != 1:
            raise self._invalid_manifest()
        entries = data.get("agents")
        if not isinstance(entries, list):
            raise self._invalid_manifest()
        records = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise self._invalid_manifest()
            target, source, digest = entry.get("target"), entry.get("source"), entry.get("sha256")
            if not all(isinstance(value, str) for value in (target, source, digest)):
                raise self._invalid_manifest()
            parsed_target = Path(target)
            if not self._safe_target(parsed_target) or len(digest) != 64:
                raise self._invalid_manifest()
            try:
                int(digest, 16)
            except ValueError as error:
                raise self._invalid_manifest() from error
            if parsed_target in records:
                raise self._invalid_manifest()
            records[parsed_target] = (Path(source), digest)
        return records

    def _write_manifest(self) -> str:
        content = self._manifest_content()
        path = self._layout.agents_manifest
        if path.exists() and path.read_text(encoding="utf-8") == content:
            return f"ok: {path}"
        atomic_write(path, content)
        return f"atualizado: {path}"

    def _manifest_content(self) -> str:
        agents = [
            {"target": str(self._target(source)), "source": str(source), "sha256": self._digest(source)}
            for source in self._layout.agent_sources()
        ]
        return json.dumps({"version": 1, "agents": agents}, indent=2) + "\n"

    def _target(self, source: Path) -> Path:
        return self._layout.custom_agents / source.name

    def _check_parent_directory(self, target: Path) -> None:
        if target.parent.is_symlink():
            raise self._conflict(f"recusando gerenciar agents dentro de symlink: {target.parent}")
        candidate = target.parent
        while not candidate.exists() and not candidate.is_symlink():
            candidate = candidate.parent
        if not candidate.is_dir():
            raise self._conflict(f"recusando criar dentro de path que não é diretório: {candidate}")

    def _digest(self, path: Path) -> str:
        return sha256(path.read_bytes()).hexdigest()

    def _safe_target(self, target: Path) -> bool:
        return (
            target.is_absolute()
            and target.parent == self._layout.custom_agents
            and target.suffix == ".toml"
            and target.name not in {".", ".."}
            and not target.parent.is_symlink()
        )

    def _invalid_manifest(self) -> RuntimeError:
        return self._conflict(
            f"manifesto de agents gerenciados inválido: {self._layout.agents_manifest}"
        )
