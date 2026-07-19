# Padrões de Teste de Integração

## Dependências Reais vs Mocks -- Matriz de Decisão

| Dependência | Real | Mock | Justificativa |
|------------|------|------|-----------|
| PostgreSQL | testcontainers | -- | O comportamento de queries difere entre o DB real e o mock |
| Redis | testcontainers | -- | Comportamento de TTL e pub/sub precisa do Redis real |
| MongoDB | testcontainers | -- | O pipeline de agregação precisa do engine real |
| RabbitMQ/Kafka | testcontainers | -- | Ordenação de mensagens e comportamento de ack |
| Stripe/PayPal | -- | respx/httpx mock | Rate limits, custo, determinismo |
| Email (SMTP) | -- | mock | Sem e-mail real nos testes |
| S3 | localstack | -- | Operações de arquivo precisam de armazenamento próximo do real |
| APIs REST externas | -- | respx/wiremock | Você não as controla |

## Padrões do Testcontainers

### PostgreSQL

```python
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest.fixture(scope="session")
def db_url(postgres):
    return postgres.get_connection_url()
```

### Redis

```python
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def redis():
    with RedisContainer("redis:7-alpine") as r:
        yield r

@pytest.fixture
def redis_client(redis):
    import redis as r
    client = r.from_url(redis.get_connection_url())
    yield client
    client.flushdb()
```

## Mocking HTTP com respx

```python
import httpx
import respx

@pytest.fixture
def mock_stripe():
    with respx.mock:
        respx.post("https://api.stripe.com/v1/charges").mock(
            return_value=httpx.Response(200, json={
                "id": "ch_test_123",
                "status": "succeeded",
                "amount": 5000,
            })
        )
        yield

async def test_payment_success(client, mock_stripe, sample_order):
    response = await client.post(f"/orders/{sample_order.id}/pay")
    assert response.status_code == 200
    assert response.json()["payment_status"] == "succeeded"
```

## Testes de Integração com FastAPI

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client(db_session):
    """Test client with real database, mocked external services."""
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

async def test_create_user(client):
    response = await client.post("/users", json={
        "name": "Alice",
        "email": "alice@test.com",
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Alice"

async def test_create_user_duplicate_email(client, existing_user):
    response = await client.post("/users", json={
        "name": "Bob",
        "email": existing_user.email,  # duplicate
    })
    assert response.status_code == 409
```

## Regras de Escopo

Cada teste de integração valida **um ponto de integração**:

```
GOOD: API endpoint + database
GOOD: Service + cache
GOOD: Service + message queue
GOOD: Service + external API (mocked)

BAD:  API + database + cache + queue + external API  (that is E2E)
```

## Asserções

```python
# Assert on HTTP response
assert response.status_code == 200
assert response.json()["id"] is not None

# Assert on database side effect
user = db_session.query(User).filter_by(email="alice@test.com").one()
assert user.name == "Alice"

# Assert on cache side effect
cached = redis_client.get(f"user:{user.id}")
assert cached is not None

# Assert on mock interactions
assert mock_stripe.calls.call_count == 1
```
