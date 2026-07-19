# Estratégias de Decomposição de Sistemas

## Domain-Driven Design (DDD) — Padrões Estratégicos

### Bounded Contexts

Um bounded context é uma fronteira dentro da qual um domain model é consistente e faz sentido.
O mesmo termo (ex.: "Order") pode significar coisas diferentes em bounded contexts diferentes.

```
Sales Context:          Order = quote + pricing + discounts
Fulfillment Context:    Order = items + shipping address + tracking
Billing Context:        Order = invoice + payment status + refunds
```

### Padrões de Context Mapping

| Padrão | Descrição | Quando usar |
|---------|-------------|-------------|
| **Shared Kernel** | Dois contextos compartilham um subconjunto do modelo | Times fortemente acoplados, núcleo compartilhado |
| **Customer-Supplier** | O upstream fornece, o downstream consome | Direção de dependência clara |
| **Conformist** | O downstream se conforma ao modelo do upstream | Sem poder de negociação |
| **Anti-Corruption Layer** | Camada de tradução entre contextos | Integração com legado/externo |
| **Open Host Service** | O upstream fornece uma API publicada estável | Múltiplos consumidores |
| **Published Language** | Linguagem compartilhada (ex.: protocolo, schema) | Comunicação entre contextos |
| **Separate Ways** | Sem integração, duplique se necessário | Contextos verdadeiramente independentes |

### Heurísticas de Decomposição

```
1. Linguistic boundary
   Ask: Do the same terms mean different things to different teams?
   Signal: "Order" means different things to sales vs shipping

2. Data ownership
   Ask: Who is the source of truth for this entity?
   Signal: Two teams both write to the same table

3. Rate of change
   Ask: Do parts of the system change at different speeds?
   Signal: Auth changes yearly, product catalog changes daily

4. Team boundary (Conway's Law)
   Ask: Would different teams own different parts?
   Signal: Organization chart maps to architecture

5. Compliance boundary
   Ask: Are there regulatory requirements that isolate data?
   Signal: PCI-DSS for payments, GDPR for user data

6. Scalability boundary
   Ask: Do parts need to scale independently?
   Signal: Search needs 10x more compute than auth

7. Fault isolation
   Ask: Should a failure in X not affect Y?
   Signal: Payment failure should not block product browsing
```

## Padrão Strangler Fig

Para migrar de monolito para serviços de forma gradual:

```
Phase 1: Route all traffic through facade
  Client -> Facade -> Monolith

Phase 2: Extract one capability, route to new service
  Client -> Facade -> New Service (orders)
                   -> Monolith (everything else)

Phase 3: Extract more capabilities
  Client -> Facade -> Order Service
                   -> User Service
                   -> Monolith (shrinking)

Phase 4: Monolith fully replaced
  Client -> API Gateway -> Order Service
                        -> User Service
                        -> Payment Service
```

**Regras:**
1. Extraia um bounded context por vez
2. Comece pelo contexto menos acoplado
3. Mantenha o monolito funcionando durante todo o processo
4. Cada extração é uma migração completa e testada
5. Nunca faça big bang — sempre incremental

## Anti-padrões

### Monolito Distribuído
Serviços que precisam ser implantados juntos, anulando o propósito dos microservices.
**Sinal:** alterar o serviço A exige alterar o serviço B e implantar ambos.
**Correção:** revise as fronteiras dos serviços, una os serviços fortemente acoplados.

### Banco de Dados Compartilhado
Múltiplos serviços lendo/escrevendo nas mesmas tabelas.
**Sinal:** mudanças de schema exigem coordenação entre times.
**Correção:** cada serviço é dono dos seus dados. Comunique-se via APIs ou eventos.

### Serviços Tagarelas (Chatty Services)
Chamadas síncronas em excesso entre serviços para uma única operação.
**Sinal:** uma requisição de usuário dispara 10+ chamadas HTTP entre serviços.
**Correção:** una serviços, use eventos assíncronos ou desnormalize os dados.

### Nano-serviços
Serviços tão pequenos que o overhead operacional supera o valor.
**Sinal:** um serviço tem um único endpoint e 50 linhas de código.
**Correção:** una a um bounded context maior.

## Fontes

- Eric Evans, "Domain-Driven Design" (2003)
- Vaughn Vernon, "Implementing Domain-Driven Design" (2013)
- Sam Newman, "Building Microservices" (2nd ed, 2021)
- Martin Fowler, "StranglerFigApplication" (2004)
