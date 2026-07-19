# Configuration Management — pydantic-settings

Referência de gestão de configuração em Python moderno. Configuração é dado externo
(env vars, arquivos, secrets) validado na borda da aplicação — trate como input não confiável:
valide, tipe e falhe cedo se estiver inválido.

## Princípios

- **Configuração é tipada e validada** — nunca leia `os.environ` cru espalhado pelo código.
- **Fonte única** — um objeto `Settings` central, criado uma vez e importado onde precisar.
- **Falhe cedo** — se uma env var obrigatória falta ou é inválida, o app não sobe.
- **Secrets nunca no código** — vêm do ambiente, de um secrets manager, ou de arquivo fora do VCS.
- **Defaults explícitos** — todo campo tem um default seguro ou é obrigatório de forma explícita.

## Settings com pydantic-settings

`pydantic-settings` (Pydantic v2) lê de env vars e `.env`, valida contra os type hints
e expõe um objeto imutável e tipado.

```python
from functools import lru_cache
from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        frozen=True,          # immutable after load
        extra="forbid",       # unknown env vars are an error
    )

    environment: str = Field(default="development")
    database_url: PostgresDsn
    api_key: SecretStr                    # never printed/logged accidentally
    max_connections: int = Field(default=10, ge=1, le=100)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # validated once, cached for the process lifetime
```

## Regras

- **`SecretStr` para segredos** — evita vazamento em logs, `repr` e tracebacks. Use `.get_secret_value()` só no ponto de uso.
- **`extra="forbid"`** — env var desconhecida com o prefixo vira erro, não é ignorada em silêncio.
- **`frozen=True`** — configuração não muda em runtime; imutabilidade evita bugs sutis.
- **Tipos ricos** (`PostgresDsn`, `HttpUrl`, `Path`) — validam formato, não só presença.
- **`get_settings()` cacheado** — crie uma vez, importe em qualquer lugar; não instancie `Settings()` repetidamente.

## Ambientes múltiplos

Selecione o arquivo por ambiente sem hardcode:

```python
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV = os.getenv("APP_ENV", "development")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{_ENV}"),  # later file overrides earlier
        env_prefix="APP_",
        frozen=True,
    )
```

Precedência (maior primeiro): env vars do processo → `.env.<ambiente>` → `.env` → defaults do modelo.

## Anti-patterns

- Ler `os.environ["X"]` direto no meio da lógica de negócio (sem validação, difícil de testar).
- `Settings()` instanciado em vários lugares (revalida e relê o disco toda vez).
- Segredo como `str` comum (vaza em log/`repr`).
- Default perigoso (ex.: `debug=True`, `allow_all_origins=True`) que "funciona" em dev e vaza pra prod.
