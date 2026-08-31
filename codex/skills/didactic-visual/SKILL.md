---
version: 1.1.0
name: didactic-visual
description: |
  Use when explaining a technical concept, decision, trade-off, architecture, failure mode, or
  implementation approach in conversation and a compact visual would make the relationship easier
  to understand. Requires the evidence skill and the active AGENTS.md evidence contract. Make
  explainability central: connect conclusions to evidence, mechanism, limitations, and action.
  Favor a conclusion-first answer, progressive disclosure, plain
  language, and useful tables, ASCII diagrams, or terminal charts. Do not use for source code,
  comments,
  docstrings, or repository documentation, where the project's conventions take precedence.
  Common triggers:
  explain this, compare these options, show the flow, make it visual, what is the trade-off, does
  this approach make sense, /didactic-visual.
type: capability
---

# Didactic Visual

Explain technical material so an experienced reader can understand the decision on the first pass.
Respond in the user's language and preserve established technical terms in English when clearer.

> Formatting earns its place only when it reduces cognitive effort.

## Hard prerequisite: evidence first

1. Load `oh-my-harness:evidence` and apply the active `AGENTS.md` evidence contract before drafting.
2. If either dependency is unavailable, Stop and report the missing prerequisite; do not continue
   under `didactic-visual`.
3. Let the evidence workflow establish claims, provenance, uncertainty, alternatives, and decisions.
4. Apply this skill only as the presentation layer after that factual substrate is sound.

```text
evidence skill + AGENTS.md contract → rigorous content → didactic-visual presentation
```

Never reclassify, hide, or simplify away uncertainty to make a visual cleaner.

## Build the answer

1. Lead with the conclusion or direct answer.
2. Give only the context needed to understand that conclusion.
3. Separate observed facts, derived results, inferences, hypotheses, estimates, unknowns, and
   decisions whenever mixing them could change what the reader does.
4. Choose prose, a list, a table, or an ASCII diagram by relationship type.
5. Add the next layer only when it materially helps or the user asks for more detail.

## Build an explanatory narrative

For a substantial explanation, use this spine and omit only stages that genuinely do not apply:

```text
problem → components → method → evidence → results → limitations → next steps
```

- Open long answers with a compact executive summary; skip it when the direct answer is already
  short.
- Use official names for services and systems on first mention, then define any abbreviation.
- Explain data concepts in accessible language without sacrificing technical precision.
- Distinguish verified facts from derived conclusions at the point where each appears.
- Add simple flows, comparison tables, and concrete examples only when they improve understanding.

## Make the explanation auditable

Treat explainability as the ability to inspect why a conclusion follows, not as disclosure of
private chain-of-thought. For every material conclusion, expose the concise, verifiable rationale:

```text
claim → evidence → mechanism → limitations → action
```

- Explain the mechanism that connects cause and effect instead of naming only the outcome.
- Identify the evidence or decision factor supporting each important conclusion.
- State limitations, counterexamples, and conditions that would change the answer.
- Name meaningful alternatives and why the recommendation differs from them.
- Never use "best practice" as a substitute for an inspectable reason.

## Prefer terminal-native visuals

When explicitly invoked for a substantial explanation, include at least one useful visual. Omit it
only when there is no meaningful relationship or quantitative data to visualize, and say why.

| Relationship | Prefer | Use when |
| --- | --- | --- |
| Sequence or state change | ASCII flow or timeline | Three or more dependent steps |
| Exact mappings or repeated fields | Table | Rows share the same comparison axes |
| Hierarchy or ownership | Tree | Nesting is harder to express linearly |
| Magnitude or ranking | Horizontal bars | Values need proportional comparison |
| Trend over time | Sparkline or time-series bars | Ordered measurements show movement |
| Distribution | Histogram | Buckets reveal concentration or spread |

For every quantitative terminal-native chart, state scale, unit, time window, source, and method.
Preserve proportional lengths, mark missing values, and never fabricate data or false precision.
Keep labels short and follow the visual with a one-sentence interpretation.

## Keep the response scannable

- Keep paragraphs to roughly three sentences.
- Use headings only for real sections.
- Use bold text as a sparse scanning anchor, not decoration.
- Use inline code for identifiers, commands, fields, and technical values.
- Put a blank line around CommonMark lists, headings, tables, and code blocks.
- Use emoji only as a status signal when it adds meaning.
- Avoid repeating the conclusion as a closing summary.

## Compact example

```text
installer --check
      │
      ├── static files ───── verified
      └── runtime trust ──── not inspected
                                 │
                                 ▼
                        health claim is limited
```

State the verified result and its boundary next to the visual; do not let formatting imply more.
