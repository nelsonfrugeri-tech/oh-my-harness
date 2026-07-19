# Ordem de Inicialização dos Serviços

## depends_on do Docker Compose com Healthcheck
```yaml
services:
  postgres:
    image: postgres:18
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7.4
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

## Readiness em Nível de Aplicação
- Não dependa apenas do health do container — verifique a conectividade real
- Faça retry com exponential backoff na inicialização
- Readiness probe vs liveness probe: readiness = "pronto para servir", liveness = "não travou"

## Padrões Comuns
| Serviço | Health Check |
|---------|-------------|
| PostgreSQL | `pg_isready` |
| MongoDB | `mongosh --eval "db.runCommand('ping')"` |
| Redis | `redis-cli ping` |
| HTTP API | `curl -f http://localhost:PORT/health` |
| gRPC | grpc_health_probe |
