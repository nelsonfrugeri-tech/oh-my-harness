---
name: site-report
description: Create or update a dark, mobile-friendly, self-contained HTML report from a repository, subsystem, architecture, or technical topic. Use when the `site` agent must turn a cited deep dive into a navigable visual artifact, preserve it outside the analyzed repository, and verify the rendered result before delivery.
---

# Site Report

Create one offline `index.html` that teaches the analyzed system at two depths: a five-minute surface
and deeper detail behind `<details>` elements.

## Output contract

- Write below `${OMH_SITES_ROOT:-$HOME/projects/sites}` at
  `<project>/<analysis-name>/index.html`; adapters may configure a writable output root.
- Normalize `project` and `analysis-name` to strict slugs matching
  `[a-z0-9]+(?:-[a-z0-9]+)*`. Reject path separators, `..`, absolute paths, empty slugs, and any
  resolved destination that is not a descendant of the resolved output root.
- Derive `project` from the Git root leaf using lowercase kebab-case normalization.
- Keep the analyzed repository read-only; use a private `mktemp -d` workspace for worktrees,
  scratch data, servers, PID files, and images, and clean it on every exit path.
- Produce one self-contained HTML file with no CDN, remote font, image, script, or stylesheet.
- HTML-escape every source-derived string before inserting it into markup; never paste untrusted
  repository text as executable HTML, CSS, SVG, or JavaScript.
- Use pt-BR for report prose unless the user requests another language; preserve code identifiers.
- Cite every factual claim with `file:line` and record the analyzed ref and commit.

Use [assets/skeleton.html](assets/skeleton.html) as the starting point. Read
[references/design-system.md](references/design-system.md) before editing the template.

## Workflow

### 1. Resolve scope and evidence

Confirm the analysis name only when the user did not provide enough information to derive it safely.
Resolve the requested ref without changing the user's working tree. Use the current checkout for a
current-state report; use an isolated `/tmp` worktree for another ref.

Split research into disjoint scopes such as entry/orchestration, domain components, cross-cutting
behavior, data/integrations, persistence, configuration, tests, and recent history. Delegate bounded
read-only scopes concurrently when the active harness supports it; otherwise inspect sequentially.
Reconcile contradictions against source code before writing.

Evidence rules:

- No `file:line`, no factual claim.
- Count before presenting a number as a stat.
- Treat documentation/code divergence as a first-class finding.
- Make absence and ambiguity explicit.
- Label inference as inference.

### 2. Design the information architecture

Preserve this teaching order unless the subject makes a section genuinely irrelevant:

1. Hero with BLUF, analyzed ref, verified stat tiles, and entity-color legend.
2. One inline SVG macro diagram.
3. Component cards with exact parameters and responsibilities.
4. Real execution or data flow.
5. X-by-Y matrices for relationships or coverage.
6. "What you may not know" with strengths and debts.
7. Timeline only when source history supports it.
8. Footer with primary sources, date, and commit.

Assign each domain entity one frozen categorical color from the bundled design system. Never use a
status color as an entity color. Do not invent palette values; the bundled palette is canonical.

### 3. Build from the asset

Copy the skeleton to the output path, then replace every template marker. Preserve its CSS contract
unless the subject requires a missing component. Keep tables inside `.tscroll`, use tabular numerals,
add accessible labels to SVGs, and put fine detail behind specific `<summary>` labels.

### 4. Validate

Before claiming completion:

1. Assert that no `{{...}}` marker or external request remains.
2. Confirm the restrictive bundled Content Security Policy is still present.
3. Serve the site from a loopback-only temporary server on a dynamically allocated port.
4. Render a desktop and mobile screenshot using the active harness's browser/rendering support or a
   discovered local headless browser.
5. Inspect the images for overflow, collisions, clipped text, unreadable contrast, inconsistent
   entity colors, and excessive empty SVG space.
6. Fix and render again until clean.
7. Stop only the server process started for this validation.

If visual rendering is unavailable, do not claim full validation. Deliver the structurally validated
file and state the exact missing check.

## Updating an existing report

Read the existing footer/ref, identify changed source scopes, refresh only affected research, then
rebuild the impacted sections and rerun the complete validation gate. Never preserve a statement
whose cited source no longer supports it.

## Delivery

Report the analyzed `ref@commit`, output path, section count, two or three strongest findings, and any
degraded validation. Exposure is a separate `site-expose` operation and never happens automatically.
