# Python project and boundary checks

Load only when project signals conflict or the change crosses a failure-prone seam.

## Project signals

| Question | Inspect first | Confirm with |
| --- | --- | --- |
| Language level | project metadata, lockfile, runtime files | CI and deployment config |
| Package/import model | source tree and build metadata | installed invocation and tests |
| Dependency workflow | lockfile and project scripts | CI install command |
| Quality gates | task runner and tool config | CI jobs |
| Local convention | adjacent implementation | adjacent tests and generated markers |

A workstation interpreter proves execution capacity, not project compatibility. When signals
conflict, prefer the path exercised by CI or the declared deployment runtime unless the task changes
it. A test passing because the repository root is on the import path does not prove installation.

Before editing a suspicious file, inspect headers, build scripts, schema sources, and ignore rules
for generation evidence. Change the authoritative source when owned and in scope; otherwise report
the regeneration path. Do not install an absent checker implicitly.

## Type, async, resource, and error behavior

Annotations describe values to a checker; parsing converts representation; validation rejects values
outside the runtime contract. Establish each behavior required at an untrusted seam before creating
a trusted domain type. A cast is justified only by an observable invariant the checker cannot express.

Trace async work through ownership, completion, cancellation/error propagation, cleanup, and observed
result. Synchronous file, network, subprocess, or sleep calls can block an async scheduler. Detached
tasks need a longer-lived owner that observes failures and shuts them down.

Use a context manager or equivalent `try/finally` when acquisition succeeds before later work can
fail. Resource-owning streams or generators must be consumed inside that lifetime or explicitly
transfer ownership. At exception boundaries, recover, translate with cause, add context and re-raise,
or propagate; logging and swallowing is not recovery.

Exercise an invalid external value, failure after acquisition, cancellation/timeout for changed async
work, and the supported import entry point when applicable. Run the configured checker in the same
mode and path set used by the project.
