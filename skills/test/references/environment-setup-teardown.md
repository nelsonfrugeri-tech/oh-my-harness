# Configuração e Teardown de Ambiente

## Ciclo de Vida

```
PROVISION -> CONFIGURE -> SEED -> TEST -> TEARDOWN -> VERIFY CLEAN
```

## Padrões de Docker Compose

### Arquivo Compose Específico de Teste

Sempre use um `docker-compose.test.yml` separado -- nunca compartilhe com o de desenvolvimento.

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"       # different port from dev
    tmpfs:
      - /var/lib/postgresql/data  # RAM disk -- 10x faster

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"       # different port from dev
    command: redis-server --save ""  # disable persistence

  localstack:
    image: localstack/localstack:3
    ports:
      - "4566:4566"
    environment:
      SERVICES: s3,sqs,sns
      DEFAULT_REGION: us-east-1
```

### Script de Inicialização

```bash
#!/usr/bin/env bash
set -euo pipefail

# Start test dependencies
docker compose -f docker-compose.test.yml up -d --wait

# Run migrations
DATABASE_URL="postgresql://test:test@localhost:5433/test_db" alembic upgrade head

# Run tests
pytest "$@"

# Teardown
docker compose -f docker-compose.test.yml down -v --remove-orphans
```

## Testcontainers (Python)

### Containers com Escopo de Sessão

```python
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.mongodb import MongoDbContainer

@pytest.fixture(scope="session")
def postgres_url():
    with PostgresContainer(
        image="postgres:16-alpine",
        dbname="test_db",
    ) as pg:
        yield pg.get_connection_url()

@pytest.fixture(scope="session")
def redis_url():
    with RedisContainer(image="redis:7-alpine") as r:
        yield r.get_connection_url()

@pytest.fixture(scope="session")
def mongo_url():
    with MongoDbContainer(image="mongo:7") as m:
        yield m.get_connection_url()
```

### Isolamento por Teste via Transações

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture(scope="session")
def engine(postgres_url):
    eng = create_engine(postgres_url)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()

@pytest.fixture
def db(engine):
    """Each test gets a transaction that rolls back."""
    conn = engine.connect()
    txn = conn.begin()
    session = Session(bind=conn)
    yield session
    session.close()
    txn.rollback()
    conn.close()
```

## Padrões de Teardown

### Rollback de Transação (preferido por velocidade)

```python
@pytest.fixture(autouse=True)
def rollback(db_session):
    yield
    db_session.rollback()
```

### Truncamento de Tabelas (quando o rollback não é possível)

```python
@pytest.fixture(autouse=True)
def truncate_tables(db_engine):
    yield
    with db_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()
```

### Flush do Redis

```python
@pytest.fixture(autouse=True)
def flush_redis(redis_client):
    yield
    redis_client.flushdb()
```

### Arquivos Temporários

```python
import tempfile
from pathlib import Path

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
    # automatically cleaned up
```

## Variáveis de Ambiente

```python
@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Ensure tests do not leak environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5433/test_db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6380/0")
    monkeypatch.setenv("ENV", "test")
```

## Verificação

Após o teardown, verifique o estado limpo:

```python
def test_no_leaked_data(db_session):
    """Canary test: verify previous tests cleaned up."""
    count = db_session.execute(text("SELECT COUNT(*) FROM users")).scalar()
    assert count == 0, "Previous test leaked data"
```
