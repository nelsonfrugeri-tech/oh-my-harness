# Note template

Generated from `kb.note` schema. Regenerate with `render_reference()`; do not edit by hand.
All narrative text is written in pt-BR. The placeholders below must be replaced before validation.
Required headings keep their relative order. Optional headings may appear anywhere.
Remove unused optional sections and unused conditional tables; do not leave empty sections.
Entities, Dates and Figures are required when the corresponding declarations or facts exist.
Timeline rows require RFC 3339 timestamps and nonempty evidence; Dates and Figures also use
RFC 3339 timestamps. Currency units use ISO 4217. Entity types are the 13 frontmatter keys.

New notes start pending. Only approval publishes them. A domain identity note is a reference at
`<scope>/<domain>/identity/identity.md`; a code project also supplies `repository_path`,
`remote_url` and `default_branch` (`remote_url: null` when unavailable or redacted). Frozen versions add `superseded_at` and
`superseded_reason` (30–500 characters), and use status superseded. Neither set of fields belongs
to the ordinary new-note skeleton. Tags contain 1–6 distinct kebab-case values.

## decision

```markdown
---
id: "<UUID v4>"
type: decision
title: "<10–70 caracteres>"
description: "<120–300 caracteres em pt-BR>"
summary: "<600–1500 caracteres em pt-BR>"
tags: ["<kebab-case>"]
status: pending
version: 1
created_at: "<RFC 3339 UTC>"
updated_at: "<RFC 3339 UTC>"
generated:
  harness: "<claude-code|codex|cursor>"
  model: null
  session_id: "<ID real da sessão>"
  cwd: "<caminho absoluto>"
  machine_id: "<UUID da identidade estável>"
parent: null
related: []
children: []
entities:
  people: []
  companies: []
  products: []
  brands: []
  roles: []
  projects: []
  apps: []
  urls: []
  repos: []
  paths: []
  documents: []
  emails: []
  names: []
---

## Decision

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Context

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Options

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Consequences

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## How to apply

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Drivers

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Confirmation

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Sources

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Entities

<!-- Condicional: inclua quando houver dados correspondentes -->

| Entidade | Tipo | Quem/o que é | Relação | Período | Fonte |
| --- | --- | --- | --- | --- | --- |

## Dates

<!-- Condicional: inclua quando houver dados correspondentes -->

| Data | O que é | Quem | Status | Fonte |
| --- | --- | --- | --- | --- |

## Figures

<!-- Condicional: inclua quando houver dados correspondentes -->

| Valor | Unidade | O que mede | Quando | Fonte |
| --- | --- | --- | --- | --- |
```

## event

```markdown
---
id: "<UUID v4>"
type: event
title: "<10–70 caracteres>"
description: "<120–300 caracteres em pt-BR>"
summary: "<600–1500 caracteres em pt-BR>"
tags: ["<kebab-case>"]
status: pending
version: 1
created_at: "<RFC 3339 UTC>"
updated_at: "<RFC 3339 UTC>"
generated:
  harness: "<claude-code|codex|cursor>"
  model: null
  session_id: "<ID real da sessão>"
  cwd: "<caminho absoluto>"
  machine_id: "<UUID da identidade estável>"
occurred_at: "<RFC 3339 com fuso>"
parent: null
related: []
children: []
entities:
  people: []
  companies: []
  products: []
  brands: []
  roles: []
  projects: []
  apps: []
  urls: []
  repos: []
  paths: []
  documents: []
  emails: []
  names: []
---

## What happened

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Timeline

<!-- Obrigatória -->

| Quando | Quem | O quê | Como | Evidência |
| --- | --- | --- | --- | --- |

## Outcome

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Impact

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Causes

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Resolution

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Lessons

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Follow-ups

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Sources

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Entities

<!-- Condicional: inclua quando houver dados correspondentes -->

| Entidade | Tipo | Quem/o que é | Relação | Período | Fonte |
| --- | --- | --- | --- | --- | --- |

## Dates

<!-- Condicional: inclua quando houver dados correspondentes -->

| Data | O que é | Quem | Status | Fonte |
| --- | --- | --- | --- | --- |

## Figures

<!-- Condicional: inclua quando houver dados correspondentes -->

| Valor | Unidade | O que mede | Quando | Fonte |
| --- | --- | --- | --- | --- |
```

## procedure

```markdown
---
id: "<UUID v4>"
type: procedure
title: "<10–70 caracteres>"
description: "<120–300 caracteres em pt-BR>"
summary: "<600–1500 caracteres em pt-BR>"
tags: ["<kebab-case>"]
status: pending
version: 1
created_at: "<RFC 3339 UTC>"
updated_at: "<RFC 3339 UTC>"
generated:
  harness: "<claude-code|codex|cursor>"
  model: null
  session_id: "<ID real da sessão>"
  cwd: "<caminho absoluto>"
  machine_id: "<UUID da identidade estável>"
parent: null
related: []
children: []
entities:
  people: []
  companies: []
  products: []
  brands: []
  roles: []
  projects: []
  apps: []
  urls: []
  repos: []
  paths: []
  documents: []
  emails: []
  names: []
---

## Goal

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## When to use

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Prerequisites

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Steps

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Verification

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Rollback

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Pitfalls

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Sources

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Entities

<!-- Condicional: inclua quando houver dados correspondentes -->

| Entidade | Tipo | Quem/o que é | Relação | Período | Fonte |
| --- | --- | --- | --- | --- | --- |

## Dates

<!-- Condicional: inclua quando houver dados correspondentes -->

| Data | O que é | Quem | Status | Fonte |
| --- | --- | --- | --- | --- |

## Figures

<!-- Condicional: inclua quando houver dados correspondentes -->

| Valor | Unidade | O que mede | Quando | Fonte |
| --- | --- | --- | --- | --- |
```

## reference

```markdown
---
id: "<UUID v4>"
type: reference
title: "<10–70 caracteres>"
description: "<120–300 caracteres em pt-BR>"
summary: "<600–1500 caracteres em pt-BR>"
tags: ["<kebab-case>"]
status: pending
version: 1
created_at: "<RFC 3339 UTC>"
updated_at: "<RFC 3339 UTC>"
generated:
  harness: "<claude-code|codex|cursor>"
  model: null
  session_id: "<ID real da sessão>"
  cwd: "<caminho absoluto>"
  machine_id: "<UUID da identidade estável>"
parent: null
related: []
children: []
entities:
  people: []
  companies: []
  products: []
  brands: []
  roles: []
  projects: []
  apps: []
  urls: []
  repos: []
  paths: []
  documents: []
  emails: []
  names: []
---

## Facts

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Scope

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Examples

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Caveats

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Where to find more

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Sources

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Entities

<!-- Condicional: inclua quando houver dados correspondentes -->

| Entidade | Tipo | Quem/o que é | Relação | Período | Fonte |
| --- | --- | --- | --- | --- | --- |

## Dates

<!-- Condicional: inclua quando houver dados correspondentes -->

| Data | O que é | Quem | Status | Fonte |
| --- | --- | --- | --- | --- |

## Figures

<!-- Condicional: inclua quando houver dados correspondentes -->

| Valor | Unidade | O que mede | Quando | Fonte |
| --- | --- | --- | --- | --- |
```

## conversation

```markdown
---
id: "<UUID v4>"
type: conversation
title: "<10–70 caracteres>"
description: "<120–300 caracteres em pt-BR>"
summary: "<600–1500 caracteres em pt-BR>"
tags: ["<kebab-case>"]
status: pending
version: 1
created_at: "<RFC 3339 UTC>"
updated_at: "<RFC 3339 UTC>"
generated:
  harness: "<claude-code|codex|cursor>"
  model: null
  session_id: "<ID real da sessão>"
  cwd: "<caminho absoluto>"
  machine_id: "<UUID da identidade estável>"
parent: null
related: []
children: []
entities:
  people: []
  companies: []
  products: []
  brands: []
  roles: []
  projects: []
  apps: []
  urls: []
  repos: []
  paths: []
  documents: []
  emails: []
  names: []
---

## Participants

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Key facts

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Outcome

<!-- Obrigatória -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Discussion

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Action items

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Open questions

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Sources

<!-- Opcional -->

<Descreva os fatos em pt-BR com contexto, papel e relação.>

## Entities

<!-- Condicional: inclua quando houver dados correspondentes -->

| Entidade | Tipo | Quem/o que é | Relação | Período | Fonte |
| --- | --- | --- | --- | --- | --- |

## Dates

<!-- Condicional: inclua quando houver dados correspondentes -->

| Data | O que é | Quem | Status | Fonte |
| --- | --- | --- | --- | --- |

## Figures

<!-- Condicional: inclua quando houver dados correspondentes -->

| Valor | Unidade | O que mede | Quando | Fonte |
| --- | --- | --- | --- | --- |
```
