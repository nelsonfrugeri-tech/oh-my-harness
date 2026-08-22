---
version: 1.0.0
name: implement
description: |
  Metodologia completa de desenvolvimento de software. Cobre todo o workflow
  QUESTION > RESEARCH > DESIGN > TEST > IMPLEMENT > VALIDATE > REVIEW,
  test-first (TDD/BDD/ATDD), workflow de bug fix, refactoring patterns (strangler fig,
  branch by abstraction, parallel change, Mikado), decomposição de features (vertical slicing,
  walking skeleton), self-review checklist, Definition of Done, gestão de technical debt
  e CI discipline.
  Use quando: (1) Planejar como abordar uma tarefa de desenvolvimento, (2) Definir estratégia de testes,
  (3) Refatorar sistemas legados, (4) Quebrar features grandes em entregas incrementais,
  (5) Preparar código para review, (6) Gerenciar technical debt.
  Triggers: /implement, development workflow, TDD, BDD, refactoring, vertical slice,
  walking skeleton, definition of done, technical debt, code review checklist.
type: capability
---

# Implement — Software Development Methodology

## Padrões de código — invioláveis

**Ativar antes de escrever, modificar ou revisar qualquer linha de código.** Estas regras não são sugestões; a fonte completa com exemplos está em [`references/code-craft.md`](references/code-craft.md).

- **Tipagem total, sempre** — nada sem tipo; `Any` só justificado. Concreto: [`../python/references/type-system.md`](../python/references/type-system.md), [`../typescript/references/type-system.md`](../typescript/references/type-system.md).
- **Imutabilidade por padrão** — `frozen=True`, sem mutação in-place, sem estado compartilhado mutável.
- **Superfície pública mínima** — um conceito público por módulo.
- **Funções ≤ 15 linhas (teto ~25); arquivos ≤ 120 linhas** — cresceu, quebre por coesão (não por contagem de linha).
- **Guard clauses, aninhamento ≤ 3** — early returns pros casos de borda; caminho feliz raso. Não force single-return.
- **Mais de 3 `if/elif` no mesmo nível → design pattern** (polymorphism, strategy, dispatch, `match`).
- **Não retorne `None`** — exceção pro erro, coleção vazia pro "nada", `Optional[T]` só quando a ausência é real.
- **≤ 4 parâmetros** — senão, Parameter Object.
- **Comentário explica o porquê, nunca o o quê** — código auto-explicativo; docstrings em inglês.
- **SOLID/patterns na medida (YAGNI)** — sem generalização especulativa.
- **Quality gate ao terminar** — format → lint → typecheck → test, com o comando descoberto do projeto (nunca hardcoded).

---

## Propósito

Esta skill é a base de conhecimento para uma metodologia sistemática de desenvolvimento de software.
Ela define COMO desenvolver software — o processo, a disciplina e os quality gates que
transformam requisitos em código pronto para produção.

**O que esta skill contém:**
- Workflow completo de desenvolvimento (7 fases)
- Metodologia test-first (TDD, BDD, ATDD)
- Workflow de bug fix (da reprodução sistemática à prevenção)
- Metodologia de refactoring (strangler fig, branch by abstraction, parallel change)
- Decomposição de features grandes (vertical slicing, walking skeleton)
- Self-check de code review antes de submeter
- Critérios de Definition of Done
- Gestão de technical debt (modelo de quadrantes)
- CI discipline (commits pequenos, builds verdes, feedback rápido)

**O que esta skill NÃO contém:**
- Padrões específicos de linguagem (esses ficam em `python`, `typescript`)
- Frameworks/ferramentas de teste (esses ficam em `python`, `typescript`, `test`)
- Padrões de arquitetura (esses ficam em `design`)

---

## Filosofia

### Processo é Disciplina, Não Burocracia

Uma boa metodologia elimina desperdício, reduz retrabalho e constrói confiança.
Uma má metodologia adiciona cerimônia sem valor. Esta skill mira na primeira.

### Princípios

1. **Entenda antes de construir** — leia o código existente, contratos, dependências e edge cases
2. **Teste antes de implementar** — defina os acceptance criteria primeiro, escreva testes que falham
3. **Entregue em thin vertical slices** — cada slice é deployável, testável e valiosa
4. **Nunca entregue código sem testes** — "compila" não é um teste
5. **Deixe o codebase melhor do que encontrou** — Boy Scout Rule
6. **Commits pequenos, builds verdes, feedback rápido** — cada commit é atômico e buildável

---

## 1. Workflow de Desenvolvimento — 7 Fases

```
QUESTION > RESEARCH > DESIGN > TEST > IMPLEMENT > VALIDATE > REVIEW
```

Toda tarefa — feature, bug fix, refactor — segue estas fases.
Nenhuma fase pode ser pulada. A profundidade de cada fase escala com a complexidade da tarefa.

### Fase 1: QUESTION

**Objetivo:** Garantir um entendimento cristalino da tarefa.

**Ações:**
- Leia a issue/ticket/requisito por completo
- Leia código, testes e documentação relacionados
- Identifique ambiguidades e resolva-as ANTES de codar
- Mapeie dependências (o que isto afeta?)
- Identifique restrições (performance, compatibilidade, segurança)

**Critérios de saída:**
- [ ] Consegue articular o problema em uma frase
- [ ] Consegue descrever o comportamento esperado (inputs -> outputs)
- [ ] Consegue listar componentes/arquivos afetados
- [ ] Todas as ambiguidades resolvidas (perguntou ao usuário se necessário)

**Anti-patterns:**
- Começar a codar antes de entender o escopo completo
- Assumir requisitos quando não estão claros
- Ignorar edge cases descobertos durante o questionamento

---

### Fase 2: RESEARCH

**Objetivo:** Fundamentar decisões em conhecimento atual, não em suposições.

**Ações:**
- Busque soluções existentes no codebase (isto já foi resolvido antes?)
- Pesquise best practices atuais (libraries, patterns, abordagens)
- Verifique se as dependências precisam de updates
- Cruze múltiplas fontes (docs, GitHub, blogs, benchmarks)
- **Dependency security check** (obrigatório antes de qualquer `pip install` / `pnpm add`):
  1. Busque a última versão estável (nunca confie nos dados de treino)
  2. Verifique CVEs: NVD, GitHub Advisories, Snyk
  3. Verifique se a library é mantida (último release, issues, maintainer ativo)
  4. Após instalar: `pip-audit` / `npm audit`

**Critérios de saída:**
- [ ] Ciente das soluções existentes no codebase
- [ ] Ciente das best practices atuais para este tipo de problema
- [ ] Dependências identificadas com versões pinadas e **segurança verificada**
- [ ] Trade-offs das diferentes abordagens entendidos

---

### Fase 3: DESIGN

**Objetivo:** Tornar as decisões de design explícitas antes de escrever código.

**Ações:**
- Defina a API / interface pública primeiro
- Identifique mudanças de data model / schema
- Escolha o pattern (e documente o PORQUÊ)
- Considere pelo menos 2 abordagens com trade-offs
- Documente brevemente a abordagem escolhida

**Entregáveis (escalam com o tamanho da tarefa):**
- Trivial: modelo mental, nenhum artefato necessário
- Pequena: comentário no código ou na issue
- Média: nota de design breve (bullet points)
- Grande: documento de design com diagramas

**Critérios de saída:**
- [ ] Interfaces/contratos definidos
- [ ] Pattern escolhido com justificativa
- [ ] Edge cases identificados
- [ ] Breaking changes identificados (se houver)

---

### Fase 4: TEST (Escreva os Testes Primeiro)

**Objetivo:** Codificar o comportamento esperado como testes executáveis ANTES de implementar.

**Ações:**
- Escreva testes que falham capturando os acceptance criteria
- Inclua happy path, edge cases e error cases
- Use nomes de teste que descrevem comportamento, não implementação
- Prepare fixtures e dados de teste

**Convenção de nomenclatura de testes:**
```
test_<behavior>_when_<condition>_then_<expected>
```

**Exemplos:**
```python
def test_create_user_when_email_valid_then_returns_user():
    ...

def test_create_user_when_email_duplicate_then_raises_conflict():
    ...
```

**Critérios de saída:**
- [ ] Testes escritos e falhando (fase RED)
- [ ] Testes cobrem o happy path
- [ ] Testes cobrem os principais edge cases
- [ ] Testes cobrem os caminhos de error/exception
- [ ] Nomes de teste descrevem o comportamento claramente

---

### Fase 5: IMPLEMENT

**Objetivo:** Escrever o mínimo de código para os testes passarem, depois refatorar.

**O ciclo RED-GREEN-REFACTOR:**
```
RED:      Write a failing test
GREEN:    Write the simplest code that passes
REFACTOR: Improve design while staying green
REPEAT
```

**Critérios de saída:**
- [ ] Todos os testes passando
- [ ] Código segue o estilo e os patterns do projeto
- [ ] Nenhuma complexidade desnecessária
- [ ] Refactoring completo (clean code)

---

### Fase 6: VALIDATE

**Objetivo:** Provar que o código funciona end-to-end, não apenas em unit tests.

**Ações:**
- Rode a suíte de testes completa (unit + integration + e2e)
- Rode linters e type checkers (`ruff`, `mypy`, `biome`)
- Teste manualmente se aplicável (curl nos endpoints, cheque a UI)
- Verifique em um ambiente o mais próximo possível de produção
- Cheque por regressões (algo mais quebrou?)

**Critérios de saída:**
- [ ] Todos os testes passando (unit, integration, e2e)
- [ ] Linters limpos (zero warnings)
- [ ] Type checker limpo
- [ ] Verificação manual feita (se aplicável)
- [ ] Nenhuma regressão introduzida

---

### Fase 7: REVIEW (Self-Check)

**Objetivo:** Pegar problemas ANTES de submeter para review.

**Ações:**
- Rode o checklist de self-check (veja a Seção 6)
- Revise seu próprio diff como se você fosse o reviewer
- Atualize a documentação (CHANGELOG, README, API docs)
- Commits limpos (atômicos, bem descritos)
- Verifique se a branch está atualizada com a base

**Critérios de saída:**
- [ ] Checklist de self-check aprovado
- [ ] Documentação atualizada
- [ ] Commits limpos e atômicos
- [ ] Branch rebaseada na branch base
- [ ] Pronto para review

---

## 2. Metodologia Test-First

### TDD (Test-Driven Development)

Centrado no desenvolvedor. Foco na implementação correta de unidades individuais.

**Ciclo:**
```
1. RED    — Write a failing test
2. GREEN  — Write the simplest code to pass
3. REFACTOR — Improve design, keep green
4. REPEAT
```

**Quando usar:**
- Business logic, algoritmos, transformações de dados
- Pure functions, código utilitário
- Qualquer código com inputs e outputs claros

**Regras-chave:**
- Nunca escreva código de produção sem um teste que falha
- Escreva apenas código suficiente para passar o teste atual
- Refatore apenas quando verde
- Cada teste deve testar UM comportamento

---

### BDD (Behavior-Driven Development)

Centrado no usuário. Foco no comportamento do sistema pela perspectiva do usuário.
Usa linguagem natural (Given-When-Then) para descrever comportamento.

**Formato:**
```gherkin
Feature: User registration

  Scenario: Successful registration with valid email
    Given a new user with email "user@example.com"
    When they submit the registration form
    Then the account is created
    And a welcome email is sent

  Scenario: Registration fails with duplicate email
    Given an existing user with email "user@example.com"
    When a new user tries to register with "user@example.com"
    Then the registration is rejected with "Email already exists"
```

**Quando usar:**
- Features voltadas ao usuário
- Comunicação cross-funcional (devs + product + QA)
- Acceptance criteria que precisam de validação de stakeholders
- Testes de API contract

---

### ATDD (Acceptance Test-Driven Development)

Combina TDD + BDD. Escreva os acceptance tests primeiro (estilo BDD), depois implemente usando TDD.

```
1. Write acceptance test (BDD — Given/When/Then)
2. Run it — it fails (no implementation)
3. Use TDD to implement the internal components
4. Acceptance test passes — feature is done
```

**Quando usar:**
- Features complexas com múltiplos componentes
- Features que exigem aprovação de stakeholders
- API endpoints (acceptance = API contract, TDD = lógica interna)

---

## 3. Workflow de Bug Fix

Todo bug fix segue um processo sistemático de 6 passos.

```
REPRODUCE > ISOLATE > WRITE TEST > FIX > VALIDATE > PREVENT
```

### Passo 1: REPRODUCE

- Crie um caso de reprodução confiável
- Documente passos exatos, inputs, ambiente
- Confirme que o bug existe (não é erro do usuário nem dado desatualizado)
- Se você não consegue reproduzir, não consegue corrigir

### Passo 2: ISOLATE

- Estreite o code path afetado
- Use busca binária (comente código, faça bisect nos commits)
- Identifique a root cause, não apenas o sintoma
- `git bisect` para bugs de regressão

```bash
git bisect start
git bisect bad HEAD
git bisect good v1.2.0
# Git will binary search through commits
# Test each one, mark good/bad
git bisect good  # or git bisect bad
# When found:
git bisect reset
```

### Passo 3: WRITE TEST (antes de corrigir)

- Escreva um teste que reproduz o bug
- O teste DEVE falhar no código atual
- Esta é sua rede de segurança contra regressão
- Nomeie com clareza: `test_<what>_when_<condition>_does_not_<bug_behavior>`

### Passo 4: FIX

- Corrija a root cause, não o sintoma
- Mude a menor quantidade de código possível
- Não misture a correção com refactoring ou features

### Passo 5: VALIDATE

- Rode o teste que falha — agora ele deve passar
- Rode a suíte de testes completa — sem regressões
- Teste manualmente se aplicável
- Teste o caso de reprodução original

### Passo 6: PREVENT

- Adicione o teste de regressão ao CI
- Considere se a classe do bug precisa de uma regra de linter
- Documente a root cause se não for óbvia
- Considere se bugs similares existem em outros lugares

---

## 4. Metodologia de Refactoring

O refactoring muda a estrutura do código sem mudar o comportamento.
Sempre refatore com redes de segurança (testes). Nunca refatore sem testes.

### Quando Refatorar

- Durante o passo REFACTOR do TDD (em todo ciclo)
- Quando adicionar uma feature exige mudar código existente
- Quando code smells tornam a área difícil de entender
- Quando o technical debt está orçado no sprint
- NUNCA como um "sprint de refactoring" separado (integre no trabalho diário)

### Patterns

#### 4.1 Strangler Fig Pattern

**Quando:** Substituir um sistema/componente legado grande de forma incremental.

```
1. IDENTIFY the component to replace
2. CREATE the new implementation alongside the old one
3. ROUTE traffic/calls gradually to the new implementation
4. MONITOR both implementations in parallel
5. REMOVE the old implementation once the new one is proven
```

**Benefícios:** Zero risco de big-bang, rollback sempre possível, validação em produção a cada passo

**Anti-patterns:** Tentar substituir tudo de uma vez, deixar o código antigo para sempre

#### 4.2 Branch by Abstraction

**Quando:** Refatorar componentes no fundo da stack com dependências upstream.

```
1. IDENTIFY the component to refactor and its callers
2. CREATE an abstraction layer (interface/protocol) between callers and component
3. CHANGE all callers to use the abstraction
4. CREATE the new implementation behind the abstraction
5. SWITCH the abstraction to use the new implementation
6. REMOVE the old implementation
```

**Benefícios:** Todas as mudanças acontecem no trunk (sem branches de longa duração), callers desacoplados

#### 4.3 Parallel Change (Expand-Migrate-Contract)

**Quando:** Mudar uma interface/API que tem múltiplos consumers.

```
1. EXPAND  — Add the new interface alongside the old one
2. MIGRATE — Move consumers to the new interface one by one
3. CONTRACT — Remove the old interface once all consumers migrated
```

```python
# Phase 1: EXPAND
class UserService:
    def get_user(self, user_id: int) -> dict:          # old
        ...
    def get_user_by_uuid(self, uuid: str) -> User:     # new
        ...

# Phase 2: MIGRATE consumers

# Phase 3: CONTRACT
class UserService:
    def get_user_by_uuid(self, uuid: str) -> User:     # only new
        ...
```

#### 4.4 Mikado Method

**Quando:** Refactoring grande com dependências desconhecidas.

```
1. SET a refactoring goal
2. TRY to implement it directly
3. If it breaks things, NOTE the prerequisite
4. REVERT your change
5. IMPLEMENT the prerequisite first
6. TRY the goal again
7. REPEAT until the goal succeeds
```

Produz um grafo de dependências (Mikado Graph) das mudanças necessárias.

---

## 5. Decomposição de Features

### Vertical Slicing

**Princípio central:** Cada slice atravessa TODAS as camadas (UI, API, business logic, dados)
e entrega valor visível ao usuário.

**Horizontal slice (ERRADO):**
```
Sprint 1: Build database schema
Sprint 2: Build API endpoints
Sprint 3: Build frontend
Sprint 4: Integration testing
Sprint 5: Finally works end-to-end
```

**Vertical slice (CERTO):**
```
Slice 1: User can create an account (simple form, one API, one table)
Slice 2: User can log in (auth flow end-to-end)
Slice 3: User can update profile (edit form, API, validation)
```

### Heurísticas de Slicing

| Técnica | Descrição | Exemplo |
|-----------|-------------|---------|
| **Por workflow step** | Cada passo de um processo vira uma slice | Checkout: add to cart, enter address, pay |
| **Por business rule** | Cada regra vira uma slice | Pricing: base price, bulk discount, loyalty |
| **Por variação de dados** | Cada tipo de dado vira uma slice | Import: CSV primeiro, depois Excel, depois API |
| **Por operação** | Operações CRUD como slices separadas | Users: create primeiro, depois read, update, delete |
| **Por persona** | Diferentes tipos de usuário como slices | Admin dashboard, depois user dashboard |

### Walking Skeleton

**Definição:** A menor slice possível de funcionalidade real que pode ser construída,
deployada e testada end-to-end.

**Características:**
- Atravessa TODAS as camadas (da UI ao database)
- Deployável para produção (mesmo com feature flag)
- Tem testes automatizados
- Tem CI/CD configurado
- Leva no máximo 1-4 dias

**Exemplo — walking skeleton de e-commerce:**
```
UI:       Single page with a "Buy" button and a product name
API:      POST /orders with hardcoded product
Business: Create order with fixed price
Database: orders table with id, product, status
Deploy:   Docker + CI + staging environment
Test:     E2E test: click Buy -> order created
```

Depois incremente: adicione product catalog, cart, payment, etc.

### Template de Decomposição de Feature

```markdown
## Feature: {name}

### Walking Skeleton (Slice 0)
- {thinnest end-to-end path}
- Target: {1-4 days}

### Slice 1: {name}
- User story: As a {persona}, I want {action}, so that {value}
- Acceptance criteria: Given {context}, When {action}, Then {result}
- Estimated: {days}

### Slice 2: {name}
...

### Out of scope (explicit)
- {what we are NOT building}
```

---

## 6. Self-Check Antes do Review

Rode este checklist ANTES de submeter o código para review.

### Corretude
- [ ] O código faz o que o ticket/issue pede
- [ ] Todos os acceptance criteria atendidos
- [ ] Edge cases tratados
- [ ] Error cases tratados com mensagens apropriadas
- [ ] Nenhum erro de off-by-one
- [ ] Nenhum acesso null/undefined sem guards

### Testes
- [ ] Todo código novo tem testes
- [ ] Os testes são significativos (não apenas enchimento de coverage)
- [ ] Testes cobrem happy path, edge cases, error cases
- [ ] Nomes de teste descrevem o comportamento
- [ ] Todos os testes passam localmente
- [ ] Nenhum teste flaky introduzido

### Qualidade de Código
- [ ] Nenhum `TODO` ou `FIXME` sem uma issue vinculada
- [ ] Nenhum código comentado
- [ ] Nenhum print/log de debug deixado para trás
- [ ] Nomes de variáveis/funções são descritivos
- [ ] Funções são pequenas e focadas (single responsibility)
- [ ] Nenhuma duplicação de código
- [ ] Type hints completos (Python) ou strict types (TypeScript)

### Segurança
- [ ] Nenhum secret ou credencial no código
- [ ] Input do usuário validado e sanitizado
- [ ] SQL injection prevenido (parameterized queries)
- [ ] Nenhum dado sensível em logs
- [ ] Checagens de authentication/authorization implementadas

### Performance
- [ ] Nenhuma query N+1
- [ ] Nenhuma chamada de API desnecessária em loops
- [ ] Recursos gerenciados corretamente (connections, files, locks)
- [ ] Caching apropriado considerado

### Documentação
- [ ] CHANGELOG.md atualizado
- [ ] README.md atualizado (se houver mudanças voltadas ao usuário)
- [ ] Documentação de API atualizada (se endpoints mudaram)
- [ ] Comentários no código para lógica não óbvia
- [ ] Docstrings em funções/classes públicas

### Higiene de Git
- [ ] Commits são atômicos e bem descritos
- [ ] Nenhum merge commit (rebaseado na branch base)
- [ ] Nenhuma mudança não relacionada misturada
- [ ] Nome da branch segue a convenção

---

## 7. Definition of Done

Um trabalho está DONE quando TODOS estes forem verdadeiros:

### Código
- [ ] Implementação completa e correspondente aos acceptance criteria
- [ ] Código segue o estilo e as convenções do projeto
- [ ] Nenhum TODO que não estava no escopo original
- [ ] Todos os linters passam (ruff, mypy, biome — zero warnings)

### Testes
- [ ] Unit tests escritos e passando
- [ ] Integration tests escritos e passando (se aplicável)
- [ ] E2E tests escritos e passando (se aplicável)
- [ ] Coverage de testes atinge o threshold do projeto
- [ ] Nenhum teste flaky

### Review
- [ ] Checklist de self-check aprovado
- [ ] Código revisado por pelo menos uma outra pessoa
- [ ] Todos os comentários de review resolvidos ou explicitamente adiados com justificativa
- [ ] Reviewer aprovou (nenhum BLOCKER restante)

### Integração
- [ ] Todos os checks de CI passando
- [ ] Nenhum merge conflict
- [ ] Branch atualizada com a branch base
- [ ] Merge bem-sucedido na branch base

### Documentação
- [ ] CHANGELOG.md atualizado
- [ ] README.md atualizado se features voltadas ao usuário mudaram
- [ ] Documentação de API atualizada se contratos mudaram

### Deployment
- [ ] Deploy bem-sucedido em staging
- [ ] Smoke tests passando em staging
- [ ] Nenhum alerta de monitoring disparado após o deployment
- [ ] Plano de rollback conhecido

---

## 8. Gestão de Technical Debt

### O Modelo de Quadrantes

```
              RECKLESS                    PRUDENT
DELIBERATE    "We don't have time         "We must ship now, but know
              for design"                  the trade-offs"

INADVERTENT   "What's layering?"          "Now we know how we should
                                           have done it"
```

**Reckless + deliberate:** Nunca aceitável. É cortar caminho de forma consciente.
**Prudent + deliberate:** Aceitável com decisão explícita e pagamento agendado.
**Inadvertent:** Descoberto via code review e retrospectivas — refatore quando encontrar.

### Gerenciando o Débito

1. **Torne-o visível** — registre os itens de débito no seu issue tracker
2. **Classifique-o** — Reckless/Prudent, Deliberate/Inadvertent
3. **Orce para ele** — reserve 20% de cada sprint para tech debt
4. **Pague-o incrementalmente** — Boy Scout Rule: deixe o código melhor do que encontrou
5. **Nunca deixe acumular silenciosamente** — discuta o débito nas retrospectivas

---

## 9. CI Discipline

### Commits Pequenos

- Cada commit é atômico, focado e buildável
- O CI deve passar em todo commit — sem exceções
- Builds quebrados são a prioridade máxima do time

### Formato da Mensagem de Commit

```
<type>(<scope>): <description>

<body> (optional)

<footer> (optional)
```

**Types:** feat, fix, refactor, test, docs, chore, perf

**Exemplos:**
```
feat(auth): add JWT refresh token rotation
fix(orders): prevent N+1 query on order list
refactor(users): extract user validation to service layer
test(payments): add integration tests for webhook handling
```

### Estratégia de Branch

- Feature branches: `feat/issue-{N}-{description}`
- Bug fixes: `fix/issue-{N}-{description}`
- Refactoring: `refactor/{description}`
- Nunca faça commit direto em `main` ou `develop`

---

## Reference Files

- [references/ci-discipline.md](references/ci-discipline.md) — CI Discipline
- [references/code-craft.md](references/code-craft.md) — Code craft — padrões invioláveis
- [references/code-review-self-check.md](references/code-review-self-check.md) — Self-Check Pré-Submissão
- [references/feature-breakdown-vertical-slicing.md](references/feature-breakdown-vertical-slicing.md) — Vertical Slicing & Walking Skeleton
- [references/pipeline-stages.md](references/pipeline-stages.md) — Pipeline — Definição dos 9 Estágios
- [references/pipeline-transitions.md](references/pipeline-transitions.md) — Pipeline — Critérios de Transição entre Estágios
- [references/qa-execution-protocol.md](references/qa-execution-protocol.md) — QA — Protocolo de Execução
- [references/refactoring-patterns.md](references/refactoring-patterns.md) — Refactoring Patterns
- [references/review-handoff-protocol.md](references/review-handoff-protocol.md) — Review Handoff — Protocolo de Comunicação
- [references/self-judge-checklist.md](references/self-judge-checklist.md) — Self-Judge — Checklist
- [references/technical-debt-quadrant.md](references/technical-debt-quadrant.md) — Technical Debt Quadrant (Martin Fowler)
- [references/templates-qa-report.md](references/templates-qa-report.md) — Template — QA Report
- [references/templates-review-summary.md](references/templates-review-summary.md) — Template — Review Summary
- [references/testing-atdd.md](references/testing-atdd.md) — ATDD — Acceptance Test-Driven Development
- [references/testing-bdd.md](references/testing-bdd.md) — BDD — Behavior-Driven Development
- [references/testing-tdd.md](references/testing-tdd.md) — TDD — Aprofundamento
- [references/testing-test-first.md](references/testing-test-first.md) — Princípios de Test-First
- [references/workflow-bug-fix.md](references/workflow-bug-fix.md) — Processo Sistemático de Bug Fix
- [references/workflow-design.md](references/workflow-design.md) — Documentação de Design
- [references/workflow-implementation.md](references/workflow-implementation.md) — Disciplina de Implementação
- [references/workflow-pairing.md](references/workflow-pairing.md) — Pair e Mob Programming
- [references/workflow-questioning.md](references/workflow-questioning.md) — Técnicas de Questionamento
- [references/workflow-research.md](references/workflow-research.md) — Metodologia de Research
- [references/workflow-validation.md](references/workflow-validation.md) — Checklist de Validação