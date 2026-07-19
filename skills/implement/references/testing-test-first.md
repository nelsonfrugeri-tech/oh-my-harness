# Test-First Principles

## Por Que Escrever Testes Primeiro

1. **Feedback de design** — Testes forçam você a projetar interfaces testáveis
2. **Controle de escopo** — Você só implementa o que os testes exigem
3. **Documentação viva** — Testes descrevem o comportamento, sempre atualizados
4. **Confiança** — Refatore sem medo
5. **Menos defeitos** — IBM/Microsoft reportam até 90% menos defeitos

## A Mentalidade Test-First

```
BEFORE: "I wrote code, now I need to test it"
 (tests are afterthought, coverage padding, implementation-coupled)

AFTER:  "I wrote tests, now I need to make them pass"
 (tests drive design, encode behavior, catch regressions)
```

## Convenção de Nomenclatura de Testes

```
test_<behavior>_when_<condition>_then_<expected>
```

Bons nomes:
```python
test_create_user_when_valid_email_then_returns_user
test_create_user_when_duplicate_email_then_raises_conflict
test_calculate_discount_when_premium_user_then_applies_10_percent
test_login_when_wrong_password_then_returns_401
```

Nomes ruins:
```python
test_create_user           # too vague
test_create_user_1         # meaningless
test_happy_path            # no specificity
test_exception             # which exception?
```

## Estrutura do Teste: Arrange-Act-Assert

```python
def test_apply_discount_when_valid_code_then_reduces_total():
    # Arrange: set up the test scenario
    cart = Cart(items=[Item(price=100)])
    discount = DiscountCode("SAVE10", percent=10)

    # Act: perform the action under test
    cart.apply_discount(discount)

    # Assert: verify the expected outcome
    assert cart.total == 90.0
```

Um teste, um comportamento. Se você precisa de múltiplos asserts, todos devem verificar o mesmo comportamento.

## O Que Testar

| Categoria | Teste | Prioridade |
|----------|------|----------|
| Happy path | O caso de uso normal funciona | P0 |
| Edge cases | Condições de borda | P0 |
| Casos de erro | Entrada inválida, falhas | P0 |
| Integração | Os componentes funcionam juntos | P1 |
| Performance | Atende aos requisitos de latência | P2 |
| Segurança | Auth, injection, acesso | P0 |

## O Que NÃO Testar

- Detalhes internos de implementação
- Internals de framework/biblioteca
- Getters/setters triviais sem lógica
- Código de terceiros (faça mock em vez disso)
