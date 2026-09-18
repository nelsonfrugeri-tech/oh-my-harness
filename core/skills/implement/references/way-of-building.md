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
   fields. No `dict[str, str]`, `dict[str, Any]`, or free strings carrying business meaning. A raw
   map exists only at the edge, such as incoming JSON or external tool arguments, and is parsed
   into a named type immediately.
2. **Close closed sets.** A fixed set of categories, states, or tools is an enum or literal type,
   never a string compared by value.
3. **One type per outcome.** Each result a caller must handle differently is its own type, such as
   `NotEnoughMoney`, not a reason string or a status code with a free message. Exceptions are for
   exceptional or infrastructure failures, such as a network error; an expected business outcome
   is a typed result.
4. **Values carry their unit.** Money uses an exact representation in a value type: integer minor
   units, or `Decimal` when sub-minor precision is required, never float. Format it in exactly one
   place, at serialization or presentation. The same holds for durations, quantities, and
   identifiers.
5. **Immutable by default.** Domain values are frozen. Behavior that only reads a value lives on
   that value or beside it in the domain; a rule across concepts is a pure function in a module
   named for the rule.
6. **Make derived numbers and absence explicit.** A computed result exposes every intermediate
   value, such as a `Calculation` with `total`, `already_paid`, and `missing`, so people, tests, and
   models can read it. Absence is an explicit optional type, and defaults are decided in one
   function, not in scattered fallbacks.
7. **One responsibility per module.** Split when a module has two reasons to change. Prefer small
   files; size is a signal to inspect, never the reason to split.
8. **Dependencies point inward.** The domain imports no framework, I/O, or model client, and never
   reads the clock or the environment. An external system the change introduces sits behind a port
   owned by its consumer when the domain must not know it or tests must replace it. In a greenfield
   project, a test enforces the direction.
9. **Content is not logic.** Prompts, user-facing messages, and templates live in their own files
   or modules, never inline in business logic or the entry point, and load once.
10. **Pure core, effects at the edge.** A model may interpret input and choose among tools; it never
    computes amounts, eligibility, or limits. Every side effect passes through one named gate that
    deterministic code controls. An irreversible action needs a precondition code can check, such
    as a confirmed plan or an idempotency key, never the model's judgment alone.
11. **Design concurrency and retries.** State what runs once, what may repeat, and what is locked,
    and test each.
12. **Design only the named extension axis.** When the requirement says a set will grow, such as
    tools, providers, or rules, a new member must work without editing the flow. Absent such a
    statement, add no abstraction for hypothetical variation.
13. **Reuse before creating.** Search the repository for code that already does the job, such as a
    type, helper, client, or fixture, before adding a file or symbol. Extend or call it; a new one
    needs a stated reason reuse does not fit.
14. **Read top to bottom.** Guard clauses first and the happy path last, with no deep nesting.
    Names say what a thing is in the business language: no `utils`, `helpers`, or `manager`
    modules. No dead code, speculative parameters, or just-in-case branches.
15. **Comments state why.** None by default; one line for a non-obvious constraint or rule.
    Docstrings on public entry points and ports state the contract in one or two lines. Never
    narrate what the code does or how it came to be.
16. **Done means observed.** A slice is done when it ran in the real runtime at the smallest safe
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

## Add structure only when it pays

Start with plain functions and values. Add each construct below only when its trigger is observed in
the requirement or the code, and name the trigger in the plan.

| Construct | Use when | Otherwise |
| --- | --- | --- |
| Class | It holds state or several operations on the same data | A plain function, not a class with one method and no state |
| Validated model | Data crosses a boundary or needs validation or serialization | A lightweight frozen record for internal bundles, such as `Context(bank, clock)` |
| Raw map | Only at the edge: raw payloads, external tool arguments, argument forwarding | A named type (rule 1) |
| Variadic keyword arguments | Transparent wrappers, decorators, and framework hooks | Explicit parameters; never on a public function |
| Named or keyword-only parameters | Two or more parameters of the same type, or easily swapped | No positional booleans |
| Interface, `Protocol`, or port | A boundary the consumer owns (rule 8), or real variation: two members exist or a named extension axis (rule 12) | Call the concrete code |
| Inheritance | Plugging into a framework extension point, or a true is-a subtype that honors the parent's contract | Compose: hold the collaborator as a field |
| SOLID principle | Its violation has an observed cost: two reasons to change (rule 7), a consumer forced to depend on methods it never calls, or a domain that imports I/O (rule 8) | Do not restructure for the principle alone |
| Design pattern | It solves the problem in front of you, such as a gate as middleware, an adapter behind a port, or a small factory like `Step.pay(bill, amount)` | No generic repositories, service locators, or abstract bases "for later" |

## Test every behavior

- Test at the public seam of each layer with the lowest level that exposes the risk:
  - domain: pure, table-driven unit tests, one per rule and per outcome type, covering every
    branch;
  - orchestration: hand-written fakes for the ports that record calls, no deep mock chains,
    covering the happy path, every refusal, a failure midway, retries, and concurrency;
  - adapters: recorded real payloads, captured read-only, plus one opt-in live test;
  - entry point: every response path, including error mapping.
- Derive expected values from the spec or the dataset, never by copying what the code returns.
- One behavior per test, named as a sentence.
- Prove each test can fail: break the rule once and watch it go red.

## Stack patterns

Recommendations the plan selects per project; they are not mandates. Resolve current library and
framework APIs from official sources before use.

**Python**

- Domain and boundary types as frozen `pydantic.BaseModel`; internal bundles such as a
  dependency context as `dataclass(frozen=True)`; closed sets as `Literal` or `enum.Enum`; a money
  type as `Annotated[int, ...]` with a serializer used only for output.
- Parse a `dict` into a model at the edge; `**kwargs` only in wrappers, decorators, and framework
  hooks; keyword-only parameters (`*, a, b`) for same-typed arguments.
- Ports as `typing.Protocol` in the consuming layer; adapters in their own package.
- Layers such as `domain`, `ai`, one package per external system, and `api` as the composition
  root. Only the composition root wires concrete adapters.
- Table-driven tests with `pytest.mark.parametrize`; branch coverage with `pytest-cov`
  (`--cov-branch --cov-fail-under=<agreed>`).

**LLM and agent applications**

- A prompt is a Markdown file next to the module that uses it, loaded once as a module constant by
  one small helper.
- When tools are an extension axis, use one agent loop over tools discovered from the tool server,
  such as MCP, instead of a classifier routing into fixed flows. Treat an unknown tool as a write.
- Writes pass through a gate, such as middleware or an interrupt, that runs only a plan computed by
  deterministic code and confirmed by the user.
- Give the model results that code already computed and typed.
- Enable tracing in the first slice and confirm one real trace in the backend before calling it
  wired.
- Prefer the framework's native construct, verified against the installed version, over
  hand-rolled orchestration.
- Judge quality on the real scenario or experiment, not on mocks alone.

## Make the standard executable on the first slice

Greenfield only. In an existing repository, use the gates it already has.

- Configure the formatter, linter, strict type checker, and branch coverage with a fail-under
  threshold the user agrees to, and expose them through one repository entry point, such as a
  Make target, so the PR quality gate discovers and runs them.
- Add an architecture test that parses imports, maps each module to a layer, asserts only allowed
  edges, and asserts the domain imports only the standard library plus the chosen validation
  library.
- Optionally add a file-size check whose limit the user chooses. It flags a file for review; it
  does not decide the design.

## Before writing

- Do not ask again about a point the conversation or plan already settled.
- Load the current framework documentation or skill for the stack before writing code against it.

## Deliver

- Update the README in the same change as any interface or command change, and run every command
  it shows.
- Keep temporary scripts, reports, and scratch files out of the repository.
- Report what ran, where, the result, and what was not verified.
