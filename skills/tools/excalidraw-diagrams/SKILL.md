---
version: 1.0.0
name: excalidraw-diagrams
description: >
  Use when analyzing code, documentation, or concepts and turning the evidence into an Excalidraw
  architecture diagram, C4 view, deployment view, sequence diagram, data flow, flowchart, state
  machine, dependency map, or mind map through an abstract diagram canvas.
type: workflow
---

# Excalidraw diagrams

## Overview

Turn evidence into an editable visual explanation. Treat the model of the system as the source of
meaning and the Excalidraw canvas as a rendering surface. Resolve canvas operations through the
abstract `diagram-canvas` capability in the active harness.

Use this skill for repository architecture, runtime flows, design proposals, incident explanations,
onboarding maps, and exploratory mind maps. Do not use it when a two-line ASCII sketch communicates
the point more clearly or when no configured canvas provider is available.

## Workflow

### 1. Frame one question

Write the question the diagram must answer and identify its audience. Keep each view focused. For a
large system, plan an overview and separate drill-down views.

### 2. Gather evidence

Read entry points, public contracts, composition roots, configuration, schemas, and tests before
implementation detail. Record each observed node and edge with `file:line`. Separate facts,
inferences, and proposed design.

For code-derived diagrams, model runtime or ownership relationships rather than every import. Use
the code graph capability when configured, but verify decisive relationships in source.

### 3. Build a semantic model

Define stable IDs, labels, kind, responsibility, boundary, and evidence for every node. Define edge
direction, protocol or event, synchronization mode, and evidence for every relationship. Reject
orphan nodes and unlabeled non-obvious edges.

Keep architecture views near 6–15 nodes and detailed flows near 10–25 nodes. Split the view when the
limit would hide important labels or create crossings.

### 4. Select the visual grammar

| Need | Diagram | Primary encoding |
| --- | --- | --- |
| System boundaries and responsibilities | C4 context/container/component | Nested boundaries and directed dependencies |
| Runtime collaboration | Sequence | Time from top to bottom; participants left to right |
| Transformation and movement | Data flow | Inputs, processes, stores, outputs |
| Decisions and procedures | Flowchart | Explicit conditions and terminal states |
| Lifecycle behavior | State machine | States, triggers, guards, terminal states |
| Infrastructure placement | Deployment | Runtime nodes, zones, networks, replicas |
| Change impact | Dependency map | Directional dependencies grouped by domain |
| Exploration and taxonomy | Mind map | Radial hierarchy with short branch labels |

Use semantic color by responsibility, not decoration. Use consistent shapes and edge styles, high
contrast, short labels, and a legend only when the notation is not self-evident.

### 5. Plan layout before rendering

Choose a reading direction, tiers, boundaries, and a coordinate grid. Put the dominant flow on the
straightest route. Keep arrows orthogonal when possible, avoid crossings, and place edge labels near
the middle without covering lines.

### 6. Render incrementally

Read the provider's format guide once when available. Create boundaries and primary nodes first,
then edges, labels, notes, and secondary context. Preserve element IDs across revisions. Use
provider checkpoints or snapshots before broad edits when available.

### 7. Inspect and correct

Use scene reads and screenshots when the provider supports them. Check:

- every modeled node and edge appears exactly once;
- arrow direction and labels match the evidence;
- text fits and remains readable at the overview scale;
- boundaries do not obscure content;
- shapes and labels do not overlap;
- contrast and color meaning are consistent;
- the title states the question and scope.

Correct the specific elements, then inspect again. If the provider cannot return a rendered view,
report that visual validation is degraded instead of claiming success.

### 8. Deliver safely

Explain the diagram's scope, evidence, inferences, and unresolved ambiguity. Keep the canvas private
by default. Ask for explicit approval before publishing, sharing, or uploading. Write an editable
artifact into a repository only when the user requests it as version-controlled product
documentation.

## Examples

- "Read the checkout service and draw a C4 container view with evidence."
- "Show the order-created event path as a sequence diagram."
- "Map the authentication state machine and identify missing transitions."
- "Create a mind map of this design proposal and its trade-offs."
- "Compare the current and proposed deployment as two focused views."

## Provider degradation

If `diagram-canvas` is missing, return the evidence-backed semantic model and state that rendering is
pending. If the provider can create but not inspect, render and disclose the missing visual quality
gate. If it cannot export editable files, do not substitute an opaque image without telling the
user.
