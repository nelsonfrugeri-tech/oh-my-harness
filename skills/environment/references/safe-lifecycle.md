# Safe local lifecycle

Use this contract for a local action that can stop work, mutate state, consume substantial resources,
change permissions, or delete data.

## Action record

Before execution, establish:

1. **Exact target:** repository, project namespace, service, process identity, path, volume, or
   resource ID. Reject unresolved variables, broad globs, and machine-wide scope.
2. **Ownership:** evidence that the target belongs to this project and is not shared.
3. **Current state:** bounded status, dependencies, active work, and data classification.
4. **Preview:** a native dry run when trustworthy; otherwise a read-only listing of the exact target
   and expected delta.
5. **Blast radius:** processes, data, ports, and other projects that can be affected.
6. **Recovery:** graceful stop, restart path, backup or snapshot when data is involved, and a tested
   or inspectable restore precondition.
7. **Authorization:** obtain it at the boundary required by the active policy after scope and impact
   are known.

Choose the smallest reversible action. Escalate from graceful stop to stronger termination only
after confirming the same process identity and documenting why the graceful path failed. Omit a
destructive command when target ownership, backup, restore, or authorization is unresolved.

## Completion

Verify the intended state, the representative local journey, and absence of unexpected collateral
changes. Record residual state and cleanup ownership. Temporary resources need an owner, namespace
or label, and an expiry or explicit removal signal.
