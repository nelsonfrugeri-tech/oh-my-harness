---
name: site-report
description: "Create or update a dark, mobile-friendly, self-contained HTML report from cited technical evidence. Store it outside the analyzed repository; never publish it."
---

# Site Report

Create one offline index.html. Resolve configured sites root and require project/analysis slugs to
match `[a-z0-9]+(?:-[a-z0-9]+)*`; reject traversal, absolute inputs, empty segments, and destinations outside root. Keep
analyzed repository read-only and scratch state private/temporary.

Use [assets/skeleton.html](assets/skeleton.html) and [references/design-system.md](references/design-system.md). Allow no external assets/runtime. Escape
source text; never insert it as executable markup/code.

Resolve ref/commit without changing worktree. Cite repository facts with relative file:line, count
quantities, and mark inference, absence, divergence, and unknown health. Configured is not healthy.

Include only supported overview, diagram, contracts, flows, matrices, risks, timeline, and sources.
Preserve bundled tokens/colors and put detail behind descriptive controls.

Validate no markers/external requests, CSP, HTML/anchors, loopback serving, and desktop/mobile render.
Inspect overflow, clipping, collisions, contrast, colors, and diagram space. Stop only owned server
and remove temporary state. Without rendering, report structural-only validation.

Report ref@commit, path, sections, findings, and degraded checks. Exposure is separate site-expose
work requiring fresh authorization for the final artifact.
