---
version: 1.0.0
name: environment
description: |
  Base de conhecimento de ambiente de desenvolvimento local (2026). Cobre o ciclo de vida do
  ambiente, boas práticas de Docker (multi-stage builds, layer caching, segurança), padrões de
  Docker Compose (health checks, depends_on, volumes, profiles, watch mode), inicialização de
  bancos de dados (PostgreSQL, MongoDB, Redis — init scripts, seeding, migrations), gerenciamento
  de .env, orquestração de serviços (ordem de inicialização, readiness probes), gerenciamento de
  portas, hot reload, instalação de dependências por ecossistema (pip, poetry, npm, pnpm), teardown
  e recuperação de erros.
  Use quando: (1) Configurar o ambiente local com Docker, (2) Configurar bancos de dados,
  (3) Diagnosticar a infraestrutura local, (4) Orquestrar stacks multi-serviço,
  (5) Depurar containers.
  Triggers: /environment, /env, docker, compose, database setup, container, devenv, local infra.
type: capability
---

# Environment — Infraestrutura de Desenvolvimento Local

## Propósito

Esta skill é a base de conhecimento para infraestrutura de desenvolvimento local (2026).
Ela cobre tudo o que é necessário para executar, depurar e manter ambientes de desenvolvimento multi-serviço.

**O que esta skill contém:**
- Boas práticas de Docker (multi-stage builds, segurança, layer caching)
- Padrões de Docker Compose (health checks, depends_on, volumes, networks)
- Setup de bancos de dados (PostgreSQL, MongoDB, Redis)
- Gerenciamento de .env (validação, templates, secrets)
- Orquestração de serviços (ordem de inicialização, readiness probes)
- Gerenciamento de portas e resolução de conflitos
- Instalação de dependências por ecossistema
- Streaming de logs e debugging
- Watch mode e hot reload
- Procedimentos de recuperação de erros

**O que esta skill NÃO contém:**
- Deploy em cloud (AWS, GCP, Azure) — o foco é local
- Kubernetes / Helm — o foco é Docker Compose
- Pipelines de CI/CD — o foco é a estação de trabalho do desenvolvedor

---

## Versões de Referência

> Sempre verifique as versões atuais antes de usar. Confira nos sites oficiais (Docker Hub, PyPI, npmjs.com, etc.)

| Ferramenta | Versão | Notas |
|------|---------|-------|
| Docker Engine | 29.3.1 | Última estável |
| Docker Compose | v2.40+ | Plugin de CLI, sem necessidade do campo `version:` |
| PostgreSQL | 18.3 | Última estável |
| MongoDB | 8.2.3 | Última estável |
| Redis | 8.4.2 | Última estável |
| Python | 3.14.3 | Última estável |
| Node.js | 24.14.1 | LTS |
| Poetry | 2.3.3 | Última estável |
| pnpm | 10.33.0 | Última estável |

---

## 1. Boas Práticas de Docker

### Multi-Stage Builds

Multi-stage builds reduzem o tamanho da imagem em até 97%.

```dockerfile
# Stage 1: Build
FROM python:3.14.3-slim AS builder
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry==2.3.3 && \
    poetry config virtualenvs.in-project true && \
    poetry install --only=main --no-interaction
COPY src/ ./src/

# Stage 2: Runtime
FROM python:3.14.3-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
ENV PATH="/app/.venv/bin:$PATH"
USER nobody
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Layer Caching

Ordene as instruções da que muda com menos frequência para a que muda com mais frequência:

```dockerfile
# 1. Base image (rarely changes)
FROM node:24.14.1-slim

# 2. System deps (rarely changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

# 3. Dependency files (changes when deps change)
COPY package.json pnpm-lock.yaml ./

# 4. Install deps (cached if lockfile unchanged)
RUN corepack enable && pnpm install --frozen-lockfile

# 5. Source code (changes frequently)
COPY src/ ./src/
```

### Segurança

```dockerfile
# Use minimal base images
FROM python:3.14.3-slim          # NOT python:3.14.3
FROM node:24.14.1-slim           # NOT node:24.14.1

# Run as non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# .dockerignore
# .git
# node_modules
# .env
# __pycache__
# .mypy_cache
# .pytest_cache
```

### Seleção de Imagem

| Caso de Uso | Imagem Base | Tamanho |
|----------|-----------|------|
| Python em produção | `python:3.14.3-slim` | ~150MB |
| Python mínimo | `python:3.14.3-alpine` | ~50MB |
| Node.js em produção | `node:24.14.1-slim` | ~200MB |
| Segurança máxima | `gcr.io/distroless/python3` | ~30MB |

---

## 2. Padrões de Docker Compose

### Dependências de Serviço com Health Checks

```yaml
# compose.yaml (no `version:` field -- deprecated in Compose v2)
services:
  postgres:
    image: postgres:18
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts/postgres:/docker-entrypoint-initdb.d
    ports:
      - "${DB_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s

  redis:
    image: redis:8.4.2-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "${REDIS_PORT:-6379}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file: .env
    ports:
      - "${API_PORT:-8000}:8000"
    volumes:
      - ./src:/app/src:ro
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s

volumes:
  postgres_data:
  redis_data:
```

### Profiles para Serviços Opcionais

```yaml
services:
  api:
    # ... always runs

  adminer:
    image: adminer:4.8.1
    ports:
      - "8080:8080"
    profiles: ["debug"]

  prometheus:
    image: prom/prometheus:v3.2.1
    profiles: ["monitoring"]
```

```bash
docker compose up                        # core services only
docker compose --profile debug up        # with debug tools
docker compose --profile monitoring up   # with monitoring
```

### Watch Mode (hot reload, Compose v2.22+)

```yaml
services:
  api:
    build: .
    develop:
      watch:
        - action: sync
          path: ./src
          target: /app/src
        - action: rebuild
          path: ./pyproject.toml
        - action: sync+restart
          path: ./config
          target: /app/config
```

```bash
docker compose watch  # auto-sync files, rebuild on dependency changes
```

---

## 3. Configuração de Banco de Dados

### PostgreSQL — Scripts de Inicialização

Arquivos em `/docker-entrypoint-initdb.d/` são executados no primeiro start (ordem alfabética):

```sql
-- init-scripts/postgres/01-extensions.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

```sql
-- init-scripts/postgres/02-schema.sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);
```

```bash
# init-scripts/postgres/03-seed.sh
#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    INSERT INTO users (email, name) VALUES
    ('admin@example.com', 'Admin User')
    ON CONFLICT (email) DO NOTHING;
EOSQL
```

### Redis

```bash
# Check Redis is up and auth working
docker exec <container> redis-cli -a ${REDIS_PASSWORD} ping

# Monitor commands in real-time
docker exec <container> redis-cli -a ${REDIS_PASSWORD} monitor

# Flush all keys (for test reset)
docker exec <container> redis-cli -a ${REDIS_PASSWORD} flushall
```

---

## 4. Gerenciamento de .env

### Template .env.example

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=postgres
DB_PASSWORD=                    # Required: set before running

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=                 # Required: set before running

# Application
API_PORT=8000
DEBUG=false
LOG_LEVEL=info

# External services
STRIPE_API_KEY=                 # Required for payment features
SENDGRID_API_KEY=               # Required for email features
```

### Validação de .env (Python — pydantic-settings)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str

    # Application
    debug: bool = False
    log_level: str = "info"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()
```

### Regras

1. **Nunca faça commit do `.env`** — adicione ao `.gitignore`
2. **Sempre faça commit do `.env.example`** — template com valores vazios
3. **Valide no startup** — use pydantic-settings ou dotenv-vault
4. **Nunca logue variáveis de ambiente** — elas contêm secrets

---

## 5. Readiness Probes de Serviço

### Aguardando Serviços em Scripts

```bash
#!/bin/bash
# Wait for PostgreSQL to be ready
until pg_isready -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER}; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done
echo "PostgreSQL is ready"

# Wait for API health check
until curl -sf http://localhost:${API_PORT}/health > /dev/null; do
  echo "Waiting for API..."
  sleep 2
done
echo "API is ready"
```

### Readiness em Python

```python
import asyncio
import httpx

async def wait_for_service(url: str, timeout: int = 30) -> None:
    """Wait for a service to become healthy."""
    start = asyncio.get_event_loop().time()
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(url, timeout=2.0)
                if response.status_code == 200:
                    return
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError(f"Service {url} not ready after {timeout}s")
            await asyncio.sleep(1)
```

---

## 6. Gerenciamento de Portas

### Atribuições Padrão de Portas

| Serviço | Porta Padrão | Override em Dev |
|---------|-------------|--------------|
| API | 8000 | Configurável via env |
| Frontend | 3000 | Configurável via env |
| PostgreSQL | 5432 | 5433 para teste |
| Redis | 6379 | 6380 para teste |
| MongoDB | 27017 | 27018 para teste |
| Adminer | 8080 | — |
| Prometheus | 9090 | — |
| Grafana | 3000 | 3001 (conflito com o frontend) |

### Resolução de Conflitos

```bash
# Find what is using a port
lsof -i :5432

# Kill process on port
kill -9 $(lsof -t -i:5432)

# Check all Docker-used ports
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

---

## 7. Instalação de Dependências

### Python — Poetry

```bash
# Install all deps
poetry install

# Install without dev deps (CI/production)
poetry install --only main

# Add dep (pinned)
poetry add requests==2.32.3

# Add dev dep
poetry add --group dev pytest==8.3.0

# Export for requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

### Node.js — pnpm

```bash
# Install all deps
pnpm install

# Install without dev deps
pnpm install --prod

# Add dep
pnpm add axios@1.7.0

# Add dev dep
pnpm add -D vitest@1.6.0

# Check for vulnerabilities
pnpm audit
```

---

## 8. Streaming de Logs e Debugging

### Logs de Container

```bash
# Follow logs for all services
docker compose logs -f

# Follow logs for specific service
docker compose logs -f api

# Show last 100 lines
docker compose logs --tail=100 api

# Filter by log level (if using structured logging)
docker compose logs api | grep '"level":"error"'
```

### Debugging Interativo

```bash
# Shell into running container
docker compose exec api bash

# Run one-off command
docker compose run --rm api python -c "from src.main import app; print('OK')"

# Check environment
docker compose exec api env | sort

# Inspect container
docker inspect $(docker compose ps -q api)
```

---

## 9. Teardown

### Shutdown Limpo

```bash
# Stop containers, keep volumes
docker compose down

# Stop containers, remove volumes
docker compose down -v

# Stop containers, remove everything (images + volumes)
docker compose down -v --rmi all

# Remove only stopped containers
docker compose rm --force --stop -v
```

### Limpeza Completa do Sistema

```bash
# Remove all unused containers, networks, images, volumes
docker system prune -a --volumes

# Remove only volumes
docker volume prune

# Remove only images
docker image prune -a
```

---

## 10. Recuperação de Erros

### Problemas Comuns e Soluções

**Porta já em uso:**
```bash
lsof -i :5432
kill -9 $(lsof -t -i:5432)
```

**Container não inicia (verifique os logs):**
```bash
docker compose logs <service>
docker compose events  # real-time event stream
```

**Conexão com o banco recusada:**
```bash
# Check if container is healthy
docker compose ps
# Check health logs
docker inspect <container_id> | jq '.[0].State.Health'
```

**Permissões de volume:**
```bash
# Fix file ownership issues
docker compose exec <service> chown -R <user>:<group> /path
```

**Sem espaço em disco:**
```bash
docker system df          # check usage
docker system prune -a    # clean up
```

---

## Reference Files

- [references/databases-setup-patterns.md](references/databases-setup-patterns.md) — Padrões de Setup de Banco de Dados
- [references/debugging-error-recovery.md](references/debugging-error-recovery.md) — Procedimentos de Recuperação de Erros
- [references/debugging-log-streaming.md](references/debugging-log-streaming.md) — Streaming de Logs e Debugging
- [references/docker-compose-patterns.md](references/docker-compose-patterns.md) — Padrões Avançados de Docker Compose
- [references/docker-dependency-installation.md](references/docker-dependency-installation.md) — Instalação de Dependências por Ecossistema
- [references/docker-dockerfile-patterns.md](references/docker-dockerfile-patterns.md) — Padrões de Dockerfile
- [references/orchestration-env-management.md](references/orchestration-env-management.md) — Gerenciamento de .env
- [references/orchestration-startup-order.md](references/orchestration-startup-order.md) — Ordem de Inicialização de Serviços