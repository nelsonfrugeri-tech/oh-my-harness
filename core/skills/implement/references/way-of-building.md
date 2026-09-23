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
15. **Comments state why, and rarely.** Do not fill code with comments. Write one only for
    genuinely complex code, in one line, explaining a non-obvious why. Docstrings only on the public
    API of a library or a published interface, not on every entry point or port, and never on a
    private function. No narration, no history, no restating the code.
16. **Done means observed.** A slice is done when it ran in the real runtime at the smallest safe
    scope: each real dependency the slice uses answered, and, when the slice emits telemetry, the
    trace or metric is visible in its backend. Offline gates passing is necessary, not sufficient. Report the observed result, including a failing
    score.

```python
# Rejected: meaning lives in strings no type checker can see.
return {"status": "error", "reason": "insufficient_balance", "missing": "1500.00"}

# Preferred: the outcome is a type; the amount is a value with a unit.
class NotEnoughMoney(BaseModel, frozen=True):
    missing: Money  # int cents, formatted only when serialized
```

## Organize code by domain

One specification, three owners: the `discoverer` designs it into the plan, the `developer` builds
it and installs its mechanical checks, and the `reviewer` polices it in the diff. It governs every
file the change creates, including eval, harness, and experiment code, which measured as the worst
area of both reference projects: a 302-line report module holding eleven mixed classes, and a
293-line experiment runner holding a 112-line function.

### Structure

- Organize code by domain, in directories: declared layers with a one-way dependency direction. The
  domain imports no framework, no I/O, and no model client.
- Name and scope each bounded context. Modules, classes, methods, and files speak the domain's
  language. A business rule lives in the domain, never in the entry point or an adapter.
- **One file type per directory.** Never mix `.py` with `.md`, or with any other type, in one
  directory. A component keeps its prompt or template in its own asset subdirectory, such as
  `ai/agent/prompts/prompt.md` beside `ai/agent/*.py`, so the asset stays with its component
  without mixing types in one listing.
- Integration between contexts crosses an explicit port: a `Protocol` owned by the consumer.

### Choose the form: class, function, or data type

| Kind of code | Form | Per module | Why |
| --- | --- | --- | --- |
| Domain data: entity, value object, result type | Frozen model or dataclass, no behavior beyond reading its own data | Many, unlimited | The module reads as the domain's vocabulary |
| Business rule | Module-level function, private helpers beside it | One public function | No state, directly testable, no lifecycle |
| State with identity or a lifecycle, such as a middleware, gate, or session | Class with at most three public methods | One | The state justifies the object |
| Adapter to an external system | Class implementing a declared `Protocol` | One | It mirrors the external contract; exempt from the public-method cap |
| Orchestration facade | Function | One public | Composition, not an object |

No state: a function. Data: an immutable type. A lifecycle: one class with one responsibility. A
stateless class with public methods is a function in disguise.

Measured in the reference project: `domain/planning.py` has no class at all and holds the rule as
module functions, `propose` public beside the private `_propose_for` and `_calculate`;
`domain/proposal.py` holds ten frozen data classes and no behavior; `ai/agent/gate.py` is a
stateful middleware class.

### Size

- Target about 100 lines per file; up to about 130 is fine when the file is cohesive, as in the
  136-line `domain/planning.py` that holds one rule plus its private helpers.
- **Over 150 lines: a mandatory deep re-evaluation, not a block.** The developer writes in the pull
  request description the module's single responsibility and either the split applied or why
  splitting would spread one rule across files; the reviewer checks that analysis.
- **A function over 50 lines is a hard limit.**
- **A class with behavior exposes at most three public methods, a hard limit**, exempting an adapter
  that implements a declared `Protocol`.
- A module that becomes a large vocabulary, such as ten result types in 126 lines, splits by family
  into a package that re-exports them.

The file-size numbers never become a failing gate: size is a signal to inspect, and responsibility
is the reason to split. Only the function-length and public-method caps are enforced by a check.

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

- Every line the change adds is covered by a test that exercises its behavior. Be critical of each
  test: it must fail when the behavior breaks. Never write a test only to raise coverage, such as
  one that asserts a mock was called, restates a constant, or tests the framework.
- Mock as little as possible. Run real dependencies, such as databases, queues, and HTTP services,
  in a disposable container, for example with Testcontainers; fake only what cannot run locally.
- Always look for a way to test. What still cannot be tested is declared at the end with the reason
  and the cheapest way to test it later.
- Test at the public seam of each layer with the lowest level that exposes the risk:
  - domain: pure, table-driven unit tests, one per rule and per outcome type, covering every
    branch;
  - orchestration: hand-written fakes for the ports that record calls, no deep mock chains,
    covering the happy path, every refusal, a failure midway, retries, and concurrency;
  - adapters: the real dependency in a disposable container when it can run locally; otherwise
    recorded real payloads, captured read-only, plus one opt-in live test;
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

- A prompt is a Markdown file in the component's own asset subdirectory, such as
  `ai/agent/prompts/prompt.md` beside `ai/agent/*.py`, loaded once as a module constant by one small
  helper. One file type per directory still holds.
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
- Add the function-length cap and the public-method cap of "Organize code by domain" as checks
  through the same entry point, with the `Protocol` exemption for adapters.
- Optionally add a file-size check whose limit the user chooses. It flags a file for review; it
  does not decide the design.

## Before writing

- Do not ask again about a point the conversation or plan already settled.
- Load the current framework documentation or skill for the stack before writing code against it.

## Deliver

- Update the README in the same change as any interface or command change, and run every command
  the change added or altered, after inspecting its effects per `implement`.
- Keep temporary scripts, reports, and scratch files out of the repository.
- Report what ran, where, the result, and what was not verified.
