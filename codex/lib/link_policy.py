from __future__ import annotations

from pathlib import Path

from lib.layout import InstallLayout


class ManagedLinkPolicy:
    """Validates persisted link entries before they can drive filesystem changes."""

    def __init__(
        self, layout: InstallLayout, conflict: type[RuntimeError]
    ) -> None:
        self._layout = layout
        self._conflict = conflict

    def validate(self, target: Path, source: Path) -> tuple[Path, Path]:
        if not target.is_absolute() or not source.is_absolute():
            raise self._invalid(target, source, "paths must be absolute")
        if not self._inside(source.resolve(strict=False), self._source_root()):
            raise self._invalid(target, source, "source escapes source_root")
        if target == self._layout.installed_adapter:
            if target.parent.resolve(strict=False) != self._layout.codex_home.resolve():
                raise self._invalid(target, source, "adapter target escapes codex_home")
            if source.resolve(strict=False) != self._layout.adapter.resolve():
                raise self._invalid(target, source, "adapter source is invalid")
            return target, source
        self._validate_leaf(target, source)
        return target, source

    def _validate_leaf(self, target: Path, source: Path) -> None:
        shapes = (
            (self._layout.installed_hooks, self._layout.source_root / "hooks", ".sh"),
            (self._layout.installed_rules, self._layout.adapter / "rules", ".rules"),
            (self._layout.custom_agents, self._layout.adapter / "agents", ".toml"),
        )
        for root, source_root, suffix in shapes:
            if target.parent == root:
                self._validate_shaped_leaf(target, source, root, source_root, suffix)
                return
        if target.parent == self._layout.personal_skills:
            self._validate_skill(target, source)
            return
        raise self._invalid(target, source, "target is outside managed roots")

    def _validate_shaped_leaf(
        self, target: Path, source: Path, root: Path, source_root: Path, suffix: str
    ) -> None:
        self._validate_parent(target, root)
        if source.parent != source_root or source.name != target.name:
            raise self._invalid(target, source, "source does not match target shape")
        if target.suffix != suffix:
            raise self._invalid(target, source, f"target must end with {suffix}")

    def _validate_skill(self, target: Path, source: Path) -> None:
        self._validate_parent(target, self._layout.personal_skills)
        roots = (self._layout.source_root / "skills", self._layout.adapter / "skills")
        if source.name != target.name or not any(
            self._inside(source.resolve(strict=False), root) for root in roots
        ):
            raise self._invalid(target, source, "skill source does not match target")

    def _validate_parent(self, target: Path, root: Path) -> None:
        home = (
            self._layout.agents_home
            if root == self._layout.personal_skills
            else self._layout.codex_home
        )
        expected = home.resolve(strict=False) / root.name
        if target.parent.resolve(strict=False) != expected:
            raise self._invalid(target, target, "managed parent resolves outside home")

    def _source_root(self) -> Path:
        return self._layout.source_root.resolve()

    @staticmethod
    def _inside(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root.resolve(strict=False))
        except ValueError:
            return False
        return True

    def _invalid(self, target: Path, source: Path, reason: str) -> RuntimeError:
        return self._conflict(
            f"invalid managed link manifest entry ({reason}): {target} -> {source}"
        )
