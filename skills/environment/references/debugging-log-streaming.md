# Streaming de Logs e Depuração

## Logs do Docker
```bash
# Follow logs for a service
docker compose logs -f api

# Last 100 lines
docker compose logs --tail 100 api

# Multiple services
docker compose logs -f api worker

# With timestamps
docker compose logs -f -t api
```

## Depurando Containers em Execução
```bash
# Shell into container
docker compose exec api bash

# Run one-off command
docker compose run --rm api python manage.py shell

# Inspect container
docker inspect <container_id> | jq '.[0].State'

# Network debugging
docker compose exec api curl -v http://postgres:5432
```

## Logging Estruturado
```python
import structlog
logger = structlog.get_logger()
logger.info("request_processed", method="GET", path="/api/users", duration_ms=42)
# Output: {"event": "request_processed", "method": "GET", "path": "/api/users", "duration_ms": 42}
```

## Problemas Comuns
| Problema | Diagnóstico |
|---------|-----------|
| Container em loop de crash | `docker logs <id>` — verifique o erro de inicialização |
| Conflito de porta | `lsof -i :PORT` — encontre o processo usando a porta |
| Permissões de volume | Verifique o mapeamento de UID/GID entre host e container |
| Resolução de DNS | `docker compose exec api nslookup postgres` |
