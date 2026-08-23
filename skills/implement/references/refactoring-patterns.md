# Padrões de Refactoring

## Árvore de Decisão

```
What are you refactoring?
  |
  +-- Entire system/component? --> Strangler Fig
  |
  +-- Deep internal component with upstream callers? --> Branch by Abstraction
  |
  +-- Public API/interface with multiple consumers? --> Parallel Change
  |
  +-- Large change with unknown dependency graph? --> Mikado Method
  |
  +-- Small code smell in current file? --> Direct refactor (RED-GREEN-REFACTOR)
```

## 1. Strangler Fig Pattern

**Nomeado a partir de:** Martin Fowler, 2004. Inspirado nas figueiras-estranguladoras que crescem em volta de uma árvore hospedeira.

**Quando:** Substituir um grande sistema ou componente legado de forma incremental.

**Passos:**
```
1. IDENTIFY   — Choose one feature/route/API to migrate
2. BUILD      — Create new implementation alongside old
3. ROUTE      — Redirect traffic/calls to new implementation
4. VERIFY     — Monitor new implementation in production
5. REPEAT     — Next feature/route/API
6. REMOVE     — Delete old code when fully migrated
```

**Padrões de implementação:**

### Abordagem Facade/Router
```python
class OrderRouter:
    """Routes to old or new implementation based on feature flag."""

    def __init__(self, legacy: LegacyOrderService, modern: ModernOrderService):
        self._legacy = legacy
        self._modern = modern

    async def create_order(self, request: OrderRequest) -> Order:
        if feature_flags.is_enabled("modern_orders"):
            return await self._modern.create_order(request)
        return await self._legacy.create_order(request)
```

### Deslocamento gradual de tráfego
```
Week 1: 1% traffic to new system (canary)
Week 2: 10% traffic (validate metrics)
Week 3: 50% traffic (load test)
Week 4: 100% traffic (full migration)
Week 5: Remove old code
```

**Regras-chave:**
- Sempre tenha um mecanismo de rollback (feature flag, reverse proxy)
- Monitore ambas as implementações lado a lado
- Complete a migração — não deixe duas implementações para sempre
- Cada passo da migração deve ser deployável de forma independente

---

## 2. Branch by Abstraction

**Quando:** Refatorar um componente fundo na stack que tem muitos callers upstream.

**Passos:**
```
1. ABSTRACT  — Create an interface/protocol for the component
2. ADAPT     — Make the old component implement the interface
3. MIGRATE   — Change all callers to use the interface
4. IMPLEMENT — Build the new component behind the interface
5. SWITCH    — Point the interface to the new implementation
6. CLEAN     — Remove the old component and the abstraction (if no longer needed)
```

**Exemplo:**

```python
# Step 1: Create abstraction
class NotificationSender(Protocol):
    async def send(self, user_id: str, message: str) -> None: ...

# Step 2: Old implementation adopts the interface
class EmailNotifier:  # already implements the protocol
    async def send(self, user_id: str, message: str) -> None:
        # ... sends email ...

# Step 3: Callers use the interface (dependency injection)
class OrderService:
    def __init__(self, notifier: NotificationSender):
        self._notifier = notifier

# Step 4: Build new implementation
class SlackNotifier:
    async def send(self, user_id: str, message: str) -> None:
        # ... sends Slack message ...

# Step 5: Switch injection
# In DI container: bind NotificationSender -> SlackNotifier

# Step 6: Remove EmailNotifier
```

**Diferença-chave em relação ao Strangler Fig:**
- Strangler Fig atua no **perímetro** (rotas de API, endpoints)
- Branch by Abstraction atua **fundo na stack** (componentes internos)

---

## 3. Parallel Change (Expand-Migrate-Contract)

**Quando:** Mudar uma API ou interface pública que tem múltiplos consumidores.

**As três fases:**

### Fase 1: EXPAND
Adicione a nova interface ao lado da antiga. Ambas funcionam. Nada quebra.

```python
class UserService:
    # OLD — keep it working
    def get_user(self, user_id: int) -> dict:
        user = self._repo.find(user_id)
        return {"id": user.id, "name": user.name}

    # NEW — add alongside
    def get_user_v2(self, user_id: str) -> UserResponse:
        user = self._repo.find_by_uuid(user_id)
        return UserResponse(id=user.uuid, name=user.name)
```

### Fase 2: MIGRATE
Mova os consumidores um a um para a nova interface.

```python
# Before: consumer uses old API
user_data = user_service.get_user(42)

# After: consumer uses new API
user = user_service.get_user_v2("uuid-123")
```

### Fase 3: CONTRACT
Uma vez que todos os consumidores tenham migrado, remova a interface antiga.

```python
class UserService:
    # Only new API remains
    def get_user(self, user_id: str) -> UserResponse:
        user = self._repo.find_by_uuid(user_id)
        return UserResponse(id=user.uuid, name=user.name)
```

**Regra-chave:** Cada fase é um commit/PR separado e deployável.

---

## 4. Mikado Method

**Quando:** Refactoring grande onde as dependências não estão claras.

**O algoritmo:**
```
1. Set the goal (e.g., "replace ORM X with ORM Y")
2. Try to implement the goal directly
3. If it compiles and tests pass → DONE
4. If it breaks:
   a. Note what broke (the prerequisite)
   b. REVERT your change
   c. Add the prerequisite to your Mikado Graph
   d. Set the prerequisite as the new goal
   e. Go to step 2
5. When a leaf goal succeeds, commit it
6. Work back up the graph until the root goal succeeds
```

**Exemplo de Mikado Graph:**
```
Replace ORM X with ORM Y (ROOT GOAL)
  |
  +-- Update UserRepository to use ORM Y
  |     |
  |     +-- Create ORM Y session factory
  |     +-- Update User model to ORM Y format
  |
  +-- Update OrderRepository to use ORM Y
  |     |
  |     +-- Update Order model to ORM Y format
  |     +-- Update migration scripts
  |
  +-- Remove ORM X dependency from requirements.txt
```

**Benefícios-chave:**
- Descobre o verdadeiro grafo de dependências por experimentação
- Cada commit é pequeno e seguro (uma folha por vez)
- Ordenação natural — você sempre corrige os pré-requisitos antes do objetivo
- Cultura de reverter primeiro — nunca deixe o codebase quebrado

---

## Regras de Segurança para Todo Refactoring

1. **Testes primeiro** — Nunca refatore sem testes. Se não existirem testes, adicione characterization tests primeiro.
2. **Passos pequenos** — Cada passo é deployável e testável de forma independente.
3. **Uma coisa por vez** — Nunca misture refactoring com trabalho de feature no mesmo commit.
4. **Verifique a cada passo** — Rode a suíte de testes completa após cada mudança.
5. **Plano de rollback** — Sempre saiba como reverter se algo der errado.
