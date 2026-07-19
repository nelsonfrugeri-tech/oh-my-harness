# TDD Deep Dive

## As Três Leis do TDD (Robert C. Martin)

1. Você não pode escrever código de produção até ter escrito um teste unitário que falha
2. Você não pode escrever mais de um teste unitário do que o suficiente para falhar
3. Você não pode escrever mais código de produção do que o suficiente para passar no teste que está falhando

## RED-GREEN-REFACTOR em Detalhe

### RED: Escreva um Teste que Falha

```python
# Start with the simplest behavior
def test_new_cart_has_zero_total():
    cart = Cart()
    assert cart.total == 0
```

Execute. Ele falha (`Cart` ainda não existe). Ótimo.

### GREEN: Faça Passar (do Jeito Mais Simples)

```python
class Cart:
    @property
    def total(self) -> float:
        return 0  # hardcoded — that's fine!
```

Sim, hardcoding é OK na fase GREEN. O próximo teste vai forçar a generalização.

### REFACTOR: Limpe

Há algo para limpar? Ainda não. Passe para o próximo teste.

### Próximo ciclo: Force a generalização

```python
def test_cart_with_one_item_has_item_price_as_total():
    cart = Cart()
    cart.add(Item(price=42.0))
    assert cart.total == 42.0
```

Agora o `return 0` hardcoded falha. Implemente de verdade:

```python
class Cart:
    def __init__(self):
        self._items: list[Item] = []

    def add(self, item: Item) -> None:
        self._items.append(item)

    @property
    def total(self) -> float:
        return sum(item.price for item in self._items)
```

## Ritmo do TDD

```
Test 1: Degenerate case (empty, zero, null)
Test 2: Simplest non-trivial case
Test 3: Another case that forces generalization
Test 4: Edge case or error case
Test 5+: Additional behaviors
```

## Erros Comuns

### Testa a implementação, não o comportamento
```python
# BAD: tests the internal structure
def test_cart_stores_items_in_list():
    cart = Cart()
    cart.add(Item(price=10))
    assert len(cart._items) == 1  # testing private state

# GOOD: tests the observable behavior
def test_cart_with_one_item_reports_correct_count():
    cart = Cart()
    cart.add(Item(price=10))
    assert cart.item_count == 1
```

### Testes demais de uma vez
Escreva UM teste, faça passar, refatore. Depois o próximo. Nunca em lote.

### Pular a etapa de refactor
A etapa de refactor é onde o design emerge. Pulá-la leva a código bagunçado
que apenas por acaso passa nos testes.

## Quando TDD é Difícil

- **Código de UI:** Use testes de BDD/integração em vez de TDD unitário
- **Integrações com terceiros:** Faça mock da fronteira, aplique TDD na lógica
- **Trabalho exploratório/spike:** Pule o TDD, mas escreva testes antes do merge
- **Código legado sem testes:** Adicione characterization tests primeiro, depois aplique TDD nas novas mudanças
