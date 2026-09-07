---
name: security
description: >-
  Build or challenge a scoped application-security threat model by tracing assets, actors, trust
  boundaries, abuse paths, controls, negative tests, and residual risk. Use for security design,
  authn/authz boundaries, untrusted input, secrets, supply chain, SSRF, or incident remediation.
  Do not use merely for a generic OWASP explanation or to replace an independent code review.
metadata:
  origin: native
  last_verified: 2026-09-07
---

# Scoped Threat Modeling

Turn a concrete system change or exposure into testable abuse paths and controls without assuming
that authentication, validation, or a scanner makes the system secure.

## Guard the boundary

- Establish the system, operation, data, environment, and attacker capability in scope. If scope is
  materially ambiguous, inspect local evidence and ask one discriminating question.
- Route structural trade-offs to `design` and consumer-visible auth/error behavior to `api-design`.
- Supply security observations and evidence to `review`; do not duplicate its severity taxonomy,
  finding format, or merge recommendation.
- Do not provide exploit steps against systems without authorization. Use local fixtures or a
  clearly authorized target for dynamic checks.
- Do not read suspected secrets to verify them. Report location and rotate/revoke through the
  authorized operational process.

## Resolve evidence and freshness

Inspect code, data flows, deployment configuration, identities, policies, dependency locks, CI
workflows, tests, and runtime observations. Configuration proves intent, not enforcement.

Use `research` with current primary sources for standards, vulnerability records, cloud metadata
behavior, OAuth/OIDC, cryptography, framework security defaults, scanners, actions, and dependency
syntax. Record source, revision or inspection date, applicability, and limitation. Never copy a
current algorithm, parameter, action tag, image tag, or scanner command from memory.

If authoritative evidence or the required environment is unavailable, mark the control or test
unverified and preserve the risk. Do not substitute a weaker check silently.

## Build the threat model

1. **Define impact.** Identify assets, sensitive operations, availability obligations, privacy or
   integrity consequences, and who owns the risk.
2. **Map exposure.** Trace actors, identities, entry points, interpreters, data stores, external
   services, privileges, and trust-boundary crossings. Include logs, queues, build inputs, and client
   bundles where relevant.
3. **Construct abuse paths.** State attacker preconditions, controlled input, path across boundaries,
   target asset, observable impact, and existing control. Use taxonomies such as STRIDE or OWASP only
   as coverage prompts after tracing the actual flow.
4. **Prioritize with evidence.** Compare reachability, required privilege, exploit preconditions,
   impact, detectability, and evidence confidence. Do not invent likelihood or collapse incomparable
   factors into an unsupported score.
5. **Place controls.** Map prevention, detection, containment, and recovery to an explicit
   enforcement point and owner. Prefer allowlists, parameterization, least privilege, bounded
   resources, immutable provenance, and fail-closed behavior where the business failure mode allows.
6. **Test negatively.** Attempt the abuse condition in an authorized fixture; verify denial,
   absence of partial effects or secret leakage, and a useful audit signal. A scanner finding or
   passing configuration check is not runtime proof.
7. **Record residual risk.** State untested paths, bypass assumptions, operational dependencies,
   accepted impact, decision owner, and the event that triggers reassessment.

Use [threat-model.md](references/threat-model.md) for a durable artifact.

## High-risk boundary checks

### Object authorization

Authentication establishes identity, not permission on an object. Test a valid principal performing
the same action against another tenant or owner's object, including indirect identifiers and batch
operations. Enforce policy at the data access or authoritative operation boundary, not only in UI or
route presence.

### Injection and interpretation

Trace where untrusted bytes become SQL, shell, template, path, query language, expression, markup,
or generated code. Prefer structured APIs and parameter binding. Validate both the intended grammar
and the downstream interpreter. Escaping for one context does not make data safe in another.

### Secrets and supply chain

Check source, history, logs, traces, build output, client bundles, caches, and error responses without
printing secret values. Treat exposure as an incident requiring revocation or rotation, not merely
deletion.

Resolve action and dependency revisions from current official sources. Pin executable CI actions and
images to immutable revisions or digests, keep the human-readable release in update metadata, and
use a reviewed update mechanism. Never use mutable `@main`, `@master`, or `latest` as an
execution trust anchor.

### A10 — Server-Side Request Forgery (SSRF)

Do not copy a hand-written hostname validator into production; URL validation alone is not an SSRF
boundary. Use a maintained outbound-request policy and verify all of these controls together:

1. Parse with a standards-compliant URL parser, allow only required schemes, reject credentials and
   ambiguous host encodings, and constrain destination ports.
2. Resolve every A and AAAA record before connecting. Reject the destination if any address is
   unspecified, loopback, private, link-local, multicast, reserved, or in a cloud metadata range;
   include IPv4-mapped IPv6 representations.
3. Prevent DNS rebinding by pinning the validated resolution to the connection and perform a
   post-connect peer-address check.
4. Disable redirects by default. If redirects are required, apply the complete parse, DNS, address,
   and post-connect validation to every hop and cap the redirect count.
5. Enforce egress proxy or firewall rules that deny internal networks and metadata services even if
   application validation fails.
6. Test direct IPs, alternate numeric encodings, mixed A/AAAA answers, DNS rebinding, redirects to
   private/link-local targets, and metadata endpoints. Fail closed on resolution or validation
   errors.

Redirect policy: DENY_BY_DEFAULT — redirects remain disabled unless every hop repeats the full
validation policy and the client enforces a finite hop limit.
Address policy: DENY — reject private, link-local, loopback, reserved, multicast, unspecified, and
cloud metadata destinations for every resolved address and connected peer.
DNS policy: PIN_AND_RECHECK — bind the validated resolution to the connection and fail closed when
the connected peer is outside the validated address set.
Egress policy: DENY_INTERNAL — enforce a separate network boundary for internal and metadata ranges.
Source: [OWASP Server-Side Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
as_of: 2026-09-06
Post-connect evidence: INFERENCE — OWASP establishes DNS-pinning and redirect risks, but does not
prescribe the exact post-connect peer check. Resolution pinning and peer verification are
defense-in-depth controls inferred to close the validation-to-connect time-of-check/time-of-use gap.
Refresh trigger: revalidate when OWASP guidance, HTTP client redirect behavior, DNS resolution, or
cloud metadata boundaries change.

### Incident pressure

Do not run destructive containment or remediation from a generic recommendation. Resolve the exact
owned scope, inspect current state, preview effects where possible, preserve evidence, define
recovery, and obtain authorization required by the active environment. Prefer reversible isolation,
credential revocation, or traffic controls when they reduce exposure without destroying evidence.
If the destructive target is broad or unresolved, refuse that action and report the safe next step.

## Produce and verify

Report scope, assets, trust boundaries, prioritized abuse paths, controls with enforcement points,
negative tests and their exact outcomes, residual risks, assumptions, unknowns, and source
provenance. Do not claim “secure” or absence of vulnerabilities.

Before stopping, verify that every high-impact abuse path has a control, a negative check or explicit
untested status, recovery ownership, and a reassessment event. Stop when the next risk decision is
actionable; do not append a generic OWASP checklist.

Refresh this skill when package evals fail or when relevant standards, advisories, dependencies,
platform defaults, cloud metadata behavior, or threat assumptions change.
