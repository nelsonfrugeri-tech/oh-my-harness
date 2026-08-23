# Gerenciamento de .env

## Estrutura
```
.env.example    — committed, all keys with placeholder values
.env            — gitignored, actual values
.env.test       — gitignored, test environment values
.env.production — NEVER on disk, only in CI/CD secrets
```

## Padrão de Validação
```python
# Python with pydantic-settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    debug: bool = False
    
    model_config = {"env_file": ".env"}
```

## Regras
1. **Nunca faça commit do .env** — adicione ao .gitignore
2. **Sempre faça commit do .env.example** — documenta as variáveis obrigatórias
3. **Valide na inicialização** — falhe rápido se faltar alguma variável obrigatória
4. **Sem segredos no docker-compose.yml** — use a diretiva env_file
5. **Rotacione os segredos** — nunca reutilize entre ambientes

## Docker Compose
```yaml
services:
  api:
    env_file:
      - .env
    environment:
      - NODE_ENV=development  # overrides .env
```
