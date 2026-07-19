# Gerenciamento de Dados de Teste

## Abordagens

### 1. Fixtures (Dados Estáticos)

Melhor para: dados de referência, configuração, exemplos conhecidos como válidos.

```python
import pytest
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def valid_user_payload() -> dict:
    return {
        "name": "Alice Smith",
        "email": "alice@test.com",
        "role": "user",
    }

@pytest.fixture
def sample_products() -> list[dict]:
    return json.loads((FIXTURES_DIR / "products.json").read_text())
```

### 2. Factories (Dados Dinâmicos)

Melhor para: testes que precisam de muitas variações da mesma entidade.

```python
import factory
from factory import fuzzy

class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid4)
    name = factory.Faker("name")
    email = factory.LazyAttribute(
        lambda o: f"{o.name.lower().replace(' ', '.')}@test.com"
    )
    role = "user"
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)

class AdminFactory(UserFactory):
    role = "admin"

class InactiveUserFactory(UserFactory):
    is_active = False

# SQLAlchemy integration
class UserModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserModel
        sqlalchemy_session_persistence = "commit"

    # same fields as above
```

### 3. Builders (Grafos Complexos)

Melhor para: entidades com muitos relacionamentos.

```python
class OrderBuilder:
    def __init__(self) -> None:
        self._user = UserFactory()
        self._items: list[Product] = []
        self._discount = 0.0
        self._status = "pending"

    def with_user(self, user: User) -> "OrderBuilder":
        self._user = user
        return self

    def with_item(self, product: Product, qty: int = 1) -> "OrderBuilder":
        self._items.extend([product] * qty)
        return self

    def with_discount(self, pct: float) -> "OrderBuilder":
        self._discount = pct
        return self

    def with_status(self, status: str) -> "OrderBuilder":
        self._status = status
        return self

    def build(self) -> Order:
        return Order(
            user=self._user,
            items=self._items,
            discount=self._discount,
            status=self._status,
        )

# Usage
order = (OrderBuilder()
    .with_user(AdminFactory())
    .with_item(ProductFactory(price=50.0), qty=2)
    .with_discount(0.1)
    .build())
```

### 4. Seeding (Pré-População do Banco de Dados)

Melhor para: dados de referência compartilhados necessários a muitos testes.

```python
@pytest.fixture(scope="session")
def seed_reference_data(db_engine):
    """Seed data that all tests need (countries, currencies, roles)."""
    with Session(db_engine) as session:
        session.add_all([
            Role(name="admin"), Role(name="user"), Role(name="viewer"),
            Currency(code="USD"), Currency(code="EUR"), Currency(code="BRL"),
        ])
        session.commit()
```

## Estratégias de Limpeza

### Rollback de Transação (mais rápido)
```python
@pytest.fixture(autouse=True)
def auto_rollback(db_session):
    yield
    db_session.rollback()
```

### Truncation (quando o rollback não é possível)
```python
@pytest.fixture(autouse=True)
def truncate(db_engine):
    yield
    with db_engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE orders, users CASCADE"))
        conn.commit()
```

## Regras

1. **Cada teste cria seus próprios dados** -- nunca dependa do estado de outro teste
2. **Prefira factories a SQL puro** -- factories respeitam a validação do modelo
3. **Evite IDs sequenciais em asserções** -- use UUIDs ou consulte por atributo
4. **Nunca use dados de produção** -- apenas dados sintéticos
5. **Faça seed apenas de dados de referência/lookup** -- países, papéis, moedas
6. **Limpe após cada teste** -- rollback de transação é preferível
