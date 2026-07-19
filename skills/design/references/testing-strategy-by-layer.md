# Estratégia de Testes por Camada Arquitetural

## Pirâmide de Testes por Camada
```
          /  E2E  \           ← Few: critical user journeys
         / Integration \      ← Medium: service boundaries, DB
        /    Unit Tests   \   ← Many: domain logic, pure functions
```

| Camada | Tipo de Teste | O quê | Ferramentas |
|-------|-----------|------|-------|
| Domain/Core | Unit | Regras de negócio, value objects | pytest, jest |
| Application | Unit + Integration | Casos de uso, orquestração | pytest + banco de teste |
| Infrastructure | Integration | Repository, cliente de API | testcontainers |
| API | Contract + Integration | Endpoints, serialização | Pact, pytest |
| E2E | E2E | Fluxos críticos | Playwright, pytest |

## Regras de Teste por Camada
- **Domain**: 100% coberto por testes unitários, sem mocks (lógica pura)
- **Application**: teste com domínio real, mocke a infraestrutura
- **Infrastructure**: teste com dependências reais (testcontainers)
- **API**: testes de contrato para APIs públicas, integração para as internas

## Anti-padrões
- Testar detalhes de implementação em vez de comportamento
- Mockar tudo (os testes passam, a produção falha)
- Testes E2E para edge cases (lentos, flaky)
- Não ter testes para caminhos de erro
