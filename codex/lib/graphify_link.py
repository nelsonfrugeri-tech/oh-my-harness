from __future__ import annotations

from pathlib import Path


def compatible_external_graphify(source: Path, target: Path) -> bool:
    if source.name != "graphify" or target.is_symlink() or not target.is_dir():
        return False
    version_file = target / ".graphify_version"
    if not version_file.is_file():
        return False
    expected = _upstream_version(source / "SKILL.md")
    return version_file.read_text(encoding="utf-8").strip() == expected


def _upstream_version(skill_file: Path) -> str:
    for line in skill_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("upstream_version:"):
            return line.partition(":")[2].strip()
    return ""
