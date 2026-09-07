# Scoped Threat Model

Load this reference when the security analysis needs a durable artifact.

## Scope and evidence

- System/change, environment, and operation:
- In-scope assets and excluded assets:
- Authorized testing boundary:
- Repository/runtime evidence:
- Current primary sources and inspection dates:
- Assumptions and unknowns:

## Data and trust flow

For each crossing, record actor or workload identity, source trust zone, controlled input, transport,
destination, privilege transition, stored or emitted data, and failure behavior. Include build,
logging, queue, browser/client, and administrative paths when applicable.

## Abuse-path record

| Field | Content |
| --- | --- |
| Asset and impact | Confidentiality, integrity, availability, privacy, or financial effect |
| Attacker preconditions | Reachability, identity, privilege, timing, or dependency compromise |
| Controlled input | Exact data or action controlled |
| Boundary path | Enforcement points crossed |
| Existing control | Location, owner, and what evidence proves |
| Bypass hypothesis | Falsifiable condition that defeats the control |
| Priority basis | Reachability, preconditions, impact, detectability, evidence confidence |
| Negative validation | Authorized fixture, expected denial, audit signal, no partial effect |
| Residual risk | Untested path, accepted impact, owner, reassessment event |

Do not use an arithmetic risk score unless its scale, calibration population, and decision threshold
are established. Qualitative priority must preserve the factors and uncertainty that produced it.

## Control verification

For each material control, distinguish:

- configuration or static evidence;
- executable negative test;
- runtime enforcement observation;
- monitoring/detection signal;
- recovery or containment exercise.

A control can remain planned or unverified. Do not promote it to effective from documentation or
configuration alone.

## Handoff to review

Return domain observations, affected requirement, repository location, evidence, abuse mechanism,
impact, proposed verification, and residual uncertainty. The independent `review` capability owns
finding severity, deduplication, verdict, and the final review template.
