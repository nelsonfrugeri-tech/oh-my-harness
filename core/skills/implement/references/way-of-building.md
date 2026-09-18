# Way of Building

An opinionated default for code the change creates: a greenfield project, or a new module in an
existing repository whose conventions do not cover it. Apply it per concern. When the repository
defines a convention for that concern, follow the repository; do not propose this reference as a
correction unless the user asks. In an existing repository, a missing tool, gate, or layer is the
repository's choice, not an undefined concern: add one only on explicit request. Name in the plan
every concern that fell back to this reference.

## Principles

Each rule is stated so the author can check it against the diff.

1. **Name the domain.** A business concept crossing a module boundary is a named type with typed
   fields. No `dict[str, str]`, `dict[str, Any]`, or free strings carrying business meaning.
2. **Close closed sets.** A fixed set of categories, states, or tools is an enum or literal type,
   never a string compared by value.
3. **One type per outcome.** Each result a caller must handle differently is its own type, such as
   `NotEnoughMoney`, not a reason string or a status code with a free message.
4. **Values carry their unit.** Money uses an exact representation in a value type: integer minor
   units, or `Decimal` when sub-minor precision is required, never float. Format it only at
   serialization or presentation. The same holds for durations, quantities, and identifiers.
5. **Immutable by default.** Domain values are frozen. Behavior that only reads a value lives on
   that value or beside it in the domain.
6. **One responsibility per module.** Split when a module has two reasons to change. Size is a
   signal to inspect, never the reason to split.
7. **Dependencies point inward.** The domain imports no framework, I/O, or model client. An
   external system the change introduces sits behind a port owned by its consumer when the domain
   must not know it or tests must replace it. In a greenfield project, a test enforces the
   direction.
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
13. **Reuse before creating.** Search the repository for code that already does the job, such as a
    type, helper, client, or fixture, before adding a file or symbol. Extend or call it; a new one
    needs a stated reason reuse does not fit. Leave no unused code behind.

```python
# Rejected: meaning lives in strings no type checker can see.
return {"status": "error", "reason": "insufficient_balance", "missing": "1500.00"}

# Preferred: the outcome is a type; the amount is a value with a unit.
class NotEnoughMoney(BaseModel, frozen=True):
    missing: Money  # int cents, formatted only when serialized
```

## Add structure only when it pays

Start with plain functions and values. Add each construct below only when its trigger is observed in
the requirement or the code, and name the trigger in the plan.

| Construct | Use when | Otherwise |
| --- | --- | --- |
| Interface, `Protocol`, or port | A boundary the consumer owns (rule 7), or real variation: two members exist or a named extension axis (rule 10) | Call the concrete code |
| Inheritance | A true is-a relation whose subclasses reuse shared behavior and honor the parent's contract | Compose: hold the collaborator as a field |
| SOLID principle | Its violation has an observed cost: two reasons to change (rule 6), a consumer forced to depend on methods it never calls, or a domain that imports I/O (rule 7) | Do not restructure for the principle alone |
| Design pattern | It solves the problem in front of you, such as a strategy per member of a named axis or an adapter behind a port | Do not name or pre-build a pattern |

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

Greenfield only. In an existing repository, use the gates it already has.

- Configure the formatter, linter, and strict type checker in the project manifest and expose them
  through the repository entry point, such as a Make target, so the PR quality gate discovers and
  runs them.
- Add an architecture test that parses imports, maps each module to a layer, asserts only allowed
  edges, and asserts the domain imports only the standard library plus the chosen validation
  library.
- Optionally add a file-size check whose limit the user chooses. It flags a file for review; it
  does not decide the design.

## Before writing

- Do not ask again about a point the conversation or plan already settled.
- Load the current framework documentation or skill for the stack before writing code against it.
