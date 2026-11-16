"""Render the canonical permission policy to each harness's native format.

Run from the repository root:

    python3 -m installers.policy.render --check
    python3 -m installers.policy.render --write
    python3 -m installers.policy.render --check-claude ~/.claude/settings.json
    python3 -m installers.policy.render --gaps codex
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Final, List, Optional, Sequence, Tuple

from .permissions import Policy, Rule, Token, expand_prefix, load_policy, prefix_matches

HARNESSES: Final = ("claude", "codex", "kiro")
RULES_HEADER: Final = (
    "# omh-managed: generated from core/policies/permissions.json — do not edit"
)
KIRO_HEADER: Final = (
    "# Generated from core/policies/permissions.json by `python3 -m installers.policy.render"
    " --write`.\n"
    "# Do not edit by hand. Copy to ~/.kiro/settings/permissions.yaml; see"
    " harness/kiro/README.md.\n"
)
CLAUDE_MODE: Final = "bypassPermissions"
_CODEX_DECISIONS: Final = {"ask": "prompt", "deny": "forbidden"}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def claude_settings_path(root: Optional[Path] = None) -> Path:
    return (root or repository_root()) / "harness/claude/settings.json"


def kiro_permissions_path(root: Optional[Path] = None) -> Path:
    return (root or repository_root()) / "harness/kiro/permissions.yaml"


# Claude Code ---------------------------------------------------------------------------------


def claude_entries(policy: Policy, effect: str) -> Tuple[str, ...]:
    """Return the Claude Code rule strings for one effect, in policy order, without duplicates."""
    entries: List[str] = []
    for rule in policy.rules:
        if rule.effect != effect:
            continue
        candidates = _claude_read(rule) if rule.capability == "fs_read" else _claude_bash(rule)
        entries.extend(entry for entry in candidates if entry not in entries)
    return tuple(entries)


def render_claude(policy: Policy) -> Dict[str, object]:
    return {
        "permissions": {
            "defaultMode": CLAUDE_MODE,
            "ask": list(claude_entries(policy, "ask")),
            "deny": list(claude_entries(policy, "deny")),
        }
    }


def render_claude_text(policy: Policy) -> str:
    return json.dumps(render_claude(policy), indent=2, ensure_ascii=False) + "\n"


def check_claude_settings(policy: Policy, settings: object) -> Tuple[str, ...]:
    """Return what a user settings object lacks to enforce the rendered policy."""
    permissions = settings.get("permissions") if isinstance(settings, dict) else None
    if not isinstance(permissions, dict):
        return ("permissions ausente",)
    problems: List[str] = []
    if permissions.get("defaultMode") != CLAUDE_MODE:
        problems.append(f"permissions.defaultMode deve ser {CLAUDE_MODE!r}")
    for effect in ("ask", "deny"):
        present = permissions.get(effect)
        present = present if isinstance(present, list) else []
        problems.extend(
            f"permissions.{effect} sem {entry}"
            for entry in claude_entries(policy, effect)
            if entry not in present
        )
    return tuple(problems)


def _claude_read(rule: Rule) -> Tuple[str, ...]:
    entries = [f"Read(//**/{glob})" for glob in rule.any_globs]
    for entry in rule.home_paths:
        suffix = "/**" if entry.kind == "dir" else ""
        entries.append(f"Read(~/{entry.path}{suffix})")
    return tuple(entries)


def _claude_bash(rule: Rule) -> Tuple[str, ...]:
    entries: List[str] = []
    for command in _literal_commands(rule):
        entries.extend((f"Bash({command})", f"Bash({command} *)"))
    entries.extend(f"Bash({glob})" for glob in rule.globs)
    return tuple(entries)


# Codex ---------------------------------------------------------------------------------------


def render_codex_rules(policy: Policy) -> str:
    """Render shell rules as Codex execpolicy ``prefix_rule`` calls; globs are reported as gaps."""
    blocks = [RULES_HEADER]
    for rule in policy.rules:
        if rule.capability != "shell":
            continue
        for prefix in rule.prefixes:
            blocks.append(_codex_prefix_rule(rule, prefix))
    return "\n\n".join(blocks) + "\n"


def render_codex_filesystem(policy: Policy, home: Path) -> Tuple[str, ...]:
    """Render fs_read rules as TOML lines for the managed Codex permissions profile."""
    home_paths = [entry for rule in policy.by_effect("fs_read", "ask") for entry in rule.home_paths]
    home_paths += [entry for rule in policy.by_effect("fs_read", "deny") for entry in rule.home_paths]
    globs = [glob for rule in policy.rules if rule.capability == "fs_read" for glob in rule.any_globs]
    lines = ["[permissions.oh-my-harness.filesystem]"]
    lines.extend(f"{_toml_string(f'{home}/{entry.path}')} = \"deny\"" for entry in home_paths)
    lines.extend(("", '[permissions.oh-my-harness.filesystem.":workspace_roots"]', '"." = "write"'))
    lines.extend(f"{_toml_string(f'**/{glob}')} = \"deny\"" for glob in _unique(globs))
    return tuple(lines)


def _codex_prefix_rule(rule: Rule, prefix: Tuple[Token, ...]) -> str:
    pattern = [token if isinstance(token, str) else list(token) for token in prefix]
    expansions = expand_prefix(prefix)
    example_tokens = (rule.example or "").split()
    examples = [rule.example] if any(prefix_matches(e, example_tokens) for e in expansions) else []
    fields = [
        f"    pattern = {json.dumps(pattern, ensure_ascii=False)},",
        f"    decision = {json.dumps(_CODEX_DECISIONS[rule.effect])},",
        f"    justification = {json.dumps(f'oh-my-harness {rule.id}: {rule.reason}', ensure_ascii=False)},",
    ]
    if examples:
        fields.append(f"    match = {json.dumps(examples, ensure_ascii=False)},")
    return "prefix_rule(\n" + "\n".join(fields) + "\n)"


# Kiro ----------------------------------------------------------------------------------------


def render_kiro(policy: Policy) -> str:
    lines = [KIRO_HEADER.rstrip("\n"), "rules:", "  # default_effect: allow everything not matched below."]
    lines += ["  - capability: all", "    effect: allow"]
    ordered = (
        *policy.by_effect("fs_read", "ask"),
        *policy.by_effect("fs_read", "deny"),
        *policy.by_effect("shell", "ask"),
        *policy.by_effect("shell", "deny"),
    )
    for rule in ordered:
        patterns = _kiro_read(rule) if rule.capability == "fs_read" else _kiro_shell(rule)
        lines.append("")
        lines.append(f"  # {rule.id}: {rule.reason}")
        lines.append(f"  - capability: {rule.capability}")
        lines.append("    match:")
        lines.extend(f"      - {json.dumps(pattern, ensure_ascii=False)}" for pattern in patterns)
        lines.append(f"    effect: {rule.effect}")
    return "\n".join(lines) + "\n"


def _kiro_read(rule: Rule) -> Tuple[str, ...]:
    entries = [f"**/{glob}" for glob in rule.any_globs]
    for entry in rule.home_paths:
        entries.append(f"~/{entry.path}/**" if entry.kind == "dir" else f"~/{entry.path}")
    return tuple(entries)


def _kiro_shell(rule: Rule) -> Tuple[str, ...]:
    entries: List[str] = []
    for command in _literal_commands(rule):
        entries.extend((command, f"{command} *"))
    entries.extend(rule.globs)
    return tuple(_unique(entries))


# Gaps ----------------------------------------------------------------------------------------


def gaps(harness: str, policy: Policy) -> Tuple[str, ...]:
    """List what the harness rendering cannot express faithfully, derived from the policy."""
    if harness not in HARNESSES:
        raise ValueError(f"harness desconhecido: {harness!r}")
    found: List[str] = []
    if harness in ("claude", "kiro"):
        found.extend(
            f"{rule.id}: prefix {' '.join(tokens)!r} has a literal '*' and is not rendered;"
            " the broader ask rule still prompts"
            for rule in policy.rules
            for tokens in rule.expansions()
            if any("*" in token for token in tokens)
        )
    if harness == "claude":
        found.append(
            "Bash rules match the command text: /bin/rm, bash -c, python -c, and similar"
            " indirections are not covered"
        )
        found.append("whether ask Read() rules also gate Bash cat is not verified")
    if harness == "codex":
        found.extend(
            f"{rule.id}: glob {glob!r} is skipped; execpolicy only matches token prefixes"
            for rule in policy.rules
            for glob in rule.globs
        )
        found.append(
            "fs_read ask becomes a sandbox read deny; the user sees an escalation request,"
            " not a read prompt"
        )
        found.append("any-depth secret globs apply only inside workspace roots")
        found.append("prefix matching misses reordered flags, such as git push origin --force")
    if harness == "kiro":
        found.append(
            "delete_file is not gateable by permissions.yaml; exclude it in a custom agent"
            " with excludedTools"
        )
        found.append("whether ~ expands in fs_read patterns is not verified")
    found.append("a plain git push while on the default branch cannot be gated; use branch protection")
    return tuple(found)


# Shared helpers ------------------------------------------------------------------------------


def _literal_commands(rule: Rule) -> Tuple[str, ...]:
    """Expansions without a literal '*', which glob-based rule languages would read as a wildcard."""
    return tuple(
        " ".join(tokens)
        for tokens in rule.expansions()
        if not any("*" in token for token in tokens)
    )


def _unique(items: Sequence[str]) -> List[str]:
    seen: List[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


# CLI -----------------------------------------------------------------------------------------


def _rendered_files(policy: Policy, root: Path) -> Tuple[Tuple[Path, str], ...]:
    return (
        (claude_settings_path(root), render_claude_text(policy)),
        (kiro_permissions_path(root), render_kiro(policy)),
    )


def _arguments(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Renderiza a política canônica de permissões.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="Regrava os arquivos gerados.")
    group.add_argument("--check", action="store_true", help="Falha se um arquivo gerado divergir.")
    group.add_argument("--check-claude", type=Path, metavar="SETTINGS")
    group.add_argument("--gaps", choices=HARNESSES)
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--root", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _arguments(argv)
    root = arguments.root or repository_root()
    try:
        policy = load_policy(arguments.policy)
    except (OSError, ValueError) as error:
        print(f"erro: {error}", file=sys.stderr)
        return 1
    if arguments.gaps:
        print("\n".join(gaps(arguments.gaps, policy)))
        return 0
    if arguments.check_claude:
        return _check_claude(policy, arguments.check_claude.expanduser())
    stale = [path for path, text in _rendered_files(policy, root) if _read(path) != text]
    if arguments.check:
        for path in stale:
            print(f"desatualizado: {path}", file=sys.stderr)
        return 1 if stale else 0
    for path, text in _rendered_files(policy, root):
        if path in stale:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(f"atualizado: {path}")
        else:
            print(f"ok: {path}")
    return 0


def _check_claude(policy: Policy, settings_path: Path) -> int:
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"erro: não foi possível ler {settings_path}: {error}", file=sys.stderr)
        return 1
    problems = check_claude_settings(policy, settings)
    for problem in problems:
        print(f"faltando: {problem}", file=sys.stderr)
    if not problems:
        print(f"ok: {settings_path}")
    return 1 if problems else 0


def _read(path: Path) -> Optional[str]:
    return path.read_text(encoding="utf-8") if path.exists() else None


if __name__ == "__main__":
    raise SystemExit(main())
