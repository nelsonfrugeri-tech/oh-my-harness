---
version: 1.1.0
name: manage
description: |
  Base de conhecimento de Technical Product/Platform Management. Cobre user stories INVEST,
  critérios de aceite (Given/When/Then), frameworks de priorização (RICE, MoSCoW,
  matriz esforço-impacto), planejamento de roadmap (Now/Next/Later/Won't), template de PRD
  (Problem/Context/Solution/Stories/SLIs/Scope/Risks), métricas AARRR, comunicação com
  stakeholders por público e o fluxo Discovery-Definition-Delivery-Iteration.
  Use quando: (1) Definir e priorizar backlog, (2) Escrever user stories com
  critérios de aceite, (3) Planejar roadmaps e releases, (4) Comunicar decisões de produto
  ao time, (5) Escrever PRDs.
  Gatilhos: /manage, /pm, product management, backlog, user stories, roadmap, priorização, PRD.
type: capability
---

# Manage — Technical Product Management

## Propósito

Esta skill é a base de conhecimento para Technical Product/Platform Management.
Ela foca em gerenciar produtos técnicos — conectando necessidades de negócio e a realidade de engenharia.

**O que esta skill contém:**
- User stories (critérios INVEST, formato de critérios de aceite)
- Frameworks de priorização (RICE, MoSCoW, esforço-impacto)
- Planejamento de roadmap (Now/Next/Later/Won't)
- Template de planejamento de sprint/iteração
- Template de PRD (Product Requirements Document)
- Métricas de produto (framework AARRR)
- Fluxo Discovery → Definition → Delivery → Iteration
- Formatos de comunicação por público
- Gestão de dívida técnica sob a perspectiva de produto

---

## Filosofia

### Produto é Sobre Valor, Não Features

**Toda feature deve ter um "porquê" claro conectado ao valor de negócio.**
As métricas de sucesso são definidas ANTES de iniciar o desenvolvimento.
As decisões são orientadas por dados quando há dados disponíveis, e por hipóteses quando não há.
Apply the `evidence` skill: preserve each hypothesis as falsifiable, keep unknowns explicit, and
never invent a metric to make prioritization appear objective.

### Princípios

1. **Foque no problema do usuário, não na solução técnica**
2. **Critérios de aceite mensuráveis** — "pronto" não é subjetivo
3. **Diga "não" com dados** — reduzir escopo é uma feature, não um fracasso
4. **Roadmaps são compromissos com problemas, não com soluções**
5. **Proteja o time do scope creep enquanto mantém os stakeholders informados**

---

## 1. User Stories

### Formato

```markdown
**As** [persona/user type],
**I want** [action/functionality],
**So that** [benefit/value].

### Acceptance Criteria
- [ ] Given [context], when [action], then [expected result]
- [ ] Given [context], when [action], then [expected result]
- [ ] Given [context], when [action], then [expected result]

### Technical Notes
- {relevant implementation considerations}
- {known dependencies}
- {identified risks}

### Definition of Done
- [ ] Code implemented and reviewed
- [ ] Tests written (unit + integration)
- [ ] Documentation updated
- [ ] Deploy to staging validated
- [ ] Acceptance criteria verified
```

### Critérios INVEST

| Letra | Critério | Significado |
|--------|-----------|---------|
| **I** | Independent | Pode ser desenvolvida isoladamente |
| **N** | Negotiable | Não é um contrato, é uma conversa |
| **V** | Valuable | Entrega valor ao usuário |
| **E** | Estimable | O time consegue estimar o esforço |
| **S** | Small | Cabe em um sprint/iteração |
| **T** | Testable | Critérios de aceite são verificáveis |

### Anti-padrões Comuns

- Stories que dependem umas das outras (viola I)
- "Como um sistema, eu quero..." — não é uma user story
- "Usuário pode criar, ler, atualizar e deletar" — grande demais, divida
- Sem critérios de aceite — "pronto" se torna subjetivo
- Especificações técnicas disfarçadas de user stories

---

## 2. Frameworks de Priorização

### RICE Score

```markdown
| Feature | Reach | Impact | Evidence factor | Effort | RICE Score |
|---------|-------|--------|-----------------|--------|------------|
| {name}  | {measured population} | {defined scale} | {calibrated factor} | {estimate with unit} | {calc} |

Score = (Reach × Impact × Evidence factor) / Effort
```

- **Reach:** Measured population and time window, or a labeled estimate with assumptions
- **Impact:** A defined ordinal or quantitative scale applied consistently to every alternative
- **Evidence factor:** Use a numeric factor only when calibration data defines it; otherwise keep
  evidence strength qualitative and do not calculate a pseudo-precise score
- **Effort:** Estimate with unit, scope, assumptions, and responsible engineering input

RICE is a decision aid, not evidence. Preserve the source and method for every input, list material
hypotheses and unknowns beside the ranking, and compare the result with the status quo. When inputs
are not commensurable, use a qualitative trade-off review instead of fabricated arithmetic.

### MoSCoW

```markdown
### Must Have (P0) — Without this, we don't launch
- {feature}

### Should Have (P1) — Important, but workable without
- {feature}

### Could Have (P2) — Nice to have
- {feature}

### Won't Have (P3) — Explicitly out of scope this release
- {feature} — {reason for deferral}
```

### Matriz Esforço × Impacto

```
|              | Low Effort | High Effort |
|-------------|------------|-------------|
| High Impact | Quick Wins | Big Bets    |
| Low Impact  | Fill-ins   | Money Pits  |
```

**Quick Wins:** Faça primeiro — alto valor, baixo custo
**Big Bets:** Avalie com cuidado — alto valor, alto investimento
**Fill-ins:** Faça se houver tempo — baixo valor, baixo custo
**Money Pits:** Evite — baixo valor, alto custo

---

## 3. Roadmap

### Formato Now / Next / Later / Won't

```markdown
## Roadmap — {Product}

### Now (Current sprint/cycle)
| Item | Status | Owner | ETA |
|------|--------|-------|-----|
| {item} | {status} | {who} | {when} |

### Next (Next cycle)
| Item | Priority | Estimate |
|------|----------|----------|
| {item} | {P0/P1/P2} | {estimate} |

### Later (Prioritized backlog)
| Item | Priority | Notes |
|------|----------|-------|
| {item} | {P1/P2/P3} | {context} |

### Won't Do (Explicit decisions)
| Item | Reason |
|------|--------|
| {item} | {justification} |
```

### Regras do Roadmap

1. **Problemas, não soluções** — roadmaps se comprometem a resolver problemas, não a implementar soluções específicas
2. **Períodos, não datas** — "Próximo trimestre" é mais honesto que "15 de março"
3. **Won't Do explícito** — o que você NÃO vai construir é tão importante quanto o que vai
4. **Revise mensalmente** — roadmaps são documentos vivos, não contratos

---

## 4. Planejamento de Sprint/Iteração

```markdown
## Sprint {N} — {Theme/Goal}

### Objective
{One clear sentence of what we want to achieve}

### Success Criteria
- {measurable deliverable or metric}

### Items
| # | User Story | Estimate | Owner | Status |
|---|-----------|----------|-------|--------|
| 1 | {story}   | {points} | {dev} | {status} |

### Risks and Dependencies
- {identified risk/dependency}

### Team Capacity
- {N} devs × {M} days = {total} person-days available
- Buffer: {historical unplanned-work rate and window, or an explicit trial assumption}
- Net capacity: {net} person-days
```

---

## 5. Template de PRD

```markdown
# PRD: {Feature Name}

## Problem
{What problem are we solving? For whom?}

## Context
{Why now? Data, user feedback, market opportunity}

## Proposed Solution
{High-level description of the solution}

## User Stories
{List of user stories that compose the feature}

## Success Metrics
- {KPI 1}: {baseline} → {target}
- {KPI 2}: {baseline} → {target}

## Scope

### In Scope
- {item}

### Out of Scope
- {item} — {reason for exclusion}

## Dependencies
- {technical or product dependency}

## Timeline
- Discovery: {period}
- Design: {period}
- Development: {period}
- QA/Staging: {period}
- Release: {date}

## Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| {risk} | {H/M/L} | {H/M/L} | {action} |

## SLIs (Service Level Indicators)
- {metric that will measure if this feature is working correctly}
```

---

## 6. Métricas de Produto (AARRR)

```markdown
### Acquisition — How users arrive
- {metric}: {definition and target}

### Activation — First value delivered
- {metric}: {definition and target}

### Retention — Users return
- {metric}: {definition and target}

### Revenue — Monetization
- {metric}: {definition and target}

### Referral — Users bring others
- {metric}: {definition and target}
```

### Boas Práticas de Métricas

1. **Defina as métricas ANTES de construir** — não depois, para justificar a decisão
2. **Indicadores leading em vez de lagging** — detecte problemas cedo
3. **Uma única north star metric** — o que mais importa?
4. **Evite vanity metrics** — page views sem contexto não significam nada
5. **Instrumente desde o primeiro dia** — adicionar analytics depois é doloroso

---

## 7. Fluxo de Produto

### Discovery → Definition → Delivery → Iteration

```
1. DISCOVERY: Understand the problem
   - Research context and data
   - Map personas and needs
   - Identify opportunities
   - Validate hypotheses (user interviews, data analysis)

2. DEFINITION: Define the solution
   - Write PRD
   - Create user stories with acceptance criteria
   - Prioritize backlog (RICE/MoSCoW)
   - Align with technical team (feasibility check)
   - Get stakeholder sign-off

3. DELIVERY: Manage execution
   - Sprint planning with team
   - Daily sync (blockers, decisions)
   - Accept/reject deliveries vs criteria
   - Communicate progress to stakeholders
   - Unblock dependencies

4. ITERATION: Measure and iterate
   - Validate success metrics
   - Collect user feedback
   - Adjust backlog and priorities
   - Document learnings
   - Plan next cycle
```

---

## 8. Comunicação por Público

### Para Desenvolvedores

- User stories detalhadas com critérios de aceite
- Contexto técnico e de negócio relevante
- Decisões de trade-off documentadas
- Disponibilidade para dúvidas e refinamento
- Definição clara de "pronto"

### Para Stakeholders

- Status em formato executivo (resumo, riscos, próximos passos)
- Métricas e progresso vs metas
- Decisões pendentes com opções e recomendação
- Impactos na timeline e no roadmap

### Para Design

- Problemas e contexto do usuário (não prescrições de solução)
- Restrições técnicas relevantes
- Fluxos de usuário e requisitos funcionais
- Critérios de aceite de UX

---

## 9. Dívida Técnica sob a Perspectiva de Produto

### Quando Priorizar Dívida Técnica

- Quando está desacelerando a entrega de features (a velocity está caindo)
- Quando está causando incidentes em produção (a confiabilidade está sofrendo)
- Quando está criando risco de segurança
- Quando está bloqueando contratações-chave (engenheiros não querem trabalhar na base de código)

### Como Apresentar Dívida Técnica aos Stakeholders

```
BAD: "We need to refactor the authentication module."

GOOD: "Authentication code appears in {measured incident share} during {time window}
       according to {incident query}. Our hypothesis is that {change} will improve
       {defined outcome}; validate it with {observation}. Estimated investment:
       {range and assumptions}."
```

### Orçamento de Dívida Técnica

- Derive the budget from incident, delivery, and capacity evidence. Without history, label the
  initial allocation as a trial assumption and define when to review it
- Acompanhe itens de dívida técnica com o mesmo rigor das features
- Inclua o impacto na velocity ao construir o business case

---
