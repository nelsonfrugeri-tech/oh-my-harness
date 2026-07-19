# Padrões Avançados de Docker Compose

## Redes

```yaml
services:
  api:
    networks:
      - backend
      - frontend

  postgres:
    networks:
      - backend  # not accessible from frontend network

  nginx:
    networks:
      - frontend
    ports:
      - "80:80"

networks:
  backend:
    driver: bridge
  frontend:
    driver: bridge
```

## Padrões de Volume

```yaml
volumes:
  # Named volume (persistent, managed by Docker)
  postgres_data:

  # Named volume with driver options
  redis_data:
    driver: local

services:
  api:
    volumes:
      # Bind mount (development: sync source code)
      - ./src:/app/src

      # Read-only bind mount (safer)
      - ./src:/app/src:ro

      # Named volume (persistent data)
      - postgres_data:/var/lib/postgresql/data

      # Anonymous volume (ephemeral)
      - /app/node_modules

      # tmpfs (in-memory, no persistence)
    tmpfs:
      - /tmp
```

## Limites de Recursos

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 512M
        reservations:
          cpus: "0.5"
          memory: 256M
```

## Políticas de Restart

```yaml
services:
  api:
    restart: unless-stopped   # restart unless manually stopped

  postgres:
    restart: always           # always restart

  migration:
    restart: "no"             # run once, don't restart
```

## Precedência de Variáveis de Ambiente

1. `environment:` no compose.yaml (maior precedência)
2. `env_file:` no compose.yaml
3. Variáveis de ambiente do shell
4. Arquivo `.env` na raiz do projeto (menor precedência)

## Estender e Sobrescrever

```yaml
# compose.yaml (base)
services:
  api:
    build: .
    ports:
      - "8000:8000"

# compose.override.yaml (auto-loaded in dev)
services:
  api:
    volumes:
      - ./src:/app/src
    environment:
      - DEBUG=true
    command: uvicorn src.main:app --reload

# compose.prod.yaml (explicit)
services:
  api:
    restart: always
    environment:
      - DEBUG=false
```

```bash
# Dev (auto-loads compose.override.yaml)
docker compose up

# Prod
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

## Padrão de Init Containers

```yaml
services:
  db-migrate:
    build: .
    command: alembic upgrade head
    depends_on:
      postgres:
        condition: service_healthy
    restart: "no"  # run once

  api:
    build: .
    depends_on:
      db-migrate:
        condition: service_completed_successfully  # wait for migration
      postgres:
        condition: service_healthy
```

## Ações do Compose Watch (v2.22+)

| Ação | Gatilho | Comportamento |
|--------|---------|----------|
| `sync` | Alteração de arquivo | Copia os arquivos alterados para o container |
| `rebuild` | Alteração de arquivo | Refaz o build da imagem e recria o container |
| `sync+restart` | Alteração de arquivo | Copia os arquivos + reinicia o processo do container |

Boas práticas:
- `sync` para código-fonte (feedback mais rápido)
- `rebuild` para arquivos de dependências (pyproject.toml, package.json)
- `sync+restart` para arquivos de configuração que exigem reinício do processo
