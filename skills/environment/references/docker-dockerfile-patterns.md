# Padrões de Dockerfile

## Build Multi-Stage: Python (Poetry)

```dockerfile
# === Stage 1: Dependencies ===
FROM python:3.14.3-slim AS deps
WORKDIR /app
RUN pip install --no-cache-dir poetry==2.3.3
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --only=main --no-interaction --no-ansi

# === Stage 2: Build (if compilation needed) ===
FROM deps AS builder
COPY src/ ./src/
# Run any build steps (compile, generate, etc.)

# === Stage 3: Runtime ===
FROM python:3.14.3-slim AS runtime
WORKDIR /app

# Security: non-root user
RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

# Copy only what's needed
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Build Multi-Stage: Node.js (pnpm)

```dockerfile
# === Stage 1: Dependencies ===
FROM node:24.14.0-slim AS deps
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# === Stage 2: Build ===
FROM deps AS builder
COPY . .
RUN pnpm build

# === Stage 3: Runtime ===
FROM node:24.14.0-slim AS runtime
RUN corepack enable
WORKDIR /app

RUN groupadd -r app && useradd -r -g app app

COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY package.json ./

USER app
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

## Build Multi-Stage: Rust

```dockerfile
# === Stage 1: Dependency cache ===
FROM rust:1.94.1-slim AS deps
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main(){}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# === Stage 2: Build ===
FROM deps AS builder
COPY src/ ./src/
RUN touch src/main.rs && cargo build --release

# === Stage 3: Runtime (minimal) ===
FROM debian:bookworm-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r app && useradd -r -g app app
COPY --from=builder /app/target/release/myapp /usr/local/bin/

USER app
CMD ["myapp"]
```

## Template de .dockerignore

```
.git
.gitignore
.env
.env.*
*.md
LICENSE
docker-compose*.yml
compose*.yaml
Dockerfile*
Makefile

# Python
__pycache__
*.pyc
.mypy_cache
.pytest_cache
.ruff_cache
.venv
htmlcov

# Node
node_modules
.next
dist
coverage

# Rust
target

# IDE
.vscode
.idea
*.swp
```

## Checklist de Segurança

1. **Imagem base**: Use variantes `-slim`, nunca imagens completas
2. **Non-root**: Sempre `USER app` (nunca execute como root)
3. **Sem segredos na imagem**: Use build args para build-time, env vars para runtime
4. **Fixe as versões**: Tags de imagem base, pacotes do sistema, pacotes da linguagem
5. **Minimize as camadas**: Combine comandos RUN com `&&`
6. **Faça a limpeza**: Remova as listas do apt, o cache do pip e as ferramentas de build na mesma camada
7. **Root somente leitura**: Use a flag `--read-only` no compose quando possível
8. **Sem novos privilégios**: Defina `security_opt: [no-new-privileges:true]`
9. **Remova as capabilities**: `cap_drop: [ALL]`, adicione de volta apenas o necessário
10. **Escaneie as imagens**: `docker scout cves <image>` ou Trivy
