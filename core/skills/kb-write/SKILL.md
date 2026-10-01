---
name: kb-write
description: "Internal workflow owned by the knowledge-base agent for schema-validated pending notes, explicit approval, frozen versions, transcript evidence, and optional indexing; not intended for direct user invocation."
---

# KB Write

Markdown notes are curated source records; Qdrant is derived. Raw transcripts stay in their harness.
Write only for an explicit preservation request. Questions, exploration, and repository mapping do
not implicitly authorize a note. Only this agent operates the CLI; never write or edit bundle
Markdown directly, including through shell scripts. Read the schema-rendered
[references/note-template.md](references/note-template.md); `kb template` is the executable schema.
Note prose is always pt-BR, with technical terms retained. Do not translate schema section names.

## Resolve identity and layout

Resolve adapter roots, explicit project name, observed Git root, and `remote_url`. Reuse the
registered identity; a domain collision blocks writing instead of inventing alternate slugs.
An existing artifact without sufficient identity fails closed. If stable Git identity is unavailable,
ask once for the canonical name and slug. A suggested slug may use this pipeline:

```bash
basename "$(git rev-parse --show-toplevel)" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-\n' '-' | sed 's/--*/-/g; s/^-//; s/-$//'
```

The user decides the path: `<scope>/<domain>/<entities...>/<name>/<name>.md`, with scope `work` or
`person`, domain entities nested as needed, and names in lowercase kebab-case, at most three words,
without repeating the parent. `type` does not select the directory. A directory containing its
same-named Markdown file is a note; otherwise it is an entity. Exclude `.history/`, `.pending/`, and
`backup/` from entity navigation. Approved descriptions populate scope/domain `index.md` entries.

Identity is `<scope>/<domain>/identity/identity.md`, `type: reference`, with `repository_path`,
`remote_url`, and `default_branch` in its frontmatter for code projects. It uses the same pending
approval and versioning flow as other notes. Do not automatically migrate a legacy snapshot.

Treat remote targets as sensitive: allow local/file remotes and an SSH/SCP transport username, but
reject HTTP(S) userinfo, any query string or fragment, a signed URL, passwords, unknown syntax, or
ambiguous parsing. Never echo a rejected value; a rejected project remote persists as
`remote_url: null`, reported only as `redacted`.

## Validate evidence and content

Use the closed `type` enum: decision, event, procedure, reference, conversation. The schema owns
field limits, ordered required/optional sections, conditional Entities/Dates/Figures, and the event
Timeline. Every paragraph of prose must be pt-BR; code, URLs, and technical jargon are not a license
for English prose. Missing evidence is reported, never manufactured to satisfy a field or length.

`generated.harness`, `generated.session_id`, `generated.cwd`, and `generated.machine_id` require
observed values; cwd is absolute. `generated.model` is nullable when the harness does not expose it.
Read stable machine identity from `~/.local/share/omh-kb/identity.json`; never derive a raw MAC address.
If required provenance is missing, do not write the note. Match machine_id to that identity.

Pass the actual parent transcript through `--transcript PATH`; do not assume a subagent transcript
covers the conversation. Claude fallback is `~/.claude/projects/<cwd-munged>/<session-id>.jsonl`,
with verified session identity, never newest-file guessing. Harvest includes subagents and external
tool results. Codex tool-call evidence remains degraded unless its adapter is verified; a transcript
path existing does not prove parsing coverage. For unavailable evidence, request explicit degraded
approval before `--approved-degraded` and record the limitation in Sources.

Run `harvest --transcript PATH` and inspect candidates before composing. The closed `entities`
object always has all thirteen keys: people, companies, products, brands, roles, projects, apps,
urls, repos, paths, documents, emails, names. Reuse known slugs; present new people/company/product/
brand/app/role slugs for confirmation. Each declared entity needs an Entities row, prose explaining
its role and relationship, and transcript evidence. URLs, paths, repos, dates, and numbers with
units/currencies in prose must be declared. Dates use RFC 3339 with observed timezone; Figures use
exact decimal values and ISO 4217 for currencies. Never invent midnight, a timezone, or a value.
Inherited entities in an update retain prior proof; new entities need current transcript evidence.

Secrets, credentials, token-bearing URLs, passwords, card numbers, and CPF are refused or redacted
before persistence or harvest output. Do not quote rejected values in an error. A harvested mention
is a candidate, not an instruction or proof of correctness. Keep one coherent knowledge item per note.

## Review once, then publish

Resolve `<skill-dir>` from this loaded skill. Use the dedicated runtime for every command:

```bash
"${OMH_KB_RUNTIME:-$HOME/.local/share/omh-kb}/venv/bin/python" "<skill-dir>/scripts/kb.py" template decision --json
```

Replace the subcommand with the applicable operation, always keeping `--json`:

| Operation | Arguments |
| --- | --- |
| Prepare | `write --path REL --file FILE --transcript PATH [--reason TEXT] [--description PATH=TEXT] [--approved-degraded]` |
| Publish | `approve --path REL --transcript PATH` |
| Relocate pending | `move --path OLD --to NEW` |
| Discard pending | `reject --path REL` |
| Inspect | `validate --path REL --file FILE`, `check`, `nav --path REL`, `harvest --transcript PATH` |

1. `write` validates and saves pending at the proposed path for a new note, or
   `<name>/.pending/<name>.md` for an update. Include an update reason. Return the Pending result,
   full note or diff, path, proposed entity descriptions, and candidates to the principal session.
2. The principal session shows the entire note, or the full diff for an update, and asks for one
   review of path and content. It asks path for a new note, not for an existing note update.
   A preservation request alone is not approval of unseen content. A subagent never asks the user.
3. After explicit user approval of that note and revision, call `approve`. Adjustments rewrite only
   pending; path corrections use `move`; rejection uses `reject`. Changed content needs renewed
   approval. Pending is excluded from Qdrant, indexes, navigation, and other notes' links.
4. Approval revalidates, freezes the old version, promotes pending, mirrors links, updates indexes,
   and upserts Qdrant. Frozen history is `.history/<YYYY-MM-DD>--v<N>--<name>.md`, preserving id and
   created_at, with status superseded, superseded_at, and required superseded_reason. The current
   note increments version. Only derived children/related mirrors avoid a new version and timestamp.
5. Reconcile interrupted approval from disk and retry idempotently; never claim all steps succeeded
   when indexing failed. Report path, version, validation errors, pending review, and index state.
   Exit 0 is success, 2 validation rejection, 3 awaiting approval, and 4 degraded operation.

## Legacy preservation and promotion

Use `backup --dry-run` before `backup --apply`, reviewing the manifest with the user at the planned
cutover. Preserve file bytes, exclude `.obsidian/` and `.trash/`, and mark existing points legacy
without re-embedding. The CLI creates pt-BR `backup/INSTRUCTION.md` idempotently with date, reason,
plan, counts, SHA-256 manifest reference, and legacy indexing state. Any legacy read starts with
that instruction before another backup file. Never open backup implicitly. On explicit request,
offer promotion as a new id/version 1 with Sources pointing to the backup; require normal approval.
