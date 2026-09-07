# TypeScript project and runtime boundaries

Load only when the package execution model is unclear or the change crosses a failure-prone seam.

## Effective project

| Signal | Establishes | Common trap |
| --- | --- | --- |
| nearest manifest and lockfile | workspace and command context | root command skips package |
| effective `tsconfig` chain | checker and emit assumptions | only root config is read |
| package type/exports/imports | public module contract | extension alone decides runtime mode |
| framework/build config | transforms and server/client graph | compiler output is assumed to run |
| adjacent tests and CI | executable gate and environment | preferred runner replaces project runner |

Determine whether a file is source, generated output, a declaration, build artifact, or fixture
before editing. The workstation runtime does not establish the deployed runtime. Prefer
lockfile-resolved tools plus CI/build configuration, and inspect both declarations and runtime
packages when they differ.

Use package scripts or task-runner targets for the affected workspace. Include a build or runtime
probe for module resolution, transforms, conditional exports, or server/client bundling. Do not
install an absent checker implicitly.

## Runtime seams

Annotations disappear at runtime. Parse and validate network responses, storage values, messages,
environment-derived data, and user input before assigning trusted domain types. Preserve
discriminants through mapping and serialization. In non-strict projects, add local guards without
claiming project-wide soundness.

Trace async work through start, owner, await/return/supervision, rejection or cancellation, cleanup,
and side effects. Confirm whether callback APIs observe promise rejection. Cancellation is
cooperative: downstream work must consume the signal and late results must not commit stale state.

Check imports across compiler resolution, transformed output, package exports, and runtime loader.
Treat client bundles as public; tree shaking is not a security boundary.

Reject one malformed payload, make a new union member fail exhaustiveness, exercise rejection and
cancellation, import through the runtime that matters, and inspect the client build when applicable.
