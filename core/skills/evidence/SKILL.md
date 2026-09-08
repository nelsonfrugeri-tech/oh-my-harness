---
name: evidence
description: >-
  Establishes status, provenance, uncertainty, conflicts, and decision consequences for material
  claims. Use for factual or quantitative claims, diagnosis, causal reasoning, trade-offs, and
  decisions. Apply as the primary reasoning contract; route missing external or current evidence to
  research, and leave final representation to didactic-visual.
metadata:
  type: capability
  version: 2.0.0
  origin: native
  last_verified: 2026-09-06
---

# Evidence

Make every material claim supportable at the scope in which it will be used, while keeping routine
answers free of ceremonial labels and unnecessary retrieval.

## Own this boundary

Evidence owns claim status, quantitative provenance, uncertainty, conflict handling, material
decisions, and the response contract. It does not acquire missing external evidence or choose the
final presentation format.

Apply it whenever claim status could change what the reader does. In a homogeneous passage of
directly supported facts, state the shared support once and write naturally. Add explicit status
labels at mixed-certainty boundaries, for material decisions, and wherever omission could make an
inference look observed.

## Resolve the evidence source

| Claim condition | Required action |
| --- | --- |
| Stable and low risk | Model knowledge may be sufficient; retrieve only if verification could change the answer. |
| Stable and high impact | Verify against an authoritative primary source before relying on it. |
| Volatile or current | Use `research` to retrieve live official or otherwise primary evidence. |
| Private repository fact | Inspect the repository, then use `code-graph` when relationships require it. |
| Curated project knowledge | Use the project knowledge base and preserve its provenance. |
| Prior discussion or episodic fact | Use `session-memory`, then revalidate anything that may have changed. |
| Ambiguous entity | Inspect available context; ask one discriminating question only if ambiguity remains material. |
| Runtime behavior | Probe the relevant runtime at the smallest safe scope; configuration alone is insufficient. |
| Source unavailable | Report the claim as unknown and name the degraded capability; never substitute plausibility. |

For example, resolve “DHH” from local context before researching it. If both David Heinemeier
Hansson and a deployment-health-hypothesis acronym remain plausible and imply different work, ask
one question that distinguishes them.

## Build the claim record

Use the narrowest status the evidence establishes. Load
[claim-taxonomy.md](references/claim-taxonomy.md) when classification or quantitative provenance is
material.

1. Frame the claim's scope, affected population, time window, and decision impact.
2. Inventory verified facts, derived results, inferences, hypotheses, estimates, unknowns, and
   decisions.
3. Inspect the strongest available evidence selected by the source matrix.
4. Narrow or relabel any claim that exceeds the observed revision, environment, population, or
   time window.
5. Preserve conflicting evidence. Reconcile differences in version, scope, method, and authority;
   otherwise report the conflict as unresolved.
6. Stop when every material claim has the authority and freshness its use requires, or is explicitly
   unknown. Never stop or continue because of a source-count quota.

Every material quantity must identify its unit, population or denominator, observation window,
source, and collection or derivation method. Record revision or inspection date and limitations
where relevant. Numeric confidence is valid only when a cited calibration procedure gives it a
defined empirical meaning.

## Make material decisions testable

Load [decision-protocol.md](references/decision-protocol.md) for a choice that can affect production
users, security, privacy, data integrity, significant spend, multiple teams, or a difficult rollback.
Measure a cheap discriminating observation before choosing when it can materially change the
decision. With weak evidence and costly failure, prefer a smaller, observable, reversible step.

Critique the proposal rather than the person: state its strongest case, the best evidenced risk, a
viable alternative, and the observation that would change the recommendation. Keep mitigation
separate from durable correction.

## Output contract

Respond in the user's language; keep established technical terms in English.

Lead with the bounded conclusion. Cite or identify support beside each material claim, including
source, inspection date or revision, derivation method, and limitation when applicable. Label only
certainty boundaries that affect action. State unresolved conflicts and unavailable-source degraded
modes explicitly. A material decision must include the selected action, decisive evidence,
trade-offs, owner, validation, rollback or review condition, and one falsifying result.

Request the `evidence-reviewer` agent, which applies
[review-rubric.md](references/review-rubric.md), for independent review of unsupported claims or
material decisions. Presentation begins only after this contract is complete.
