# ATDD — Acceptance Test-Driven Development

## O Fluxo de Trabalho ATDD

```
1. DISCUSS   — Team discusses the feature (devs + product + QA)
2. DISTILL   — Write acceptance criteria as Given/When/Then
3. DEVELOP   — Implement using TDD, driven by acceptance tests
4. DEMO      — Show the passing acceptance tests to stakeholders
```

## Como o ATDD Combina BDD + TDD

```
Acceptance Test (BDD layer — fails)
  |
  +-- Unit Test 1 (TDD — fails → pass)
  +-- Unit Test 2 (TDD — fails → pass)
  +-- Unit Test 3 (TDD — fails → pass)
  |
Acceptance Test (now passes — feature done)
```

**Exemplo de fluxo de trabalho:**

1. Escreva o teste de aceitação:
```gherkin
Scenario: User places an order
  Given a logged-in user with items in cart
  When they submit the order
  Then the order is created with status "pending"
  And the user receives a confirmation email
```

2. Isso falha (sem implementação). Agora use TDD:
   - Ciclo TDD 1: `OrderService.create_order()` — criação básica
   - Ciclo TDD 2: `OrderService.create_order()` — define o status "pending"
   - Ciclo TDD 3: `EmailService.send_confirmation()` — envia o email
   - Ciclo TDD 4: Integração — a criação do pedido dispara o email

3. O teste de aceitação passa. Feature concluída.

## Quando Usar ATDD

- Features complexas com múltiplos componentes
- Features que cruzam fronteiras de serviços
- Features que exigem aprovação de stakeholders
- Fluxos de negócio críticos (pagamentos, auth, processamento de dados)

## ATDD vs TDD Puro vs BDD Puro

| Abordagem | Melhor para |
|----------|----------|
| TDD Puro | Bibliotecas, utilitários, algoritmos |
| BDD Puro | Features simples, contratos de API |
| ATDD | Features complexas, multi-componente, visíveis a stakeholders |

## The Three Amigos

Antes de escrever os testes de aceitação, faça uma sessão "Three Amigos":
- **Developer:** Viabilidade técnica, edge cases
- **Product:** Valor de negócio, critérios de aceitação
- **QA:** Cenários de teste, condições de erro

Duração: 15-30 minutos por feature.
Saída: Critérios de aceitação no formato Given/When/Then.
