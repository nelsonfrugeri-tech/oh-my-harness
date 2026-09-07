# Agent Engineering

Use an agent only for model-directed tool selection or adaptive control flow.

1. Define finite state, ownership, transitions, completion, timeout, cancellation, and recovery.
2. Give tools narrow typed schemas, least authority, timeouts, stable errors, and effect classes.
3. Validate arguments before execution and outputs before reuse; treat all content as untrusted.
4. Bind required human approval to the resolved action, target, parameters, and expiry.
5. Reconcile ambiguous outcomes before retrying; bound loops, calls, spend, and wall time.
6. Test invalid arguments, missing tools, partial effects, duplicates, stale memory, injection,
   denied approval, resume, and rollback.

Compose langchain-skills:ecosystem-primer first for LangChain, LangGraph, or Deep Agents, followed only
by its focused selection. If unavailable with official docs, deliver framework-neutral state, tool,
authority, recovery, and test contracts without guessing syntax.
