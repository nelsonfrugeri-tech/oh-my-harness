---
version: 1.0.0
name: api-design
description: |
  Base de conhecimento de design de APIs (2026). Cobre REST (nomeação de recursos, métodos HTTP, status codes,
  paginação, versionamento, HATEOAS), GraphQL (schema-first, resolvers, DataLoader, persisted queries),
  gRPC (Protocol Buffers, streaming, propagação de deadline), workflow contract-first com OpenAPI,
  padrões de idempotência, padrões de resposta de erro, rate limiting, regras de compatibilidade retroativa
  e checklists de design de API.
  Use quando: (1) Projetar APIs REST, GraphQL ou gRPC, (2) Escrever contratos OpenAPI/Protobuf,
  (3) Avaliar estratégia de versionamento, (4) Definir formatos de resposta de erro, (5) Revisar design de API.
  Gatilhos: /api-design, /api, REST, GraphQL, gRPC, OpenAPI, API design, pagination, versioning.
type: knowledge
---

# API Design — Base de Conhecimento

## Propósito

Esta skill é a base de conhecimento para projetar APIs (2026).
Cobre REST, GraphQL, gRPC, workflow contract-first e os padrões que tornam as APIs
previsíveis, evoluíveis e seguras.

**O que esta skill contém:**
- Design REST (recursos, métodos HTTP, status codes, versionamento, paginação)
- GraphQL (schema-first, prevenção de N+1, persisted queries)
- gRPC (Protocol Buffers, tipos de streaming, deadlines)
- Workflow contract-first com OpenAPI / Protobuf
- Padrões de resposta de erro
- Padrões de idempotência
- Rate limiting e throttling
- Regras de compatibilidade retroativa
- Checklist de design de API

---

## Filosofia

### Contract First

Defina o contrato antes da implementação. Código sem um contrato é um detalhe de implementação
se passando por uma API.

1. Escreva a spec OpenAPI (ou o schema Protobuf / GraphQL) primeiro
2. Gere stubs, mocks e SDKs de cliente a partir do contrato
3. Implemente conforme a spec
4. Valide a implementação contra a spec no CI

### Princípio da Menor Surpresa

Uma API é uma interface de usuário para desenvolvedores. Cada decisão de design deve minimizar a surpresa:
- Convenções de nomeação consistentes em todos os endpoints
- Formatos de erro consistentes independentemente do que falhou
- Comportamento consistente para casos extremos (listas vazias, campos nulos, timestamps)

---

## 1. Design de API REST

### Nomeação de Recursos

```
# GOOD — nouns, plural, hierarchical
GET    /users                   # list users
POST   /users                   # create user
GET    /users/{id}              # get user
PATCH  /users/{id}              # partial update
DELETE /users/{id}              # delete user
GET    /users/{id}/orders       # list user orders
POST   /users/{id}/orders       # create order for user

# BAD — verbs in path
GET    /getUser/{id}            # no verbs
POST   /createOrder             # no verbs
POST   /users/{id}/activate     # exception: actions on resources
```

### Métodos HTTP

| Método | Idempotente | Seguro | Caso de Uso |
|--------|-----------|------|---------|
| GET | Sim | Sim | Ler recurso |
| HEAD | Sim | Sim | Ler apenas os headers |
| POST | Não | Não | Criar recurso, ações não idempotentes |
| PUT | Sim | Não | Substituir o recurso por completo |
| PATCH | Não | Não | Atualização parcial |
| DELETE | Sim | Não | Remover recurso |

### Códigos de Status HTTP

```
2xx — Success
  200 OK              GET, PATCH, DELETE success
  201 Created         POST success (include Location header)
  202 Accepted        Async operation accepted
  204 No Content      DELETE success, no body

4xx — Client Error
  400 Bad Request     Validation failed, malformed request
  401 Unauthorized    Authentication required
  403 Forbidden       Authenticated but not authorized
  404 Not Found       Resource does not exist
  409 Conflict        State conflict (duplicate, version mismatch)
  410 Gone            Resource permanently deleted
  422 Unprocessable   Semantic validation failed
  429 Too Many Reqs   Rate limit exceeded

5xx — Server Error
  500 Internal Error  Unexpected server failure
  502 Bad Gateway     Upstream service failed
  503 Unavailable     Service temporarily down
  504 Gateway Timeout Upstream timed out
```

### Resposta de Erro Padrão

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format",
        "value": "not-an-email"
      }
    ],
    "request_id": "req_abc123",
    "documentation_url": "https://api.example.com/docs/errors#VALIDATION_FAILED"
  }
}
```

### Estratégias de Versionamento

| Estratégia | Exemplo | Prós | Contras |
|----------|---------|------|------|
| URL path | `/v1/users` | Simples, cacheável, explícito | Poluição da URL |
| Header | `Accept: application/vnd.api+json;version=1` | URLs limpas | Menos visível |
| Query param | `/users?version=1` | Fácil de testar | Problemas de cache |

**Recomendação:** versionamento por URL path para APIs públicas. Versionamento por header para APIs internas.

### Paginação

```
# Cursor-based (recommended for large datasets)
GET /items?cursor=eyJpZCI6MTAwfQ==&limit=20
Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIwfQ==",
    "has_more": true
  }
}

# Page-based (acceptable for small datasets with UI pagination)
GET /items?page=2&per_page=20
Response:
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 450,
    "total_pages": 23
  }
}
```

**Regras de paginação baseada em cursor:**
- O cursor é opaco (codificado em base64, não adivinhável)
- Estável sob escritas concorrentes (sem desvio de offset)
- Obrigatório para scroll infinito e feeds em tempo real

### Filtragem e Ordenação

```
# Filtering
GET /products?category=electronics&min_price=100&max_price=500
GET /orders?status=pending&created_after=2025-01-01T00:00:00Z

# Sorting
GET /products?sort=price&order=asc
GET /products?sort=-price          # minus prefix = descending

# Field selection (sparse fieldsets)
GET /users?fields=id,name,email    # return only specified fields
```


---

## 2. GraphQL

### Quando Usar GraphQL

| Use GraphQL | Use REST |
|-------------|---------|
| UI intensiva em dados (múltiplos recursos por tela) | APIs CRUD simples |
| Clientes precisam de seleção flexível de campos | Upload/download de arquivos |
| Múltiplos tipos de consumidores (mobile, web, terceiros) | APIs públicas simples |
| Iteração rápida de UI (frontend altera campos livremente) | Receptores de webhook |

### Workflow Schema-First

```graphql
# schema.graphql — define contract first
type User {
  id: ID!
  name: String!
  email: String!
  orders(first: Int = 10, after: String): OrderConnection!
  createdAt: DateTime!
}

type Order {
  id: ID!
  status: OrderStatus!
  total: Float!
  items: [OrderItem!]!
}

type OrderConnection {
  edges: [OrderEdge!]!
  pageInfo: PageInfo!
}

type OrderEdge {
  node: Order!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  endCursor: String
}

enum OrderStatus {
  PENDING
  CONFIRMED
  SHIPPED
  DELIVERED
  CANCELLED
}

type Query {
  user(id: ID!): User
  users(first: Int = 10, after: String, filter: UserFilter): UserConnection!
}

type Mutation {
  createOrder(input: CreateOrderInput!): CreateOrderPayload!
  cancelOrder(id: ID!): CancelOrderPayload!
}
```

### DataLoader — Prevenção de N+1

```typescript
import DataLoader from "dataloader";

// Without DataLoader: N+1 queries
// For 100 orders, 100 separate DB calls to load each user

// With DataLoader: batch and cache
const userLoader = new DataLoader<string, User>(async (userIds) => {
	const users = await db.user.findMany({ where: { id: { in: [...userIds] } } });
	const userMap = new Map(users.map((u) => [u.id, u]));
	return userIds.map((id) => userMap.get(id) ?? new Error(`User ${id} not found`));
});

// Resolver uses DataLoader — automatically batched
const orderResolvers = {
	Order: {
		user: (order: Order, _args: unknown, ctx: Context) =>
			ctx.loaders.user.load(order.userId),
	},
};
```

### Persisted Queries (Produção)

```typescript
// Prevents arbitrary query execution in production
// Client sends hash, server looks up the full query

const persistedQueries = new Map<string, string>();

function persistedQueryPlugin(): ApolloServerPlugin {
	return {
		requestDidStart: async () => ({
			async didResolveOperation({ request, document }) {
				if (process.env.NODE_ENV === "production") {
					const hash = request.extensions?.persistedQuery?.sha256Hash;
					if (!hash || !persistedQueries.has(hash)) {
						throw new ForbiddenError("Unpersisted query not allowed in production");
					}
				}
			},
		}),
	};
}
```


---

## 3. gRPC

### Quando Usar gRPC

| Use gRPC | Use REST/GraphQL |
|----------|-----------------|
| Comunicação interna service-to-service | API externa/pública |
| Alto throughput, baixa latência | Clientes de navegador (sem grpc-web) |
| Streaming bidirecional | Request-response simples |
| Contratos fortemente tipados são críticos | Evolução flexível de schema |

### Protocol Buffers

```protobuf
// user.proto
syntax = "proto3";

package user.v1;

import "google/protobuf/timestamp.proto";

service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc ListUsers(ListUsersRequest) returns (stream User);
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc UpdateUser(UpdateUserRequest) returns (User);
}

message User {
  string id = 1;
  string name = 2;
  string email = 3;
  google.protobuf.Timestamp created_at = 4;
  UserStatus status = 5;
}

enum UserStatus {
  USER_STATUS_UNSPECIFIED = 0;
  USER_STATUS_ACTIVE = 1;
  USER_STATUS_SUSPENDED = 2;
}

message GetUserRequest {
  string id = 1;
}

message ListUsersRequest {
  int32 page_size = 1;
  string page_token = 2;
  string filter = 3;
}
```

### Tipos de Streaming

| Tipo | Padrão | Caso de Uso |
|------|---------|---------|
| Unary | 1 req → 1 resp | Chamada RPC padrão |
| Server streaming | 1 req → muitas resp | Download de arquivo, feed ao vivo |
| Client streaming | muitas req → 1 resp | Upload de arquivo, escrita em lote |
| Bidirectional | muitas req ↔ muitas resp | Chat, colaboração em tempo real |

### Propagação de Deadline (Sempre)

```python
import grpc

channel = grpc.insecure_channel("localhost:50051")
stub = UserServiceStub(channel)

# ALWAYS set a deadline
try:
    user = stub.GetUser(
        GetUserRequest(id="usr_123"),
        timeout=5.0,  # seconds — never omit this
    )
except grpc.RpcError as e:
    if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
        raise TimeoutError(f"GetUser timed out after 5s")
    if e.code() == grpc.StatusCode.NOT_FOUND:
        raise NotFoundError("User", "usr_123")
    raise ExternalServiceError("user-service", e)
```


---

## 4. OpenAPI Contract-First

### Estrutura do OpenAPI 3.1

```yaml
openapi: "3.1.0"
info:
  title: User API
  version: "1.0.0"
  description: |
    API for user management.
    See [authentication guide](https://docs.example.com/auth) for details.

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://api.staging.example.com/v1
    description: Staging

paths:
  /users/{id}:
    get:
      operationId: getUser
      summary: Get a user by ID
      tags: [users]
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            pattern: "^usr_[a-zA-Z0-9]{20}$"
      responses:
        "200":
          description: User found
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
        "404":
          $ref: "#/components/responses/NotFound"

components:
  schemas:
    User:
      type: object
      required: [id, name, email, created_at]
      properties:
        id:
          type: string
          example: "usr_abc123"
        name:
          type: string
          minLength: 1
          maxLength: 100
        email:
          type: string
          format: email
        created_at:
          type: string
          format: date-time
  responses:
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/Error"
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

### Validação Contract-First no CI

```yaml
# GitHub Actions
- name: Validate OpenAPI spec
  uses: actions/setup-node@v4
- run: npx @redocly/cli lint openapi.yaml
- run: npx @redocly/cli check-config openapi.yaml

- name: Check for breaking changes
  uses: oasdiff/oasdiff-action@main
  with:
    base: origin/main:openapi.yaml
    revision: openapi.yaml
    fail-on-diff: breaking
```


---

## 5. Idempotência

```
Idempotent: calling the same operation multiple times has the same effect as calling it once.

Why it matters:
- Network failures → clients retry → server processes duplicate
- Without idempotency: double charges, duplicate records, data corruption

Strategies:
1. Client-provided idempotency key (header: Idempotency-Key: <uuid>)
2. Server stores result for 24h–7 days
3. Return stored result for duplicate requests
4. Response includes: X-Idempotent-Replayed: true
```

```yaml
# OpenAPI: document idempotency key
paths:
  /payments:
    post:
      parameters:
        - name: Idempotency-Key
          in: header
          required: true
          schema:
            type: string
            format: uuid
          description: |
            Unique key to ensure idempotency. Generate a UUID per operation attempt.
            Duplicate requests with the same key return the cached response.
```

---

## 6. Rate Limiting

### Headers de Resposta

```
X-RateLimit-Limit: 1000        # requests allowed per window
X-RateLimit-Remaining: 750     # requests remaining in current window
X-RateLimit-Reset: 1701388800  # unix timestamp when window resets
Retry-After: 30                # seconds to wait after 429
```

### Estratégias de Rate Limit

| Estratégia | Prós | Contras | Caso de Uso |
|----------|------|------|---------|
| Fixed window | Simples | Rajada na borda da janela | APIs internas |
| Sliding window | Distribuição suave | Mais complexa | APIs públicas |
| Token bucket | Amigável a rajadas | Estado por cliente | CDN, proxy reverso |
| Leaky bucket | Taxa consistente | Enfileira requisições | APIs de pagamento |

---

## 7. Regras de Compatibilidade Retroativa

### Mudanças Não Quebradas (seguras para publicar)

- Adicionar campos opcionais de requisição
- Adicionar campos de resposta (clientes ignoram campos desconhecidos)
- Adicionar novos endpoints
- Adicionar novos valores de enum (se os clientes lidam com valores desconhecidos)
- Expandir os valores permitidos de um campo

### Mudanças Quebradas (exigem nova versão da API)

- Remover ou renomear campos
- Alterar tipos de campos
- Adicionar campos obrigatórios de requisição
- Alterar as URLs dos endpoints
- Alterar o comportamento de operações existentes
- Remover valores de enum

### Protocolo de Depreciação

```
1. Add Deprecation header to responses:
   Deprecation: true
   Sunset: Wed, 31 Dec 2025 23:59:59 GMT
   Link: <https://api.example.com/v2/users>; rel="successor-version"

2. Log deprecated endpoint usage (by client)
3. Notify API consumers 6 months before sunset
4. Remove after sunset date
```

---

## Checklist de Design de API

```markdown
### Contract
- [ ] Contract defined first (OpenAPI / Protobuf / GraphQL schema)
- [ ] Breaking changes documented vs non-breaking
- [ ] Versioning strategy decided and documented

### REST
- [ ] Resource names are nouns, plural
- [ ] HTTP methods used correctly (GET safe, PUT idempotent)
- [ ] HTTP status codes are accurate
- [ ] Error responses follow standard format
- [ ] Pagination implemented (cursor-based for large collections)

### Security
- [ ] Authentication documented (Bearer, API key, OAuth2)
- [ ] Authorization checked at each endpoint
- [ ] Rate limiting configured
- [ ] Input validation on all parameters
- [ ] Sensitive fields never in URLs (use POST body or headers)

### Reliability
- [ ] Idempotency key for mutation endpoints
- [ ] Retry-After header for 429 responses
- [ ] Timeout documentation
- [ ] Maximum response payload documented

### Developer Experience
- [ ] Example requests and responses in spec
- [ ] Error codes documented with explanations
- [ ] Changelog for API versions
- [ ] SDK or code examples for common languages
```

---

