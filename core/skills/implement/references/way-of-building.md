# Way of Building

An opinionated default for concerns the repository leaves undefined: a greenfield project, or an
existing repository with no convention for domain modeling, prompt location, dependency direction,
or similar. Apply it per concern. When the repository defines a convention for that concern, follow
the repository; do not propose this reference as a correction unless the user asks. Name in the
plan every concern that fell back to this reference.

## Principles

Each rule is stated so a reviewer can check it against the diff.

1. **Name the domain.** A business concept crossing a module boundary is a named type with typed
   fields. No `dict[str, str]`, `dict[str, Any]`, or free strings carrying business meaning.
2. **Close closed sets.** A fixed set of categories, states, or tools is an enum or literal type,
   never a string compared by value.
3. **One type per outcome.** Each result a caller must handle differently is its own type, such as
   `NotEnoughMoney`, not a reason string or a status code with a free message.
4. **Values carry their unit.** Money is integer minor units in a value type; format it only at
   serialization or presentation. The same holds for durations, quantities, and identifiers.
5. **Immutable by default.** Domain values are frozen. Behaviour that only reads a value lives on
   that value or beside it in the domain.
6. **One responsibility per module.** Split when a module has two reasons to change. Size is a
   signal to inspect, never the reason to split.
7. **Dependencies point inward.** The domain imports no framework, I/O, or model client. Each
   external system sits behind a port owned by its consumer. A test enforces the direction.
8. **Content is not logic.** Prompts, user-facing messages, and templates live in their own files
   or modules, never inline in business logic or the entry point.
9. **Code decides, the model proposes.** A model may interpret input and choose among tools; it
   never computes amounts, eligibility, or limits. Every side effect passes through one gate that
   deterministic code controls.
10. **Design only the named extension axis.** When the requirement says a set will grow, such as
    tools, providers, or rules, a new member must work without editing the flow. Absent such a
    statement, add no abstraction for hypothetical variation.
11. **Docstrings state the contract** in one or two lines. Remove narration of what the code does.
12. **Done means observed.** A slice is done when it ran in the real runtime at the smallest safe
    scope: the real dependency answered, and the trace or metric is visible in its backend. Offline
    gates passing is necessary, not sufficient. Report the observed result, including a failing
    score.

```python
# Rejected: meaning lives in strings no type checker can see.
return {"status": "error", "reason": "insufficient_balance", "missing": "1500.00"}

# Preferred: the outcome is a type; the amount is a value with a unit.
class NotEnoughMoney(BaseModel, frozen=True):
    missing: Money  # int cents, formatted only when serialized
```

## Stack patterns

Recommendations the plan selects per project; they are not mandates. Resolve current library and
framework APIs from official sources before use.

**Python**

- Domain types as frozen `pydantic.BaseModel` or `dataclass(frozen=True)`; closed sets as
  `Literal` or `enum.Enum`; a money type as `Annotated[int, ...]` with a serializer used only for
  output.
- Ports as `typing.Protocol` in the consuming layer; adapters in their own package.
- Layers such as `domain`, `ai`, one package per external system, and `api` as the composition
  root. Only the composition root wires concrete adapters.

**LLM and agent applications**

- A prompt is a Markdown file next to the module that uses it, loaded by one small helper.
- When tools are an extension axis, use one agent loop over tools discovered from the tool server,
  such as MCP, instead of a classifier routing into fixed flows. Treat an unknown tool as a write.
- Writes pass through a gate, such as middleware or an interrupt, that runs only a plan computed by
  deterministic code and confirmed by the user.
- Enable tracing in the first slice and confirm one real trace in the backend before calling it
  wired.
- Prefer the framework's native construct over hand-rolled orchestration.
- Judge quality on the real scenario or experiment, not on mocks alone.

## Make the standard executable on the first slice

- Configure the formatter, linter, and strict type checker in the project manifest and expose them
  through the repository entry point, such as a Make target, so the PR quality gate discovers and
  runs them.
- Add an architecture test that parses imports, maps each module to a layer, asserts only allowed
  edges, and asserts the domain imports only the standard library plus the chosen validation
  library.
- Optionally add a file-size check whose limit the user chooses. It flags a file for review; it
  does not decide the design.

## Coordination

For the orchestrating agent that plans and delegates this work.

- Before asking the user, check whether the conversation or plan already decided the point. Asking
  again for a settled choice costs a round trip and trust.
- Do small or sequential work directly and consult a specialist for advice. Delegate only
  substantial, independent work, and never start a subagent the task did not call for.
- Name in each delegation brief the framework and stack skills to load, and require loading them
  before any code is written.
- Treat a subagent report as a claim. Verify the files on disk and the behavior in the real runtime
  before reporting.
- Relay subagent results in the user's language.
