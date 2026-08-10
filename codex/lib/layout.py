from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstallLayout:
    source_root: Path
    codex_home: Path
    agents_home: Path

    @property
    def adapter(self) -> Path:
        return self.source_root / "codex"

    @property
    def global_agents_file(self) -> Path:
        return self.codex_home / "AGENTS.md"

    @property
    def local_agents_file(self) -> Path:
        return self.codex_home / "AGENTS.local.md"

    @property
    def hooks_file(self) -> Path:
        return self.codex_home / "hooks.json"

    @property
    def installed_adapter(self) -> Path:
        return self.codex_home / "oh-my-harness"

    @property
    def links_manifest(self) -> Path:
        return self.codex_home / "oh-my-harness-links.json"

    @property
    def personal_skills(self) -> Path:
        return self.agents_home / "skills"

    @property
    def custom_agents(self) -> Path:
        return self.codex_home / "agents"

    @property
    def installed_hooks(self) -> Path:
        return self.codex_home / "hooks"

    @property
    def installed_rules(self) -> Path:
        return self.codex_home / "rules"

    def skill_sources(self) -> tuple[Path, ...]:
        candidates = (
            *self.source_root.glob("skills/**/SKILL.md"),
            *self.adapter.glob("skills/**/SKILL.md"),
        )
        skills = sorted(
            path.parent for path in candidates if path.parent.name != "claude-code"
        )
        by_name: dict[str, Path] = {}
        for path in skills:
            if path.name in by_name:
                raise ValueError(f"duplicate skill leaf name: {path.name}")
            by_name[path.name] = path
        return tuple(by_name.values())

    def agent_sources(self) -> tuple[Path, ...]:
        return tuple(sorted((self.adapter / "agents").glob("*.toml")))

    def hook_sources(self) -> tuple[Path, ...]:
        return tuple(sorted(self.source_root.glob("hooks/*.sh")))

    def rule_sources(self) -> tuple[Path, ...]:
        return tuple(sorted(self.adapter.glob("rules/*.rules")))
