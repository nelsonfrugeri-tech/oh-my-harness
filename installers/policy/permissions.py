"""Load, validate, and evaluate the canonical permission policy.

The policy is the single source of truth for every harness renderer. ``evaluate`` is a reference
implementation of its semantics (deny > ask > allow); harness renderers approximate it with each
harness's native rule language, and the tests use it to define the expected outcome.
"""

from __future__ import annotations

import itertools
import json
import posixpath
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Optional, Sequence, Tuple, Union

EFFECTS: Final = ("ask", "deny")
CAPABILITIES: Final = ("fs_read", "shell")
HOME_KINDS: Final = ("file", "dir")
DEFAULT_EFFECT: Final = "allow"
SCHEMA_VERSION: Final = 1

_STRICTNESS: Final = {"allow": 0, "ask": 1, "deny": 2}
_RULE_ID: Final = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SEPARATORS: Final = frozenset({"&&", "||", ";", "|", "|&", "&", "\n"})
_TOP_LEVEL_KEYS: Final = frozenset({"version", "default_effect", "rules"})
_COMMON_KEYS: Final = frozenset({"id", "capability", "effect", "reason"})
_CAPABILITY_KEYS: Final = {
    "fs_read": frozenset({"paths"}),
    "shell": frozenset({"example", "prefixes", "globs"}),
}

Token = Union[str, Tuple[str, ...]]


@dataclass(frozen=True)
class HomePath:
    """A path relative to the user's home directory; a ``dir`` covers its whole subtree."""

    path: str
    kind: str


@dataclass(frozen=True)
class Rule:
    id: str
    capability: str
    effect: str
    reason: str
    example: Optional[str] = None
    any_globs: Tuple[str, ...] = ()
    home_paths: Tuple[HomePath, ...] = ()
    prefixes: Tuple[Tuple[Token, ...], ...] = ()
    globs: Tuple[str, ...] = ()

    def expansions(self) -> Tuple[Tuple[str, ...], ...]:
        """Return the cartesian product of every prefix, one literal token tuple per command."""
        return tuple(tokens for prefix in self.prefixes for tokens in expand_prefix(prefix))


def expand_prefix(prefix: Sequence[Token]) -> Tuple[Tuple[str, ...], ...]:
    """Expand one prefix whose inner tuples are unions into every literal token sequence."""
    choices = [(token,) if isinstance(token, str) else token for token in prefix]
    return tuple(itertools.product(*choices))


@dataclass(frozen=True)
class Policy:
    version: int
    default_effect: str
    rules: Tuple[Rule, ...]

    def by_effect(self, capability: str, effect: str) -> Tuple[Rule, ...]:
        return tuple(
            rule for rule in self.rules if rule.capability == capability and rule.effect == effect
        )


@dataclass(frozen=True)
class Decision:
    effect: str
    rule_ids: Tuple[str, ...]


def default_policy_path() -> Path:
    return Path(__file__).resolve().parents[2] / "core/policies/permissions.json"


def load_policy(path: Optional[Path] = None) -> Policy:
    source = path or default_policy_path()
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"política de permissões com JSON inválido em {source}: {error}") from error
    return parse_policy(data)


def parse_policy(data: object) -> Policy:
    if not isinstance(data, dict):
        raise ValueError("a política de permissões deve ser um objeto JSON")
    _require_keys(data, _TOP_LEVEL_KEYS, _TOP_LEVEL_KEYS, "política")
    if data["version"] != SCHEMA_VERSION:
        raise ValueError(f"versão da política não suportada: {data['version']!r}")
    if data["default_effect"] != DEFAULT_EFFECT:
        raise ValueError("default_effect da política deve ser 'allow'")
    raw_rules = data["rules"]
    if not isinstance(raw_rules, list) or not raw_rules:
        raise ValueError("a política deve declarar ao menos uma regra em rules")
    rules = tuple(_parse_rule(raw) for raw in raw_rules)
    identifiers = [rule.id for rule in rules]
    duplicates = sorted({item for item in identifiers if identifiers.count(item) > 1})
    if duplicates:
        raise ValueError(f"id de regra duplicado: {', '.join(duplicates)}")
    policy = Policy(SCHEMA_VERSION, DEFAULT_EFFECT, rules)
    for rule in rules:
        _require_example_matches(rule)
    return policy


def evaluate(
    policy: Policy,
    *,
    command: Optional[str] = None,
    path: Optional[str] = None,
    home: Optional[str] = None,
) -> Decision:
    """Return the strictest effect among matching rules; unmatched requests get the default.

    A shell ``command`` is split on shell separators and every segment is checked, mirroring the
    harnesses that evaluate compound commands per segment. A ``path`` is checked against fs_read
    rules; ``~`` in it and every ``home`` rule resolve against ``home``.
    """
    if (command is None) == (path is None):
        raise ValueError("informe exatamente um entre command e path")
    if command is not None:
        segments = _segments(command)
        matched = [
            rule
            for rule in policy.rules
            if rule.capability == "shell" and any(_shell_matches(rule, s) for s in segments)
        ]
    else:
        if home is None:
            raise ValueError("avaliar um path exige o diretório home")
        resolved = _resolve(path or "", home)
        matched = [
            rule
            for rule in policy.rules
            if rule.capability == "fs_read" and _path_matches(rule, resolved, home)
        ]
    if not matched:
        return Decision(policy.default_effect, ())
    strictest = max(_STRICTNESS[rule.effect] for rule in matched)
    winners = tuple(rule.id for rule in matched if _STRICTNESS[rule.effect] == strictest)
    effect = next(name for name, rank in _STRICTNESS.items() if rank == strictest)
    return Decision(effect, winners)


def prefix_matches(expansion: Sequence[str], tokens: Sequence[str]) -> bool:
    return len(tokens) >= len(expansion) and tuple(tokens[: len(expansion)]) == tuple(expansion)


def glob_matches(glob: str, text: str) -> bool:
    """Match a shell glob in which ``*`` stands for any text and every other character is literal."""
    pattern = ".*".join(re.escape(part) for part in glob.split("*"))
    return re.fullmatch(pattern, text, flags=re.DOTALL) is not None


def _parse_rule(raw: object) -> Rule:
    if not isinstance(raw, dict):
        raise ValueError("toda regra da política deve ser um objeto")
    identifier = raw.get("id")
    if not isinstance(identifier, str) or not _RULE_ID.match(identifier):
        raise ValueError(f"id de regra inválido: {identifier!r}")
    capability = raw.get("capability")
    if capability not in CAPABILITIES:
        raise ValueError(f"regra {identifier}: capability desconhecida {capability!r}")
    allowed = _COMMON_KEYS | _CAPABILITY_KEYS[capability]
    _require_keys(raw, _COMMON_KEYS, allowed, f"regra {identifier}")
    effect = raw["effect"]
    if effect not in EFFECTS:
        raise ValueError(f"regra {identifier}: effect desconhecido {effect!r}")
    reason = raw["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError(f"regra {identifier}: reason é obrigatório")
    if capability == "fs_read":
        any_globs, home_paths = _parse_paths(identifier, raw.get("paths"))
        return Rule(identifier, capability, effect, reason, any_globs=any_globs, home_paths=home_paths)
    example = raw.get("example")
    if not isinstance(example, str) or not example.strip():
        raise ValueError(f"regra {identifier}: regras shell exigem example")
    prefixes = _parse_prefixes(identifier, raw.get("prefixes"))
    globs = _parse_globs(identifier, raw.get("globs", []))
    return Rule(identifier, capability, effect, reason, example, prefixes=prefixes, globs=globs)


def _parse_paths(identifier: str, raw: object) -> Tuple[Tuple[str, ...], Tuple[HomePath, ...]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"regra {identifier}: regras fs_read exigem paths")
    any_globs = []
    home_paths = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError(f"regra {identifier}: todo item de paths deve ser um objeto")
        scope = item.get("scope")
        if scope == "any":
            _require_keys(item, {"scope", "glob"}, {"scope", "glob"}, f"regra {identifier}")
            glob = item["glob"]
            if not isinstance(glob, str) or not glob or "/" in glob:
                raise ValueError(f"regra {identifier}: glob inválido {glob!r}")
            any_globs.append(glob)
        elif scope == "home":
            keys = {"scope", "path", "kind"}
            _require_keys(item, keys, keys, f"regra {identifier}")
            home_paths.append(_parse_home_path(identifier, item["path"], item["kind"]))
        else:
            raise ValueError(f"regra {identifier}: scope desconhecido {scope!r}")
    return tuple(any_globs), tuple(home_paths)


def _parse_home_path(identifier: str, path: object, kind: object) -> HomePath:
    if not isinstance(path, str) or not path or path.startswith(("/", "~")):
        raise ValueError(f"regra {identifier}: path relativo ao home inválido {path!r}")
    if ".." in path.split("/") or "*" in path or posixpath.normpath(path) != path:
        raise ValueError(f"regra {identifier}: path relativo ao home inválido {path!r}")
    if kind not in HOME_KINDS:
        raise ValueError(f"regra {identifier}: kind desconhecido {kind!r}")
    return HomePath(path, str(kind))


def _parse_prefixes(identifier: str, raw: object) -> Tuple[Tuple[Token, ...], ...]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"regra {identifier}: regras shell exigem prefixes")
    prefixes = []
    for prefix in raw:
        if not isinstance(prefix, list) or not prefix:
            raise ValueError(f"regra {identifier}: todo prefixo deve ser uma lista não vazia")
        prefixes.append(tuple(_parse_token(identifier, token) for token in prefix))
    return tuple(prefixes)


def _parse_token(identifier: str, token: object) -> Token:
    if isinstance(token, str) and token:
        return token
    if (
        isinstance(token, list)
        and token
        and all(isinstance(choice, str) and choice for choice in token)
    ):
        return tuple(token)
    raise ValueError(f"regra {identifier}: token de prefixo inválido {token!r}")


def _parse_globs(identifier: str, raw: object) -> Tuple[str, ...]:
    if not isinstance(raw, list) or not all(
        isinstance(glob, str) and "*" in glob and glob.strip() == glob for glob in raw
    ):
        raise ValueError(f"regra {identifier}: globs deve ser uma lista de padrões com '*'")
    return tuple(raw)


def _require_keys(data: dict, required: frozenset, allowed: frozenset, where: str) -> None:
    missing = sorted(set(required) - set(data))
    unknown = sorted(set(data) - set(allowed))
    if missing:
        raise ValueError(f"{where}: campos obrigatórios ausentes: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"{where}: campos desconhecidos: {', '.join(unknown)}")


def _require_example_matches(rule: Rule) -> None:
    if rule.capability != "shell":
        return
    if not any(_shell_matches(rule, segment) for segment in _segments(rule.example or "")):
        raise ValueError(f"regra {rule.id}: example não casa com a própria regra")


def _segments(command: str) -> Tuple[Tuple[str, ...], ...]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError as error:
        raise ValueError(f"comando shell inválido: {command!r}") from error
    segments: list = [[]]
    for token in tokens:
        if token in _SEPARATORS:
            segments.append([])
        else:
            segments[-1].append(token)
    return tuple(tuple(segment) for segment in segments if segment)


def _shell_matches(rule: Rule, tokens: Tuple[str, ...]) -> bool:
    if any(prefix_matches(expansion, tokens) for expansion in rule.expansions()):
        return True
    text = " ".join(tokens)
    return any(glob_matches(glob, text) for glob in rule.globs)


def _resolve(path: str, home: str) -> str:
    if path == "~" or path.startswith("~/"):
        path = home + path[1:]
    return posixpath.normpath(path)


def _path_matches(rule: Rule, path: str, home: str) -> bool:
    name = posixpath.basename(path)
    if any(glob_matches(glob, name) for glob in rule.any_globs):
        return True
    for entry in rule.home_paths:
        target = posixpath.normpath(posixpath.join(home, entry.path))
        if path == target or (entry.kind == "dir" and path.startswith(target + "/")):
            return True
    return False
