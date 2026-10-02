"""Count the output-response character budget and long sentences in one saved response."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal

ResponseKind = Literal["direct", "explanation", "decision", "code_review", "diagnosis", "plan"]
LIMITS: Final = MappingProxyType({
    "direct": 800,
    "explanation": 1600,
    "decision": 1600,
    "code_review": None,
    "diagnosis": 2800,
    "plan": None,
})
SENTENCE_WORD_LIMIT: Final = 25
_OPEN = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
_CLOSE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")
_QUOTE = re.compile(r"^\s*(?:>\s?)+")
_BLOCK_START = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
# Abbreviations whose period does not end a sentence; the list is deliberately short.
_ABBREVIATIONS: Final = frozenset({"e.g.", "i.e.", "vs.", "p.", "ex.", "sr.", "sra.", "dr.", "dra."})


@dataclass(frozen=True)
class WithinBudget:
    chars: int
    limit: int


@dataclass(frozen=True)
class OverBudget:
    chars: int
    limit: int
    excess: int


@dataclass(frozen=True)
class Exempt:
    kind: str


@dataclass(frozen=True)
class Sentence:
    words: int
    text: str


@dataclass(frozen=True)
class Report:
    status: WithinBudget | OverBudget | Exempt
    long_sentences: tuple[Sentence, ...]


def budget_for(kind: ResponseKind | str) -> int | None:
    if kind not in LIMITS:
        raise ValueError(f"unknown response kind: {kind}")
    return LIMITS[kind]


def _opening_fence(line: str) -> str | None:
    marker = _OPEN.match(line)
    if marker is None or (marker.group(1)[0] == "`" and "`" in marker.group(2)):
        return None
    return marker.group(1)


def _closes(line: str, fence: str) -> bool:
    marker = _CLOSE.match(line)
    return marker is not None and marker.group(1).startswith(fence)


def counted_lines(response: str) -> tuple[str, ...]:
    kept: list[str] = []
    fence: str | None = None
    for line in response.splitlines():
        if fence is not None:
            fence = None if _closes(line, fence) else fence
        elif (opened := _opening_fence(line)) is not None:
            fence = opened
        elif not _QUOTE.sub("", line).lstrip().startswith("|"):
            kept.append(line)
    return tuple(kept)


def counted_text(response: str) -> str:
    return " ".join(" ".join(counted_lines(response)).split())


def count_chars(text: str) -> int:
    return len(text)


def blocks(response: str) -> tuple[str, ...]:
    grouped: list[list[str]] = []
    for quoted in counted_lines(response):
        line = _QUOTE.sub("", quoted)
        if not line.strip():
            grouped.append([])
        elif _BLOCK_START.match(line) or not grouped:
            grouped.append([line])
        else:
            grouped[-1].append(line)
    joined = (" ".join(" ".join(group).split()) for group in grouped if group)
    return tuple(_BLOCK_START.sub("", text, count=1) for text in joined)


def _sentences(block: str) -> tuple[str, ...]:
    merged: list[str] = []
    for part in _SENTENCE_END.split(block):
        if merged and merged[-1].split()[-1].lower() in _ABBREVIATIONS:
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    return tuple(merged)


def long_sentences(paragraphs: tuple[str, ...]) -> tuple[Sentence, ...]:
    sentences = (part for block in paragraphs for part in _sentences(block))
    measured = (Sentence(len(text.split()), text) for text in sentences)
    return tuple(s for s in measured if s.words > SENTENCE_WORD_LIMIT)


def check(kind: ResponseKind | str, response: str) -> Report:
    limit = budget_for(kind)
    chars = count_chars(counted_text(response))
    sentences = long_sentences(blocks(response))
    if limit is None:
        return Report(Exempt(kind), sentences)
    if chars > limit:
        return Report(OverBudget(chars, limit, chars - limit), sentences)
    return Report(WithinBudget(chars, limit), sentences)


def render(report: Report) -> dict[str, object]:
    names = {WithinBudget: "within_budget", OverBudget: "over_budget", Exempt: "exempt"}
    fields = asdict(report.status)
    return {
        "status": names[type(report.status)],
        "chars": fields.get("chars"),
        "limit": fields.get("limit"),
        "excess": fields.get("excess", 0),
        "long_sentences": [asdict(sentence) for sentence in report.long_sentences],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, choices=sorted(LIMITS))
    parser.add_argument("response", type=Path)
    args = parser.parse_args(argv)
    try:
        response = args.response.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        parser.error(f"cannot read {args.response}: {error}")
    report = check(args.kind, response)
    print(json.dumps(render(report), ensure_ascii=False, indent=2))
    return 1 if isinstance(report.status, OverBudget) else 0


if __name__ == "__main__":
    sys.exit(main())
