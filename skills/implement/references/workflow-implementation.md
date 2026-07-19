# Disciplina de Implementação

## O Ciclo RED-GREEN-REFACTOR na Prática

### Fase RED
```python
# Write a test that captures the desired behavior
def test_calculate_total_with_discount():
    order = Order(items=[Item(price=100), Item(price=50)])
    order.apply_discount(percent=10)
    assert order.total == 135.0  # (100 + 50) * 0.9
```

Execute. Falha. Bom.

### Fase GREEN
```python
# Write the SIMPLEST code that passes
class Order:
    def __init__(self, items: list[Item]):
        self.items = items
        self._discount = 0

    def apply_discount(self, percent: int) -> None:
        self._discount = percent

    @property
    def total(self) -> float:
        subtotal = sum(item.price for item in self.items)
        return subtotal * (1 - self._discount / 100)
```

Execute. Passa. Bom.

### Fase REFACTOR
- O código está limpo?
- Os nomes são descritivos?
- Há duplicação?
- Podemos simplificar?

Só refatore quando TODOS os testes estiverem verdes.

## Ritmo de Commits

```
Write test (RED)     → don't commit yet
Make it pass (GREEN) → COMMIT: "test: add discount calculation"
Refactor             → COMMIT: "refactor: extract subtotal method"
Next test (RED)      → repeat cycle
```

## Anti-Padrões de Implementação

### The Big Bang
Escrever todo o código primeiro e só depois rodar os testes.
Correção: um teste por vez, rode após cada mudança.

### Gold Plating
Adicionar funcionalidades que não estão nos requisitos.
Correção: implemente apenas o que os testes exigem.

### Premature Optimization
Otimizar antes de medir.
Correção: faça funcionar, faça certo, faça rápido (nessa ordem).

### Shotgun Surgery
Alterar muitos arquivos para uma única funcionalidade.
Correção: projete abstrações melhores, reduza o acoplamento.
