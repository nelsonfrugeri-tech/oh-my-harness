---
name: frontend-ui
description: >-
  Implement or verify user-facing web UI when interaction states, keyboard/focus behavior,
  semantics, accessibility, responsive layout, or visual coherence affect the result. Use for
  concrete frontend surfaces; do not load for backend-only work, generic visual-trend questions,
  or tasks with no rendered or interactive user interface.
metadata:
  origin: native
  last_verified: 2026-09-07
---

# Frontend UI engineering

Deliver a coherent interface whose interaction and layout behavior is verified in the target
project, not inferred from visual polish or static markup.

## Discover the product surface

Inspect the existing UI before choosing components or styles. Establish product intent and journeys,
design tokens and reusable primitives, rendering boundaries, browser/device targets, localization
constraints, generated artifacts, and available accessibility/visual tools. Reuse project
conventions unless the request changes the system. Do not introduce a fashionable stack, color
model, spacing scale, font, or animation library by default.

Read [interaction and responsive verification](references/interaction-verification.md) when changing
controls, transient UI, dynamic states, or layout behavior.

## Specify states before styling

Identify applicable initial, hover, focus, active, selected, disabled, loading, empty, success,
validation-error, operational-error, partial-data, and retry states. Define what the user perceives
and can do in each state; preserve input and recovery paths when possible.

- Prefer native elements and project primitives. Custom controls must reproduce keyboard, focus,
  name, role, value, and state behavior, not only appearance.
- Keep focus visible and logical; closing transient UI restores focus to a valid origin or successor.
- Make dynamic status and errors perceivable without stealing focus unnecessarily.
- Verify narrow, intermediate, and wide available widths with long and zoomed content. Derive
  breakpoints from observed content failure, not device names.
- Keep client code free of secrets and server-only capabilities.
- Respect reduced-motion and other user/project preferences without removing essential state cues.

## Verify and report

Use existing browser, component, accessibility, and screenshot tools. Automated checks do not prove
usability or complete accessibility: exercise keyboard input, inspect focus and accessible
names/states, and resize across the supported range. Screenshots follow behavior and semantics.

Retrieve current primary documentation when a decision depends on a browser feature, framework API,
performance metric, or accessibility standard. Record target version/standard, source, and inspection
date. Do not retain numeric thresholds or current metric names here unless they are project policy.

Report states covered, primitives reused, interaction/accessibility observations, viewport/content
conditions, commands, and remaining manual or assistive-technology gaps. Stop at the requested
surface rather than redesigning unrelated screens.
