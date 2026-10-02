# Writing Standards

How the prose of every answer is written. Labels say how certain each assertion is; these standards
say how the sentences read. Both apply to every answer.

The rules below paraphrase two published standards and cite them; they do not reproduce their text.

## Plain language: ABNT NBR ISO 24495-1:2024

ABNT NBR ISO 24495-1:2024 is the Brazilian adoption of ISO 24495-1:2023, the plain-language
standard. A text is in plain language when its intended readers can find what they need, understand
it, and use it. It rests on four principles:

| Principle | Applied to an answer |
| --- | --- |
| Relevance | Give the reader what they need for their next action, and nothing that only shows effort. |
| Findability | Put the core answer in the first sentence; order the rest by depth so the reader finds detail where they expect it. |
| Understandability | Use common words, short sentences, and a defined term the first time it appears. |
| Usability | Make the answer actionable: name the command, the file, or the decision the reader can act on. |

## Simplified technical writing: ASD-STE100 Issue 9

ASD-STE100, Simplified Technical English, Issue 9, sets writing rules for technical text. Its
writing rules transfer to pt-BR prose; the English controlled dictionary does not transfer, so do
not translate its approved-word list into Portuguese.

- Keep a procedural sentence, one that tells the reader to do something, to 20 words or fewer.
- Keep a descriptive sentence to 25 words or fewer.
- Write one instruction per sentence, unless two actions happen at the same time.
- Use the active voice: name who or what acts.
- Use one term per concept: once a word names a thing, keep using that word for it.

## Language

Write pt-BR prose when the user writes pt-BR. Technical terms, jargon, and proper names stay in
English inline, such as guard clause, idempotency, RAG, or OAuth. Explain an unfamiliar term inline
the first time it appears.

## Character budget

| Kind of answer | Budget in counted characters |
| --- | --- |
| Direct question | 800 or fewer |
| Explanation or decision | 1600 or fewer |
| Code review, diagnosis, or plan | Exempt for now |

Counted text is prose, paragraphs, headings, and list items, labels included. Fenced blocks (code
and diagrams) and table rows do not count. Whitespace runs count as one space, and each Unicode
code point counts as one character. The output-response eval applies the same rule with a counting
script.

A diagnosis investigates a concrete failure in the user's system with inspected tool output; any
other "why" question is an explanation and keeps its budget. When an answer does not fit, move
repeated fields into a table, cut examples and redundancy, or offer the next layer on request;
never drop a label, the falsifying result, or a material limitation to fit.

## Sources

- ISO 24495-1:2023, Plain language, Part 1: Governing principles and guidelines; adopted in Brazil
  as ABNT NBR ISO 24495-1:2024.
- ASD-STE100, Simplified Technical English, Issue 9, AeroSpace, Security and Defence Industries
  Association of Europe (ASD).
