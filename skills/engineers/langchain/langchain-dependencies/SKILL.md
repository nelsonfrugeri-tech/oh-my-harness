---
version: 2.0.0
upstream_source: https://github.com/langchain-ai/langchain-skills
upstream_version: 92e4f3b494c02d8927f85ab3b8d97417b445b6ee
adaptation_status: local-adaptation
name: langchain-dependencies
description: |
  Dependency selection and reproducible versioning for Python and TypeScript projects that
  use LangChain, LangGraph, LangSmith, or Deep Agents. Use for new environments, upgrades,
  compatibility diagnosis, lockfile maintenance, and security-aware package selection.
type: knowledge
---

# LangChain Dependency Management

The ecosystem is split across independently released core, orchestration, provider, and
integration packages. Never infer a compatible set from memory and never persist a floating
dependency specification.

## Required workflow

1. Identify the runtime, package manager, selected orchestration layer, model providers, and
   integrations actually used by the project.
2. Inspect the existing manifest and lockfile before proposing changes.
3. Resolve current stable, non-prerelease releases from official package registries and the
   projects' official compatibility documentation through the `web` capability.
4. Review upstream release notes and current security advisories for every direct dependency.
5. Select one mutually compatible set and record every direct dependency as an exact version.
6. Generate or refresh the package-manager lockfile so transitive dependencies are reproducible.
7. Install from the lockfile in a clean environment, then run format, lint, typecheck, tests,
   and the project's dependency audit.

If live registry or advisory access is unavailable, stop before choosing versions. Report the
unresolved package set instead of substituting remembered or floating versions.

## Framework choice

Choose one orchestration layer unless the architecture explicitly combines them:

| Layer | Use when | Direct package |
| --- | --- | --- |
| LangChain | General tool-using agents and retrieval | `langchain` |
| LangGraph | Explicit state graphs, branching, persistence, or interrupts | `langgraph` / `@langchain/langgraph` |
| Deep Agents | Planning, filesystem context, skills, and subagent delegation | `deepagents` |

Provider and integration packages remain explicit direct dependencies. For example, an OpenAI
agent using Qdrant normally declares its core layer plus `langchain-openai` and
`langchain-qdrant`; unused providers should not be installed.

## Python contract

- Use a supported Python version confirmed by the selected package releases.
- Pin each direct dependency with `==` in the input manifest.
- Commit a generated lockfile with hashes when the selected tool supports them.
- Install CI and production environments from that lockfile, not by resolving again.
- Prefer dedicated integration packages over broad community bundles.

The following is a template. Replace every placeholder with a version resolved during the
required workflow before saving it as a project file:

```text
langchain==<resolved-version>
langchain-core==<resolved-version>
langsmith==<resolved-version>
langgraph==<resolved-version>
langchain-openai==<resolved-version>
langchain-qdrant==<resolved-version>
```

For Deep Agents, replace the orchestration line rather than blindly adding another layer:

```text
deepagents==<resolved-version>
langchain==<resolved-version>
langchain-core==<resolved-version>
langsmith==<resolved-version>
```

Supported reproducibility patterns include:

```bash
# uv
uv lock
uv sync --frozen

# pip-tools
pip-compile --generate-hashes requirements.in
pip-sync requirements.txt
```

Use the project's existing package manager. Do not introduce a second locking tool without an
explicit migration decision.

## TypeScript contract

- Confirm the Node.js runtime supported by all selected releases.
- Save every direct dependency as an exact version with no range operator.
- Commit the lockfile produced by npm, pnpm, yarn, or Bun.
- Use the package manager's frozen/immutable install mode in CI.
- Declare peer dependencies such as `@langchain/core` explicitly when the package graph needs
  them, especially in workspaces.

Template only; resolve every placeholder first:

```json
{
  "dependencies": {
    "@langchain/core": "<resolved-version>",
    "@langchain/langgraph": "<resolved-version>",
    "@langchain/openai": "<resolved-version>",
    "langchain": "<resolved-version>",
    "langsmith": "<resolved-version>"
  }
}
```

Example commands after versions have been selected:

```bash
npm install --save-exact \
  langchain@<resolved-version> \
  @langchain/core@<resolved-version> \
  @langchain/langgraph@<resolved-version> \
  langsmith@<resolved-version>
npm ci
```

## Upgrade strategy

Treat an upgrade as a controlled compatibility change:

1. Read the release notes between the locked and candidate versions.
2. Check Python/Node support, peer constraints, and provider compatibility.
3. Resolve and lock the candidate graph on a dedicated branch.
4. Run the dependency audit and all project quality gates.
5. Exercise agent construction, one tool call, structured output, persistence, and tracing in
   the combinations the product actually uses.
6. Keep the previous lockfile in version control so rollback is a normal revert.

Do not widen constraints to make a resolver succeed. Diagnose the conflicting package and
choose a compatible exact set. Do not update unrelated dependencies in the same change unless
the resolver proves they are part of the compatibility boundary.

## Security and provenance

- Prefer official registry artifacts and verify package ownership when adding a new integration.
- Review security advisories from the official ecosystem and the project's configured scanner.
- Treat unexpected package-name variants as potential dependency confusion.
- Never place provider credentials in manifests, lockfiles, command history, or examples.
- Record why a vulnerable release is temporarily retained and define an expiry or follow-up.

## Common failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Import or schema mismatch | Core and integration packages resolved independently | Re-resolve a documented compatible exact set |
| Duplicate core types in a workspace | Missing or incompatible peer dependency | Inspect the dependency tree and align exact peer versions |
| Works locally but fails in CI | CI resolved a different graph | Enforce frozen lockfile installation |
| Upgrade changes tool schemas | Integration package changed behavior | Review release notes and add a regression test |
| Resolver succeeds only with broad ranges | Hidden incompatibility or stale lock state | Identify the conflict; do not persist the broad range |

The output of this skill is a reviewed set of exact direct pins, a committed lockfile, evidence
that security advisories were checked, and passing project quality gates.
