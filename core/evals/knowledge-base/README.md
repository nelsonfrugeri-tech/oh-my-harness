# Knowledge Base Eval Protocol

This corpus specifies behavior for plan `kb-note-model` revision 1. Unit tests check the evaluator
and corpus format, **not agent quality**. No agent run, human language label, or calibrated judge
result is included or claimed. The missing human labels block KR7/KR10 acceptance and the dependent
KR6a correctness gate; they do not block implementing deterministic checks.

## Run an evaluation

Record harness, exact model (or explicitly unknown), model family, commit, skill hashes, fixture
hashes, date, evaluator version, and original transcript locations. Start a fresh session for every
case and repetition, with `claude --agent oh-my-harness:knowledge-base` or the installed Codex
counterpart. Run the conversational approval scenarios through a principal session that delegates
to that agent; the principal must remain responsible for showing the review and asking the user.
Use an isolated fixture bundle and Qdrant collection, never the user's bundle. Record all required
behaviors as pass, fail, or unexercised with supporting original transcript locators.

1. Create fixture facts, notes, and expected answers **before** running the candidate. The eight
   `approval-*` cases from `approval-new` through `approval-multiple` form the KR5 canary. Configure
   existing notes for `approval-update`, known and unknown entities for `approval-entities`, and
   two distinct notes for `approval-multiple`. For move/rewrite/reject cases, send that exact review
   instruction only after presentation; for multiple notes approve only one first. Send explicit
   note-specific approval only after the candidate asks. Save every scripted user turn.
2. For `navigation-01` through `navigation-10`, prepare an initial note and a graph whose answer is
   only in the specified parent, child, or sibling. Use unique facts per case, unrelated
   distractors,
   index pages, and a locked expected answer. Store these evaluator assets outside candidate access.
   Ensure the answer is absent from the initial note and prompt. Do not feed required behaviors or
   judge labels to the candidate. Record fixture IDs and hashes alongside the results.
3. Prepare a superseded version with a reason for `history-reason`, a legacy note and
`backup/INSTRUCTION.md` for
   `legacy-request`, and an earlier disposable transcript for `session-retirement`. The ontology
   fixture provides a recruiter, company, proposal, deadline, and transcript evidence for each;
   invented details are failures. Run entity validation with `--transcript` on generated notes.
4. Save complete main and subagent transcripts, tool arguments/results, generated note revisions,
   actual read/write paths, Qdrant state, and the final answer. Preserve failures and missing runs.
   A parser or tool coverage gap makes the affected check unexercised. Fixture creators own cleanup.
5. Independently normalize the recorded observations into the event contract below, keeping a
   source locator on every event. An evaluator must inspect original tool arguments and results;
   candidate claims and quoted examples are not observed calls. Annotate consent only for an actual
   user message approving the specific reviewed note/revision. Ambiguous consent is not approval.
6. Run `python3 core/evals/knowledge-base/check_transcript.py /tmp/kb-eval-events.json` on that
   independently produced artifact. Exit 0 means checked events passed, 1 means observed failure,
   and 2 means unavailable/malformed/incomplete evidence. This is not a raw JSONL parser and cannot
   establish the authenticity or completeness of evaluator annotations by itself.
7. Run the eight KR5 cases three times each (24 runs). A case achieves pass^3 only if all three
   observed runs pass; all eight must achieve it. Run the ten navigation cases three times each
   (30 runs), score correctness with the calibrated judge, and require at least nine case majorities
   plus at most two navigation calls in every run. These are regression canaries, not population
   success-rate estimates. Missing runs never count as passes.
8. Score S25, S36, S37, S39, and S50 separately. The checker covers approval ordering, navigation
   count, current-state history exclusion, session JSON writes, and session-memory use. Legacy
   promotion, entity confirmation, actual freezing timing, pending exclusion from Qdrant, and
   semantic correctness need artifact/integration evidence; no checker pass claims those behaviors.

## Normalized event contract

Input is a JSON object with `complete: boolean`, `events: [...]`, and optional boolean selectors
`navigation`, `current_state`, `session_recall`, and `legacy_read`, plus optional `bundle_root`
(the observed absolute bundle path). File paths must be normalized without `..`; relative paths
are bundle-relative. Absolute accesses require `bundle_root`, and accesses outside that root do
not count as bundle history or legacy reads. Resolve symlinks when annotating actual targets.
`complete` means the independent evaluator has accounted for main and subagent tool effects and
ordering. Set it false if shell writes, missing
outputs, truncated transcripts, or concurrent calls cannot be resolved. Every event has `kind` and
`source` (original transcript path plus line/call ID). Events are in observed causal order.

- `pending`: `note`, `revision`, `content`, `update`; content is exact complete note or expected
  update diff. A new pending event invalidates earlier consent for that note.
- `present`: `note`, `revision`, `actor`, `content`, `path_shown`, `candidates_shown`; actor must be
  `main`, content must match the pending artifact.
- `ask`: `note`, `revision`, `actor`, `asks_path`; main asks after presentation; a new note asks
  path, an update does not.
- `consent`: `note`, `revision`, `actor`, `approved`; only actual `user` approval after the question
  qualifies. Repeating the same valid question or consent is idempotent; refusal
  invalidates consent, and a new pending revision requires a new review.
- `approve`: `note`, `revision`; actual `kb approve` invocation, not prose. Consumes consent.
- `nav`: One actual `kb nav` invocation.
- `read`, `write`: `path`; one actual file access, including shell and subagent effects. Every
  `write` also requires boolean `session_record`, independently classified from the observed
  content and purpose, not the filename. True identifies a curated session JSON record forbidden
  by KR11, wherever written; false covers other writes, including automatic raw transcript capture.
  If classification is unavailable, omit it: the checker returns unexercised, never pass.
- `session_memory`: Actual invocation of the installed session-memory capability.

`note` is a stable fixture identity, so moving its path does not detach consent from its content.
`revision` identifies the exact pending bytes/diff, not just the eventual integer version. Retain
hashes in the run manifest. Locators are mandatory but not cryptographic provenance. Do not accept
candidate-generated annotations as evidence. Unknown event kinds and malformed fields are rejected.
A transcript with no events is unexercised. Result counts refer only to supplied events.

With `legacy_read: true`, the checker requires a read of `backup/INSTRUCTION.md` before any
other backup file. S51 (idempotent Portuguese instruction generation with date, reason, plan,
counts, SHA-256 manifest and legacy point count) requires integration artifacts, not a trace claim.

## Human labels and judge calibration — pending

KR7 requires at least 60 Portuguese notes with technical jargon and 30 English notes labeled by a
human. Preserve note text, immutable ID/hash, labeler, date, paragraph labels, and adjudication of
mixed text. Include code, URLs, tables, short paragraphs, and English inserted in Portuguese.
Generated examples can seed annotation but remain **unlabeled** until human review. Keep tuning
examples distinct from the locked acceptance corpus; never count copied templates as independent
human observations. Report both false rejections and false acceptances and the actual denominators.
Do not claim the rule-of-three bound for an unrepresentative sample or beyond its assumptions.

KR10 needs 20 human-labeled notes and a judge from a different model family than the generator.
For each entity label `role_present` and `relation_present` independently, with exact prose
evidence.
The rubric asks whether prose identifies who/what the entity is and how it relates to this event or
other entities; an isolated list or table does not supply narrative context. An entity passes only
when both labels are true. Use explicit abstention for missing evidence. Lock the rubric and model
configuration before evaluation; blind the judge to author/model identity and human labels.

Report human/judge confusion counts, TPR, TNR, and Cohen's kappa, including undefined denominators,
plus the observed entity pass fraction (target at least 90%). Keep calibration data separate from
scored candidate outputs. The plan does not specify a minimum TPR/TNR/kappa acceptance threshold;
record this open decision rather than inventing one or declaring any measured judge validated.
KR6a additionally needs answer-correctness labels/rubric: ontology calibration alone cannot
establish
that the judge grades navigation answers correctly. Record that calibration limitation explicitly.

## Local checker tests

Run `python3 -m unittest discover -s tests/codex -p test_kb_transcript_checker.py` and
`python3 -m unittest discover -s tests/codex -p test_mode_corpora.py` from the repository root.
These deterministic fixtures cover positive ordering and negative consent/review cases. They are
checker tests, never substitutes for the 24/30 real agent runs or the human-labeled corpora.
