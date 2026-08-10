---
version: 1.1.0
name: design
description: |
  Base de conhecimento de arquitetura de software (2026). Cobre princípios SOLID com trade-offs reais,
  Architecture Decision Records (template ADR/MADR), C4 Model (Context/Container/Component/Code),
  decomposição de sistemas (DDD, bounded contexts), análise de trade-offs (ATAM, utility trees),
  fitness functions, árvore de decisão entre microservices, monolito e monolito modular,
  arquitetura de segurança (zero trust, STRIDE threat modeling), design de APIs (REST/GraphQL/gRPC),
  e arquitetura orientada a eventos (CQRS, event sourcing).
  Use quando: (1) Tomar decisões arquiteturais, (2) Escrever ADRs, (3) Criar diagramas C4,
  (4) Avaliar trade-offs, (5) Planejar decomposição de sistemas, (6) Projetar APIs,
  (7) Escolher entre monolito/microservices.
  Gatilhos: /design, arquitetura, ADR, C4, trade-off, decomposição, design review.
type: capability
---

# Design — Metodologia de Arquitetura de Software

## Propósito

Esta skill é a base de conhecimento para arquitetura de software (2026).
Ela é **agnóstica de linguagem** — complementa as skills de linguagem com a camada de design e de
tomada de decisão arquitetural.

**O que esta skill contém:**
- Princípios SOLID com trade-offs reais (não os de livro-texto)
- Architecture Decision Records (ADR) — templates, ciclo de vida, MADR
- C4 Model (Context, Container, Component, Code)
- Diagramas — quando usar cada tipo
- Design review com fitness functions
- Decomposição de sistemas (DDD, bounded contexts)
- Análise de trade-offs (ATAM, utility trees)
- Arquitetura de segurança (zero trust, STRIDE, defense in depth)
- Design de APIs (REST, GraphQL, gRPC)
- Arquitetura orientada a eventos (CQRS, event sourcing)
- Decisão entre microservices, monolito e monolito modular

---

## Filosofia

### Arquitetura é sobre Decisões, não Diagramas

Arquitetura de software é o conjunto de decisões que são caras de mudar.
Diagramas são apenas a representação visual dessas decisões.

Apply the `evidence` skill to material architecture choices. An ADR separates verified evidence,
derived results, hypotheses, estimates, and unknowns; cites quantitative provenance; compares the
status quo and viable alternatives; and defines a falsifying result plus review or rollback
conditions. Do not make uncertain inputs look objective by assigning unsupported numeric scores.

### Princípios Fundamentais

1. **Decisões explícitas e documentadas** — toda decisão arquitetural significativa merece um ADR
2. **Trade-offs, nunca soluções mágicas** — toda decisão tem custo e benefício; quantifique-os
3. **Simplicidade primeiro** — comece com a solução mais simples que resolve o problema
4. **Fitness functions como guardrails** — métricas automatizadas protegem decisões arquiteturais
5. **Evolução, não big bang** — a arquitetura evolui de forma incremental

---

## 1. Princípios SOLID — Com Trade-offs Reais

SOLID não é dogma. É um conjunto de ferramentas. Cada princípio tem custo e um contexto onde faz sentido.

### Single Responsibility Principle (SRP)

**O que realmente significa:** Um módulo tem uma, e apenas uma, razão para mudar.

**Trade-off real:**
- SRP excessivo = explosão de classes/módulos minúsculos
- SRP insuficiente = god classes que mudam por 5 razões diferentes
- **Heurística:** se você não consegue nomear a responsabilidade em uma frase, ela é grande demais; se você precisa de 3 classes para seguir um único fluxo, ela é granular demais

### Open/Closed Principle (OCP)

**O que realmente significa:** Aberto para extensão, fechado para modificação.

**Trade-off real:**
- OCP prematuro = abstrações desnecessárias, Strategy pattern para algo que muda uma única vez
- **Heurística:** aplique OCP quando o ponto de variação já apareceu 2 ou mais vezes, não na primeira vez

### Liskov Substitution Principle (LSP)

**O que realmente significa:** Subtipos devem ser substituíveis por seus tipos base.

**Trade-off real:**
- Prefira composição; use herança apenas para relações genuínas de "is-a"

### Interface Segregation Principle (ISP)

**O que realmente significa:** Clientes não devem depender de interfaces que não usam.

**Trade-off real:**
- ISP excessivo = 20 interfaces de um único método, impossíveis de navegar
- **Heurística:** agrupe por coesão de uso, não por granularidade máxima

### Dependency Inversion Principle (DIP)

**O que realmente significa:** Módulos de alto nível não devem depender de módulos de baixo nível; ambos devem depender de abstrações.

**Trade-off real:**
- DIP é essencial nas fronteiras arquiteturais (domínio vs infraestrutura)
- DIP em TUDO = inferno de indireção
- **Heurística:** aplique nas fronteiras; dentro do mesmo módulo, dependências diretas são ok

### Quando NÃO Aplicar SOLID

- Protótipos e MVPs (código descartável é mais barato que abstração)
- Scripts utilitários (< 200 linhas)
- Código de cola entre sistemas (adapters simples)

---

## 2. Architecture Decision Records (ADR)

ADRs capturam decisões arquiteturais significativas com contexto, alternativas e consequências.

### Template MADR

```markdown
# ADR-{NNN}: {Decision Title}

## Status

{Proposed | Accepted | Deprecated | Superseded by ADR-XXX}

## Context

{What problem are we solving? What is the technical and business context?
What constraints exist? What motivated this decision?}

## Decision Drivers

- {driver 1: e.g., latency < 100ms for p99}
- {driver 2: e.g., team has Python experience}
- {driver 3: e.g., budget limited to 2 instances}

## Considered Options

### Option A: {Name}
- **Pros:** {benefits}
- **Cons:** {costs}
- **Effort:** {effort estimate}

### Option B: {Name}
- **Pros:** {benefits}
- **Cons:** {costs}
- **Effort:** {effort estimate}

## Decision

{Which option was chosen and WHY. Explain the reasoning.}

## Consequences

### Positive
- {positive consequence}

### Negative
- {negative consequence and how to mitigate}

### Risks
- {identified risk, supporting evidence, and calibrated likelihood or qualitative uncertainty}

## Related Decisions

- {ADR-XXX: related decision}

## Notes

- {date of decision}
- {participants}
```

### Ciclo de Vida

```
Proposed -> Accepted -> [Active]
                     -> Deprecated (technology/context changed)
                     -> Superseded by ADR-XXX (decision replaced)
```

### Boas Práticas

1. **Uma decisão por ADR** — divida se necessário
2. **Escreva DURANTE a decisão** — não depois
3. **5-10 minutos de leitura** — conciso, focado
4. **Armazene em `/docs/adr/`** — versionado junto com o código
5. **ADRs aceitos são imutáveis** — nova decisão = novo ADR que substitui
6. **Revise a cada 6-12 meses** — deprecie o que não se aplica mais

---

## 3. C4 Model

O C4 Model, de Simon Brown, organiza diagramas em 4 níveis de zoom progressivo.

### Nível 1: System Context

**O que mostra:** O sistema como uma caixa-preta + usuários + sistemas externos.
**Público:** Todos (devs, PMs, stakeholders).
**Regra:** No máximo 10-15 elementos.

```
[User] --> [Your System] --> [External System A]
                         --> [External System B]
```

### Nível 2: Container

**O que mostra:** Containers implantáveis dentro do sistema (web app, API, banco de dados, fila).
**Público:** Devs e ops.
**Regra:** Um container = uma unidade de deploy. Banco de dados é um container. Fila é um container.

```
[Web App] --> [API Server] --> [Database]
                           --> [Message Queue] --> [Worker]
```

### Nível 3: Component

**O que mostra:** Componentes lógicos dentro de um container (controllers, services, repositories).
**Público:** Desenvolvedores do time.
**Regra:** Use apenas para containers complexos. Não é necessário para todos.

### Nível 4: Code

**O que mostra:** Classes/funções dentro de um componente.
**Regra:** Quase nunca vale a pena manter. Use a IDE.

### Quando Criar Cada Nível

| Nível | Quando criar | Quando atualizar | Manter? |
|-------|----------------|----------------|-----------|
| Context | Sempre | A cada novo sistema externo | Sim |
| Container | Sempre | A cada novo container | Sim |
| Component | Containers complexos | Refatorações grandes | Talvez |
| Code | Nunca (use a IDE) | — | Não |

---

## 4. Fitness Functions

Fitness functions são métricas automatizadas que protegem decisões arquiteturais.

The thresholds below are illustrative syntax, not universal targets. Replace them with a measured
baseline, user or business requirement, and explicit observation window for the current system.

```
Fitness Function = metric + baseline + target + threshold + automation
```

| Aspecto | Exemplo | Ferramenta |
|--------|---------|------|
| Coupling | Dependências cíclicas = 0 | deptry, madge |
| Complexidade | Complexidade ciclomática < 15 | ruff, biome |
| Performance | Latência p99 < 200ms | k6, locust |
| Segurança | Vulnerabilidades críticas = 0 | Snyk, Trivy |
| Cobertura | Cobertura de testes > 80% | pytest-cov, vitest |
| Bundle | Tamanho do bundle < 200KB gzip | webpack-bundle-analyzer |
| API | Breaking changes = 0 | openapi-diff |

### Testes de Arquitetura (Fitness Functions em Código)

```python
# Domain layer must not import infrastructure
def test_domain_does_not_import_infra():
    """Ensure domain module has no infrastructure dependencies."""
    import ast
    import pathlib

    domain_files = pathlib.Path("src/domain").rglob("*.py")
    forbidden = {"sqlalchemy", "redis", "httpx", "boto3"}

    for f in domain_files:
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in forbidden
```

---

## 5. Checklist de Design Review

```markdown
## Pre-Review
- [ ] ADR written for significant decisions
- [ ] C4 diagrams updated (Context + Container)
- [ ] Fitness functions defined for quality attributes

## Functional
- [ ] All functional requirements covered
- [ ] Edge cases identified and handled
- [ ] Error handling at all boundaries

## Quality Attributes
- [ ] Performance: SLOs defined and tested
- [ ] Scalability: bottlenecks identified
- [ ] Security: threat model updated
- [ ] Reliability: failure modes mapped
- [ ] Maintainability: complexity controlled

## Operability
- [ ] Structured logging in all components
- [ ] Metrics exposed (RED/USE)
- [ ] Health checks implemented
- [ ] Runbooks for known failure modes

## API
- [ ] Contracts defined (OpenAPI, Protobuf, GraphQL schema)
- [ ] Versioning planned
- [ ] Rate limiting configured
- [ ] Backward compatibility verified
```

---

## 6. Decomposição de Sistemas

### DDD — Bounded Contexts

**Bounded Context** = fronteira lógica onde um modelo de domínio é consistente.

```
Decomposition Heuristics:
1. Linguistic boundary  — do terms change meaning? (e.g., "Order" in Sales vs Shipping)
2. Data ownership       — who is the source of truth for this entity?
3. Rate of change       — do parts change at different speeds?
4. Team boundary        — different teams? Consider separate bounded contexts
5. Compliance boundary  — regulatory requirements isolate components?
```

### Estratégias de Decomposição

| Estratégia | Quando usar | Risco |
|----------|-------------|------|
| Por capacidade de negócio | Domínios claros, times alinhados | Pode criar silos |
| Por subdomínio (DDD) | Core vs supporting vs generic | Exige domínio de negócio |
| Por volatilidade | Partes que mudam muito vs estáveis | Overengineering |
| Por posse de dados | Cada serviço é dono dos seus dados | Transações distribuídas |
| Strangler fig | Migração gradual de legado | Longa, exige disciplina |

### Anti-padrões

1. **Monolito distribuído** — microservices que precisam ser implantados juntos
2. **Banco de dados compartilhado** — múltiplos serviços lendo/gravando na mesma tabela
3. **Serviços tagarelas** — 10 chamadas entre serviços para uma única operação
4. **Nano-serviços** — serviços tão pequenos que o overhead > valor

---

## 7. Decisão entre Microservices e Monolito

### Árvore de Decisão

```
Start here: Do you have well-defined bounded contexts?
  |
  NO --> Use modular monolith
  |
  YES --> Do different parts need to scale independently?
    |
    NO --> Use modular monolith
    |
    YES --> Do you have multiple teams (6+ engineers)?
      |
      NO --> Use modular monolith
      |
      YES --> Do you have mature DevOps practices?
        |
        NO --> Use modular monolith, build DevOps first
        |
        YES --> Consider microservices
```

### Requisitos de Maturidade para Microservices

Antes de dividir em microservices, você DEVE ter:
- [ ] Service discovery
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Logging centralizado
- [ ] API gateway
- [ ] Circuit breakers
- [ ] Testes automatizados nas fronteiras dos serviços
- [ ] CI/CD por serviço
- [ ] Rotação de on-call (microservices falham de novas maneiras)

---

## 8. Análise de Trade-offs (ATAM)

### Utility Tree

```
Quality Attribute
  |
  +-- Stimulus Scenario
  |     Priority: (H,M,L) business x (H,M,L) technical risk
  |
  Example:
    Performance
      |
      +-- "1000 concurrent users, response < 200ms p99" (H,H)
      +-- "Batch job processes 1M records in < 5min" (M,M)

    Availability
      |
      +-- "System survives single AZ failure" (H,H)
      +-- "Zero-downtime deployments" (H,M)
```

### Quantificação de Trade-offs

Não apenas liste trade-offs — quantifique-os:

```markdown
| Decision | Option A | Option B | Winner |
|----------|----------|----------|--------|
| Latency p99 | 50ms | 200ms | A |
| Throughput | 1K rps | 10K rps | B |
| Dev effort | 2 weeks | 6 weeks | A |
| Ops complexity | Low | High | A |
| Cost/month | $500 | $2000 | A |
| Scalability ceiling | 5K users | 500K users | B |
```

---

## 9. Arquitetura de Segurança

### Princípios de Zero Trust

```
1. Never trust, always verify
2. Assume breach
3. Least privilege access
4. Micro-segmentation
5. Continuous verification
```

### Camadas de Defense in Depth

```
Layer 1: Network     — firewall, VPN, network segmentation
Layer 2: Identity    — MFA, SSO, identity provider (OIDC)
Layer 3: Application — input validation, output encoding, CSRF tokens
Layer 4: Data        — encryption at rest, encryption in transit, key rotation
Layer 5: Monitoring  — audit logs, anomaly detection, SIEM
```

### STRIDE Threat Modeling

| Ameaça | Descrição | Mitigação |
|--------|-------------|------------|
| **S**poofing | Falsificar identidade | Authentication, MFA |
| **T**ampering | Modificar dados | Integrity checks, signing |
| **R**epudiation | Negar ações | Audit logging |
| **I**nformation Disclosure | Vazamento de dados | Encryption, access control |
| **D**enial of Service | Sobrecarregar o sistema | Rate limiting, CDN |
| **E**levation of Privilege | Acesso não autorizado | Least privilege, RBAC |

### Checklist de Segurança

```markdown
- [ ] Authentication: OIDC/OAuth2, MFA for privileged ops
- [ ] Authorization: RBAC or ABAC, least privilege
- [ ] Input validation: schema validation at every boundary
- [ ] Secrets management: vault, never hardcoded, rotation policy
- [ ] Encryption: TLS 1.3 in transit, AES-256 at rest
- [ ] Dependency scanning: automated CVE checks in CI
- [ ] Audit logging: who did what when (immutable)
- [ ] Rate limiting: per-user, per-endpoint
- [ ] CORS: restrict to known origins
- [ ] CSP: Content-Security-Policy headers
```

---

## 10. Design de APIs

### REST

```
- Use nouns for resources: /users/{id}, not /getUser/{id}
- Use HTTP methods: GET (read), POST (create), PUT (replace), PATCH (update), DELETE (remove)
- Versioning: /v1/users or Accept: application/vnd.api+json;version=1
- Status codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 404 Not Found, 409 Conflict
- Pagination: cursor-based for large datasets, page-based for UI
- Error format: {code, message, details[]}
```

### GraphQL

```
- Use for data-intensive UIs with flexible queries
- Schema-first: define SDL before implementation
- Resolver depth limiting: prevent N+1 in resolvers
- DataLoader pattern: batch and cache database calls
- Persisted queries: for production (prevent arbitrary queries)
```

### gRPC

```
- Use for internal service-to-service communication
- Protocol Buffers: strongly typed, compact, fast
- Bidirectional streaming for real-time data
- Deadline propagation: always set deadlines on calls
```

### Checklist de Design de APIs

```markdown
- [ ] Contract defined first (OpenAPI / Protobuf / GraphQL schema)
- [ ] Versioning strategy decided
- [ ] Breaking vs non-breaking changes documented
- [ ] Rate limiting configured
- [ ] Authentication scheme documented
- [ ] Error responses standardized
- [ ] Pagination strategy defined
- [ ] Idempotency for mutation endpoints (POST/PUT)
```

---

## Reference Files

- [references/adr-templates.md](references/adr-templates.md) — Templates de ADR
- [references/api-design-comparison.md](references/api-design-comparison.md) — Design de APIs — REST vs GraphQL vs gRPC
- [references/c4-model-guide.md](references/c4-model-guide.md) — Guia do C4 Model
- [references/decomposition-monolith-vs-microservices.md](references/decomposition-monolith-vs-microservices.md) — Monolito vs Monolito Modular vs Microservices
- [references/decomposition-strategies.md](references/decomposition-strategies.md) — Estratégias de Decomposição de Sistemas
- [references/event-driven-patterns.md](references/event-driven-patterns.md) — Padrões de Arquitetura Orientada a Eventos
- [references/observability-design-patterns.md](references/observability-design-patterns.md) — Observabilidade por Design
- [references/security-zero-trust.md](references/security-zero-trust.md) — Arquitetura de Segurança
- [references/testing-strategy-by-layer.md](references/testing-strategy-by-layer.md) — Estratégia de Testes por Camada Arquitetural
- [references/trade-off-analysis-atam.md](references/trade-off-analysis-atam.md) — ATAM — Architecture Tradeoff Analysis Method
- [references/trade-off-analysis-fitness-functions.md](references/trade-off-analysis-fitness-functions.md) — Architecture Fitness Functions
