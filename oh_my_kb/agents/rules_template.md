# kb-mcp — memory and knowledge base rules

kb-mcp is this project's long-term memory. Notes persist as Markdown files
indexed in Qdrant. The active universe is **{universe}**. Every query and write
is scoped to it automatically — never pass the universe as a tool argument.

Four tools: `kb_search` (semantic retrieval), `kb_tree` (structural directory),
`kb_expand` (full note + resolved links), `kb_write` (register/supersede a note).

---

## When to search — `kb_search`

Use when the user refers to past context, an established decision, convention,
or procedure, and the information is not already in the current session.
Also prefer `kb_search` when the universe is large or the question is about
content similarity ("what do we know about X?", "what's our policy on Y?").

Do not use `kb_search` to explore structure — that is `kb_tree`.

---

## When to navigate — `kb_tree` + `kb_expand`

Use `kb_tree` when the question is structural: "what exists?", "what topics
does this universe cover?", "what notes are in project X?". It returns a
project-grouped map of note ids, titles, types, and summaries — no embedding
cost, no full body.

Use `kb_expand` to read a note in full and resolve its outbound links. Follow
the knowledge graph hop by hop by calling `kb_expand` again on any returned
link id. Chain calls for multi-hop exploration:

```
kb_tree → pick id → kb_expand → follow link id → kb_expand → ...
```

Prefer navigation over search when the universe or project is small, or when
the question is about relationships between notes.

---

## When to write — `kb_write`

Write **only** when the user explicitly asks to register, record, annotate, or
save something. Do not write as a side-effect of answering a question.

Before every `kb_write` call, read both resources in order:

1. `skill://scribe/SKILL.md` — reasoning process: when to write, how to pick
   the note type, how to write a dense self-contained summary (200–800 chars of
   specific prose, not a label), how to extract entities, how to propose links.
2. `skill://scribe/template.md` — the exact Markdown structure the `body` field
   must follow, section by section, per note type (`decision`, `event`,
   `procedure`, `reference`, `conversation`).

To **update** an existing note: find it with `kb_search`, then call `kb_write`
with `supersedes` set to the old note's UUID. The old note is preserved as
history; the new note carries the updated content.

Before writing, run `kb_search` on the note's topic and include relevant
existing note UUIDs in `links_out` — this builds the navigable knowledge graph.

---

## Decision guide

```
User refers to past context or an established convention?
  └─ not in session → kb_search

User asks what exists or what relates?
  └─ kb_tree for the map → kb_expand to open a note → repeat to follow links

User explicitly asks to record / register / save something?
  └─ READ skill://scribe/SKILL.md AND skill://scribe/template.md FIRST
  └─ kb_write (set supersedes if updating an existing note)

None of the above → answer from session context; no kb call needed
```

---

## Resources

- `skill://scribe/SKILL.md` — reasoning: type choice, summary quality, entity
  extraction, link proposals, new vs. supersede decision.
- `skill://scribe/template.md` — note body format: required and optional
  sections per note type.
