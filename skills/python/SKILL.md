---
version: 1.0.0
name: python
description: |
  Base de conhecimento de Python (2026). Abrange o sistema de tipos moderno do Python (Protocol, TypeVar, Generic,
  Literal, TypedDict, sintaxe de union), async/await e modelos de concorrência (asyncio, threading,
  multiprocessing), dataclasses (frozen, slots), context managers, decorators, Pydantic v2
  (validators, computed fields), hierarquias de tratamento de erros, logging estruturado com structlog,
  gerenciamento de configuração com pydantic-settings, generators e avaliação preguiçosa, empacotamento moderno
  (pyproject.toml) e ferramentas essenciais (ruff, black, mypy, pytest, pre-commit).
  Use quando: (1) Escrever ou revisar código Python, (2) Escolher padrões para segurança de tipos, I/O assíncrona,
  tratamento de erros ou testes, (3) Configurar ferramentas de Python, (4) Projetar modelos ou configs Pydantic.
  Triggers: /python, python, type hints, pydantic, async, pytest, structlog, fastapi, mypy.
type: knowledge
---

# Python — Base de Conhecimento

## Objetivo

Esta skill é a base de conhecimento para engenharia moderna de Python (2026).
Abrange padrões idiomáticos, segurança de tipos, I/O assíncrona, testes e ferramentas.

**O que esta skill contém:**
- Sistema de tipos (Protocol, TypeVar, Generic, Literal, TypedDict)
- Async/await e concorrência (asyncio, threading, multiprocessing)
- Dataclasses (frozen, slots, field defaults)
- Context managers (@contextmanager, __enter__/__exit__)
- Decorators (functools.wraps, cache, decorators customizados)
- Pydantic v2 (validação, computed fields, settings)
- Tratamento de erros (hierarquias customizadas, tratamento explícito de exceções)
- Logging estruturado com structlog
- Gerenciamento de configuração com pydantic-settings
- Generators e avaliação preguiçosa
- Empacotamento moderno (pyproject.toml, Poetry)
- Ferramentas essenciais (ruff, black, mypy, pytest, pre-commit)

---

## Princípios Fundamentais

1. **Explícito acima de implícito** — type hints em toda assinatura de função, sem Any implícito
2. **Falhe rápido** — valide nas fronteiras (Pydantic), lance exceções customizadas
3. **Async por padrão para I/O** — asyncio para chamadas de rede, arquivos e banco de dados
4. **Teste tudo** — pytest com fixtures e parametrize, 100% de cobertura nos caminhos críticos
5. **Formato: Black + 88 chars** — aspas duplas, trailing commas em estruturas multilinha

---

## 1. Sistema de Tipos

### Sintaxe Básica (Python 3.10+)

```python
from typing import Protocol, TypeVar, Generic, Literal, TypedDict
from collections.abc import Iterator, AsyncIterator

# Union with | (PEP 604, Python 3.10+)
def greet(name: str | None = None) -> str:
    return f"Hello, {name or 'World'}"

# TypedDict for typed dicts
class Config(TypedDict):
    host: str
    port: int
    debug: bool

# Literal for specific values
Status = Literal["pending", "active", "done", "failed"]
```

### Protocol — Structural Subtyping

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Readable(Protocol):
    def read(self) -> str: ...

class FileSource:
    def read(self) -> str:
        return open("data.txt").read()

class HttpSource:
    def read(self) -> str:
        return requests.get("https://example.com").text

def process(source: Readable) -> str:
    return source.read().upper()

# Both work — no inheritance required
process(FileSource())
process(HttpSource())
```

### TypeVar e Generic

```python
from typing import TypeVar, Generic

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self._value = value

    def get(self) -> T:
        return self._value

    def map(self, fn: Callable[[T], V]) -> "Container[V]":
        return Container(fn(self._value))

# Usage: fully typed
num: Container[int] = Container(42)
text: Container[str] = num.map(str)
```

### Type Aliases

```python
from typing import TypeAlias

UserId: TypeAlias = str
OrderId: TypeAlias = str
Price: TypeAlias = float

# NewType for stronger typing
from typing import NewType
UserId = NewType("UserId", str)
OrderId = NewType("OrderId", str)

user_id = UserId("usr_123")
order_id = OrderId("ord_456")
# user_id == order_id → type error (mypy catches this)
```

**Referência:** [references/type-system.md](references/type-system.md)

---

## 2. Async/Await

### Quando Usar Async

| Carga de trabalho | Modelo | Por quê |
|----------|-------|-----|
| Chamadas HTTP, queries de DB | asyncio | Não bloqueante, thread única |
| I/O bloqueante legada | threading | O GIL não bloqueia I/O |
| Computação CPU-bound | multiprocessing | Contorna o GIL |

### Padrões Async

```python
import asyncio
import httpx

async def fetch(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()

# Parallel execution
async def fetch_all(urls: list[str]) -> list[dict]:
    return await asyncio.gather(*[fetch(url) for url in urls])

# With error handling per task
async def fetch_safe(url: str) -> dict | None:
    try:
        return await fetch(url)
    except httpx.HTTPError:
        return None

async def fetch_all_safe(urls: list[str]) -> list[dict | None]:
    tasks = [fetch_safe(url) for url in urls]
    return await asyncio.gather(*tasks)
```

### Async Context Manager

```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

@asynccontextmanager
async def managed_db_connection(dsn: str) -> AsyncIterator[Connection]:
    conn = await asyncpg.connect(dsn)
    try:
        yield conn
    finally:
        await conn.close()

async def main() -> None:
    async with managed_db_connection("postgresql://...") as conn:
        rows = await conn.fetch("SELECT * FROM users")
```

### Async Generator

```python
async def paginated_fetch(base_url: str) -> AsyncIterator[dict]:
    page = 1
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(f"{base_url}?page={page}")
            data = response.json()
            if not data["items"]:
                break
            for item in data["items"]:
                yield item
            page += 1

async def main() -> None:
    async for item in paginated_fetch("https://api.example.com/items"):
        print(item)
```

**Referência:** [references/async-patterns.md](references/async-patterns.md)

---

## 3. Dataclasses

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float
    label: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    def distance_from_origin(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5

@dataclass
class Order:
    id: str
    items: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    total: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Order id cannot be empty")
```

### Dataclass vs Pydantic

| Caso de uso | Dataclass | Pydantic |
|----------|-----------|---------|
| Estruturas de dados internas | Sim | Exagero |
| Dados externos (API, config) | Não — sem validação | Sim |
| Serialização/desserialização | Manual | Integrado |
| Desempenho (sem validação) | Mais rápido | Levemente mais lento |

**Referência:** [references/dataclasses.md](references/dataclasses.md)

---

## 4. Context Managers

```python
from contextlib import contextmanager, suppress
from typing import Iterator

@contextmanager
def transaction(conn: Connection) -> Iterator[Connection]:
    """Commit on success, rollback on any exception."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise

# suppress specific exceptions
with suppress(FileNotFoundError):
    os.remove("temp.txt")

# Class-based (when you need __enter__ return value)
class Timer:
    def __enter__(self) -> "Timer":
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        self.elapsed = time.perf_counter() - self.start

with Timer() as t:
    do_work()
print(f"Elapsed: {t.elapsed:.3f}s")
```

**Referência:** [references/context-managers.md](references/context-managers.md)

---

## 5. Decorators

```python
import functools
import time
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")

def retry(times: int = 3, delay: float = 1.0) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorator with configurable attempts and delay."""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: Exception | None = None
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_error = exc
                    if attempt < times - 1:
                        time.sleep(delay)
            raise last_error  # type: ignore[misc]
        return wrapper
    return decorator

@retry(times=3, delay=0.5)
def call_external_api(endpoint: str) -> dict:
    return requests.get(endpoint).json()

# functools.cache for memoization (Python 3.9+)
@functools.cache
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

**Referência:** [references/decorators.md](references/decorators.md)

---

## 6. Pydantic v2

### Modelos e Validação

```python
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field
from pydantic import EmailStr, HttpUrl
from typing import Annotated

PositiveInt = Annotated[int, Field(gt=0)]

class Address(BaseModel):
    street: str
    city: str
    country: str = "US"

class User(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: PositiveInt
    address: Address | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip().title()

    @computed_field
    @property
    def is_adult(self) -> bool:
        return self.age >= 18

    @model_validator(mode="after")
    def validate_adult_address(self) -> "User":
        if self.is_adult and self.address is None:
            raise ValueError("Adult users must provide an address")
        return self

# Serialization
user = User(name="alice", email="alice@example.com", age=25)
print(user.model_dump())          # dict
print(user.model_dump_json())     # JSON string
user_copy = user.model_copy(update={"age": 26})
```

### Strict Mode

```python
class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True)

    count: int
    value: float

# Strict: no coercion
StrictModel(count="5", value="3.14")  # ValidationError — no coercion in strict mode
StrictModel(count=5, value=3.14)      # OK
```

**Referência:** [references/pydantic.md](references/pydantic.md)

---

## 7. Tratamento de Erros

### Hierarquia de Exceções Customizada

```python
class AppError(Exception):
    """Base exception for all application errors."""

class ValidationError(AppError):
    """Raised when input data validation fails."""

class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource} with id '{identifier}' not found")
        self.resource = resource
        self.identifier = identifier

class ConflictError(AppError):
    """Raised when an operation conflicts with current state."""

class ExternalServiceError(AppError):
    """Raised when an external dependency fails."""

    def __init__(self, service: str, cause: Exception) -> None:
        super().__init__(f"External service '{service}' failed: {cause}")
        self.service = service
        self.__cause__ = cause
```

### Regras

```python
# GOOD: catch specific, re-raise with context
try:
    user = await user_repo.get(user_id)
except DatabaseError as exc:
    raise ExternalServiceError("database", exc) from exc

# GOOD: never swallow exceptions silently
try:
    result = risky_operation()
except SpecificError:
    logger.warning("operation_failed", reason="expected case")
    result = fallback_value

# BAD: bare except catches everything including KeyboardInterrupt
# except:  # never do this

# BAD: swallowing the exception
# except Exception:
#     pass
```

**Referência:** [references/error-handling.md](references/error-handling.md)

---

## 8. Logging Estruturado

```python
import structlog
from opentelemetry import trace

def add_trace_context(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add OpenTelemetry trace context to every log entry."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_trace_context,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
)

logger = structlog.get_logger()

# Bind context once, reuse throughout the request
def process_order(order_id: str, user_id: str) -> None:
    log = logger.bind(order_id=order_id, user_id=user_id)
    log.info("processing_started")
    try:
        result = do_work(order_id)
        log.info("processing_completed", status="success", result_count=len(result))
    except Exception as exc:
        log.error("processing_failed", error=str(exc), exc_info=True)
        raise
```

**Referência:** [references/logging.md](references/logging.md)

---

## 9. Gerenciamento de Configuração

```python
from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: PostgresDsn
    db_pool_size: int = Field(default=10, ge=1, le=100)

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")  # type: ignore

    # Application
    debug: bool = False
    log_level: str = "info"
    secret_key: str = Field(min_length=32)

    # Derived
    @property
    def is_production(self) -> bool:
        return not self.debug

# Singleton — create once, import everywhere
settings = Settings()
```

**Referência:** [references/configuration.md](references/configuration.md)

---

## 10. Generators e Avaliação Preguiçosa

```python
from typing import Iterator, Generator
from pathlib import Path

def read_chunks(path: Path, size: int = 8192) -> Iterator[str]:
    """Read file in chunks — constant memory regardless of file size."""
    with open(path) as f:
        while chunk := f.read(size):
            yield chunk

def process_lines(path: Path) -> Iterator[str]:
    """Pipeline: read → split → filter → transform."""
    for chunk in read_chunks(path):
        for line in chunk.splitlines():
            if line.strip():
                yield line.upper()

# Generator expression (lazy)
total = sum(len(line) for line in process_lines(Path("data.txt")))

# itertools for composable pipelines
import itertools

def batch(iterable: Iterator[T], size: int) -> Iterator[list[T]]:
    it = iter(iterable)
    while batch := list(itertools.islice(it, size)):
        yield batch
```

**Referência:** [references/generators.md](references/generators.md)

---

## 11. Testes com pytest

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Fixtures
@pytest.fixture
def db_session(postgresql):
    """Fixture providing a real DB session via pytest-postgresql."""
    session = SessionLocal(bind=postgresql)
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def mock_http_client():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    return client

# Parametrize
@pytest.mark.parametrize(
    "price, discount, expected",
    [
        (100.0, 0.1, 90.0),
        (50.0, 0.2, 40.0),
        (0.0, 0.5, 0.0),
    ],
)
def test_apply_discount(price: float, discount: float, expected: float) -> None:
    result = apply_discount(price, discount)
    assert result == pytest.approx(expected)

# Async tests
@pytest.mark.asyncio
async def test_fetch_user(mock_http_client: AsyncMock) -> None:
    mock_http_client.get.return_value.json.return_value = {"id": "1", "name": "Alice"}
    user = await fetch_user("1", client=mock_http_client)
    assert user.name == "Alice"
    mock_http_client.get.assert_awaited_once_with("/users/1", timeout=10.0)

# Exception testing
def test_not_found_raises() -> None:
    with pytest.raises(NotFoundError) as exc_info:
        get_user("nonexistent")
    assert exc_info.value.identifier == "nonexistent"
    assert "User" in str(exc_info.value)
```


---

## 12. Ferramentas Essenciais

| Categoria | Ferramenta | Propósito | Comando |
|----------|------|---------|---------|
| Lint | **ruff** | Linter ultrarrápido | `ruff check . --fix` |
| Format | **black** | Formatador opinativo | `black .` |
| Types | **mypy** | Verificador estático de tipos | `mypy src/` |
| Test | **pytest** | Framework de testes | `pytest` |
| Coverage | **pytest-cov** | Relatórios de cobertura | `pytest --cov=src --cov-report=term-missing` |
| Hooks | **pre-commit** | Git hooks | `pre-commit install` |
| Deps | **Poetry** | Gerenciamento de dependências | `poetry install` |

### pyproject.toml

```toml
[project]
name = "mypackage"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pydantic==2.11.3",
    "pydantic-settings==2.9.1",
    "structlog==25.1.0",
    "httpx==0.28.1",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.5",
    "pytest-asyncio==0.25.3",
    "pytest-cov==6.1.0",
    "mypy==1.15.0",
    "ruff==0.11.5",
    "black==25.1.0",
    "pre-commit==4.2.0",
]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "ANN", "S", "B", "A", "C4", "PT"]

[tool.mypy]
strict = true
python_version = "3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*"]
```


---

## Arquivos de Referência

- [references/async-patterns.md](references/async-patterns.md) — Padrões de Async/Await - Python 3.10+
- [references/concurrency.md](references/concurrency.md) — Concorrência - Python 3.10+
- [references/configuration.md](references/configuration.md) — configuration.md
- [references/context-managers.md](references/context-managers.md) — Context Managers - Python 3.10+
- [references/dataclasses.md](references/dataclasses.md) — Data Classes - Python 3.10+
- [references/decorators.md](references/decorators.md) — Decorators - Python 3.10+
- [references/error-handling.md](references/error-handling.md) — Tratamento de Erros - Python 3.10+
- [references/generators.md](references/generators.md) — Generators e Avaliação Preguiçosa - Python 3.10+
- [references/logging.md](references/logging.md) — Logging Estruturado - Python 3.10+
- [references/packaging.md](references/packaging.md) — Python Packaging - Python 3.10+
- [references/pydantic.md](references/pydantic.md) — Pydantic v2 - Python 3.10+
- [references/type-system.md](references/type-system.md) — Sistema de Tipos Avançado - Python 3.10+