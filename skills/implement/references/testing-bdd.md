# BDD — Behavior-Driven Development

## Formato Given-When-Then

```gherkin
Feature: Shopping cart discount

  Scenario: Apply percentage discount to cart
    Given a cart with items totaling $100
    When I apply a 10% discount code "SAVE10"
    Then the cart total should be $90

  Scenario: Reject expired discount code
    Given a cart with items totaling $100
    And a discount code "OLD20" that expired yesterday
    When I apply the discount code "OLD20"
    Then the discount is rejected
    And the cart total remains $100
```

## BDD vs TDD

| Aspecto | TDD | BDD |
|--------|-----|-----|
| Público | Developers | Developers + Product + QA |
| Linguagem | Código | Linguagem natural (Gherkin) |
| Escopo | Unidade | Feature/comportamento |
| Foco | Correção da implementação | Entrega de valor de negócio |
| Artefatos | Testes unitários | Especificações executáveis |

## Quando Usar BDD

- Features voltadas ao usuário com critérios de aceitação claros
- Features que precisam de validação de stakeholders
- Contratos de API consumidos por múltiplos times
- Onboarding: specs BDD servem como documentação viva

## Quando NÃO Usar BDD

- Detalhes internos de implementação
- Funções utilitárias
- Otimizações de performance
- Código de infraestrutura

## Implementação de BDD

### Python (pytest-bdd)
```python
from pytest_bdd import scenario, given, when, then, parsers

@scenario("cart.feature", "Apply percentage discount to cart")
def test_apply_discount():
    pass

@given("a cart with items totaling $100")
def cart():
    return Cart(items=[Item(price=100)])

@when(parsers.parse('I apply a {percent:d}% discount code "{code}"'))
def apply_discount(cart, percent, code):
    cart.apply_discount(DiscountCode(code, percent=percent))

@then(parsers.parse("the cart total should be ${total:d}"))
def check_total(cart, total):
    assert cart.total == total
```

### TypeScript (Cucumber)
```typescript
import { Given, When, Then } from "@cucumber/cucumber";

Given("a cart with items totaling ${int}", function (total: number) {
  this.cart = new Cart([new Item({ price: total })]);
});

When("I apply a {int}% discount code {string}", function (percent: number, code: string) {
  this.cart.applyDiscount(new DiscountCode(code, percent));
});

Then("the cart total should be ${int}", function (expected: number) {
  expect(this.cart.total).toBe(expected);
});
```

## Escrevendo Bons Cenários

**Regras:**
- Um cenário = um comportamento
- Use linguagem de negócio, não termos técnicos
- Evite detalhes de implementação nos cenários
- Mantenha os cenários curtos (3-7 passos)
- Use Background para passos Given compartilhados
