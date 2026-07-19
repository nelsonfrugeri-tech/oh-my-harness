# Documentação de Design

## Ajuste ao Tamanho da Tarefa

### Trivial (< 1 hora)
Nenhum artefato necessário. O modelo mental é suficiente.
Exemplos: renomear variável, corrigir erro de digitação, atualizar valor de config.

### Pequena (1-4 horas)
Comentário na issue ou uma breve nota.
Exemplos: adicionar um novo endpoint, corrigir um bug, adicionar validação.

```markdown
## Approach
- Add `DELETE /api/users/{id}` endpoint
- Soft delete (set `deleted_at` timestamp)
- Return 404 if user not found
- Return 204 on success
```

### Média (1-3 dias)
Breve nota de design com tópicos.
Exemplos: nova funcionalidade, refatoração significativa, nova integração.

```markdown
## Design: {Feature Name}

### Problem
{1-2 sentences}

### Approach
{bullet points}

### Interfaces
{key function signatures or API contracts}

### Data Model
{schema changes if any}

### Edge Cases
{list of edge cases and how to handle them}

### Open Questions
{anything unresolved}
```

### Grande (1+ semana)
Documento de design completo com diagramas.
Exemplos: novo serviço, mudança de arquitetura, funcionalidade grande.

Inclua tudo da Média mais:
- Diagrama de arquitetura
- Diagramas de sequência para os fluxos principais
- Plano de migração (se alterar sistemas existentes)
- Plano de rollout (feature flags, rollout gradual)
- Plano de monitoramento e alertas

## Design Interface-First

Sempre defina a interface pública antes da implementação:

```python
# Define the contract first
class OrderService(Protocol):
    async def create_order(self, request: CreateOrderRequest) -> Order: ...
    async def get_order(self, order_id: str) -> Order: ...
    async def cancel_order(self, order_id: str) -> None: ...
```

```typescript
// Define the contract first
interface OrderService {
  createOrder(request: CreateOrderRequest): Promise<Order>;
  getOrder(orderId: string): Promise<Order>;
  cancelOrder(orderId: string): Promise<void>;
}
```

Isso força você a pensar nos consumidores antes da implementação.
