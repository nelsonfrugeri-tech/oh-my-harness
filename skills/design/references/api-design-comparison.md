# Design de API — REST vs GraphQL vs gRPC

## Boas Práticas de REST

### Design de URL
```
GET    /v1/users              # List users
GET    /v1/users/123          # Get user by ID
POST   /v1/users              # Create user
PUT    /v1/users/123          # Replace user
PATCH  /v1/users/123          # Partial update
DELETE /v1/users/123          # Delete user

# Nested resources
GET    /v1/users/123/orders   # User's orders

# Filtering, sorting, pagination
GET    /v1/users?status=active&sort=-created_at&page[cursor]=abc&page[size]=20
```

### Paginação: baseada em cursor vs offset

| Abordagem | Prós | Contras | Usar quando |
|----------|------|------|----------|
| Baseada em cursor | Resultados estáveis, performática em escala | Cursor opaco, sem "pular para página" | Grandes volumes de dados, dados em tempo real |
| Offset | Simples, permite "pular para página" | Resultados inconsistentes, lenta com offset alto | Pequenos volumes de dados, UIs administrativas |

**Resposta baseada em cursor:**
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIzfQ==",
    "has_more": true
  }
}
```

### Tratamento de Erros (RFC 9457 — Problem Details)

```json
{
  "type": "https://api.example.com/errors/insufficient-funds",
  "title": "Insufficient Funds",
  "status": 422,
  "detail": "Account balance is $30.00, but transfer requires $50.00",
  "instance": "/transfers/abc-123",
  "balance": 30.00,
  "required": 50.00
}
```

### Idempotência

```
POST /v1/payments
Idempotency-Key: unique-client-generated-uuid

# Server stores result keyed by Idempotency-Key
# Repeated requests with same key return cached result
# Key expires after 24h
```

### Estratégias de Versionamento

| Estratégia | Exemplo | Prós | Contras |
|----------|---------|------|------|
| Caminho na URL | `/v1/users` | Simples, explícito | Muda a URL |
| Header | `Accept: application/vnd.api.v1+json` | URLs limpas | Menos descobrível |
| Parâmetro de query | `/users?version=1` | Simples | Polui os parâmetros |

**Recomendação:** versionamento pelo caminho na URL pela simplicidade. A maioria das APIs precisa de apenas 2-3 versões.

## Boas Práticas de GraphQL

### Design de Schema

```graphql
type Query {
  user(id: ID!): User
  users(first: Int, after: String, filter: UserFilter): UserConnection!
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
}

# Relay-style pagination
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  cursor: String!
  node: User!
}

# Input/Payload pattern
input CreateUserInput {
  name: String!
  email: String!
}

type CreateUserPayload {
  user: User
  errors: [UserError!]!
}
```

### Prevenção de N+1 com DataLoader

```python
# Without DataLoader: N+1 queries
# users query -> 1 query
# for each user, fetch orders -> N queries

# With DataLoader: 2 queries total
from aiodataloader import DataLoader

async def batch_load_orders(user_ids: list[str]) -> list[list[Order]]:
    orders = await db.orders.find({"user_id": {"$in": user_ids}})
    # Group by user_id and return in same order as input
    ...

order_loader = DataLoader(batch_load_orders)
```

### Segurança

```
1. Depth limiting       — max query depth of 10
2. Complexity analysis   — assign cost to each field, limit total
3. Persisted queries     — client sends hash, server looks up query
4. Rate limiting         — per-query complexity, not just per-request
5. Introspection         — disable in production
```

## Boas Práticas de gRPC

### Design do Arquivo Proto

```protobuf
syntax = "proto3";
package ecommerce.v1;

service OrderService {
  rpc CreateOrder(CreateOrderRequest) returns (CreateOrderResponse);
  rpc GetOrder(GetOrderRequest) returns (Order);
  rpc ListOrders(ListOrdersRequest) returns (ListOrdersResponse);
  rpc StreamOrderUpdates(StreamOrderUpdatesRequest) returns (stream OrderUpdate);
}

message CreateOrderRequest {
  string user_id = 1;
  repeated OrderItem items = 2;
  string idempotency_key = 3;
}

message CreateOrderResponse {
  Order order = 1;
}

message ListOrdersRequest {
  int32 page_size = 1;
  string page_token = 2;  // cursor-based pagination
  string filter = 3;       // e.g., "status=PENDING"
}

message ListOrdersResponse {
  repeated Order orders = 1;
  string next_page_token = 2;
}
```

### Regras de Compatibilidade Retroativa

```
SAFE:
- Add new fields (with new field numbers)
- Add new RPC methods
- Add new enum values

UNSAFE (breaking):
- Remove or rename fields
- Change field numbers
- Change field types
- Remove RPC methods
- Change RPC signatures

Use `reserved` for removed fields:
message Order {
  reserved 4, 8;           // field numbers no longer in use
  reserved "old_field";     // field names no longer in use
}
```

### Deadlines e Timeouts

```
Always set deadlines:
- Client sets deadline for the entire call
- Server checks remaining time, propagates to downstream calls
- Default: 5s for simple queries, 30s for complex operations
- Never: infinite timeout (will leak resources)
```

## Abordagem Híbrida (Comum em 2026)

```
                    Internet
                       |
                  API Gateway
                  /    |    \
           REST      GraphQL    (public APIs)
           /v1/*      /graphql
                       |
              Internal Services
              /        |        \
         gRPC       gRPC       gRPC     (internal communication)
        Service A   Service B   Service C
```

**Padrão:** REST para simplicidade pública, GraphQL para flexibilidade no frontend,
gRPC para performance interna.

## Fontes

- https://dev.to/cryptosandy/api-design-best-practices-in-2025-rest-graphql-and-grpc-234h
- https://www.designgurus.io/blog/rest-graphql-grpc-system-design
- RFC 9457 (Problem Details for HTTP APIs)
- https://relay.dev/graphql/connections.htm (Relay Cursor Connections Spec)
