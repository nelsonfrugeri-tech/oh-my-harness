---
version: 1.0.0
name: security
description: |
  Base de conhecimento de segurança de aplicações (2026). Cobre OWASP Top 10 (2021) com mitigações,
  princípios de arquitetura zero trust, modelagem de ameaças STRIDE, validação de entrada e codificação de saída,
  padrões de autenticação (JWT, OAuth2, OIDC, MFA), autorização (RBAC, ABAC, ReBAC),
  gestão de segredos (vault, rotação, nunca hardcoded), padrões de criptografia (TLS 1.3,
  AES-256-GCM, Argon2), segurança de dependências e cadeia de suprimentos, testes de segurança (SAST, DAST,
  varredura de dependências) e fundamentos de resposta a incidentes.
  Use quando: (1) Revisar código em busca de problemas de segurança, (2) Projetar autenticação/autorização,
  (3) Configurar gestão de segredos, (4) Executar modelagem de ameaças, (5) Responder a vulnerabilidades.
  Gatilhos: /security, OWASP, authentication, authorization, STRIDE, secrets, CVE, vulnerability.
type: knowledge
---

# Security — Base de Conhecimento

## Propósito

Esta skill é a base de conhecimento para segurança de aplicações (2026).
Cobre o cenário de ameaças, autenticação, autorização, segredos, criptografia
e padrões de teste necessários para construir sistemas seguros.

**O que esta skill contém:**
- OWASP Top 10 (2021) com mitigações concretas
- Princípios de arquitetura zero trust
- Modelagem de ameaças STRIDE
- Validação de entrada e codificação de saída
- Autenticação (JWT, OAuth2/OIDC, MFA, gerenciamento de sessão)
- Autorização (RBAC, ABAC, ReBAC)
- Gestão de segredos (vault, política de rotação)
- Padrões de criptografia (o que usar, o que evitar)
- Segurança de dependências e cadeia de suprimentos
- Testes de segurança (SAST, DAST, varredura de dependências)
- Checklist de revisão de segurança

---

## Filosofia

### Segurança é uma Restrição de Design, Não uma Reflexão Tardia

Bugs de segurança são os mais caros de corrigir após o deploy. Princípios de design:

1. **Defesa em profundidade** — múltiplas camadas independentes; uma falha não compromete o sistema
2. **Menor privilégio** — cada componente tem apenas as permissões de que precisa
3. **Assuma a violação** — projete para contenção, não apenas prevenção
4. **Falhe de forma segura** — quando uma verificação de segurança falha, negue o acesso (nunca permita por padrão)
5. **Seguro por padrão** — configurações inseguras exigem opt-in explícito, não o contrário

---

## 1. OWASP Top 10 (2021)

### A01 — Broken Access Control

**Risco:** Usuários acessando recursos aos quais não deveriam ter acesso.

```python
# GOOD: verify ownership at every data access
async def get_order(order_id: str, current_user: User) -> Order:
    order = await order_repo.get(order_id)
    if order is None:
        raise NotFoundError("Order", order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        raise ForbiddenError("You do not own this order")
    return order

# BAD: trust client-provided user_id in payload
# order = await order_repo.get_by_user(request.body.user_id, order_id)
```

**Mitigações:**
- Aplique autorização na camada de dados, não apenas na camada de rotas
- Nunca confie em claims de identidade fornecidos pelo cliente (`user_id` no body/query)
- Use queries parametrizadas — nunca SQL cru com entrada do usuário
- Registre todas as falhas de controle de acesso

### A02 — Cryptographic Failures

**Risco:** Dados sensíveis expostos devido a criptografia fraca ou ausente.

| Use | NÃO use |
|-----|-----------|
| AES-256-GCM para criptografia simétrica | AES-ECB (determinístico, revela padrões) |
| Argon2id para senhas | MD5, SHA-1 para senhas |
| TLS 1.3 para transporte | TLS 1.0/1.1, SSL |
| ECDSA / RSA-2048 para assinaturas | RSA-512 |
| HKDF / PBKDF2 para derivação de chaves | Hash direto para derivação de chaves |

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(
    time_cost=3,      # iterations
    memory_cost=65536, # 64 MB
    parallelism=4,
)

# Hash password on registration
hashed = ph.hash(plain_password)

# Verify on login
try:
    ph.verify(hashed, plain_password)
    if ph.check_needs_rehash(hashed):
        hashed = ph.hash(plain_password)  # upgrade parameters
except VerifyMismatchError:
    raise AuthenticationError("Invalid credentials")
```

### A03 — Injection

**Risco:** Dados controlados pelo atacante interpretados como código (SQL, comandos de SO, LDAP, etc.).

```python
# GOOD: parameterized queries
async def get_user_by_email(email: str) -> User | None:
    return await db.fetchrow(
        "SELECT * FROM users WHERE email = $1",  # $1 is a parameter
        email,
    )

# BAD: string interpolation → SQL injection
# f"SELECT * FROM users WHERE email = '{email}'"

# GOOD: command execution — never shell=True with user input
import subprocess
result = subprocess.run(
    ["convert", "-resize", "800x600", input_path, output_path],
    capture_output=True,
    timeout=30,
    check=True,
)

# BAD: shell=True allows injection
# subprocess.run(f"convert {user_path}", shell=True)
```

### A04 — Insecure Design

**Mitigações:**
- Faça modelagem de ameaças de toda nova funcionalidade (veja a seção STRIDE)
- Defina requisitos de segurança antes da implementação
- Use padrões de design comprovados (não invente criptografia própria)
- Inclua critérios de aceitação de segurança nas user stories

### A05 — Security Misconfiguration

```python
# Checklist for production configuration
assert settings.debug is False
assert settings.secret_key != "development-key"
assert settings.database_url.startswith("postgresql://")
assert "sslmode=require" in settings.database_url

# Disable verbose error messages in production
@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    if settings.debug:
        raise exc  # show full traceback in dev
    # In production: log the error, return generic message
    logger.error("unhandled_exception", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
    )
```

### A06 — Vulnerable and Outdated Components

Veja a seção [Dependency Security](#6-dependency-and-supply-chain-security).

### A07 — Identification and Authentication Failures

Veja a seção [Authentication](#3-authentication).

### A08 — Software and Data Integrity Failures

```bash
# Verify checksums when downloading artifacts
curl -sL https://example.com/app.tar.gz | sha256sum -c expected.sha256

# Pin dependencies to exact versions (prevent supply chain attacks)
# requirements.txt
requests==2.32.3
# NOT requests>=2.32
```

### A09 — Security Logging and Monitoring Failures

```python
# Log all security events — structured, immutable, centralized
security_logger = structlog.get_logger("security")

def log_auth_attempt(email: str, success: bool, ip: str, user_agent: str) -> None:
    security_logger.info(
        "authentication_attempt",
        email=email,
        success=success,
        ip=ip,
        user_agent=user_agent,
        # Never log the password or token
    )

def log_access_denied(user_id: str, resource: str, action: str) -> None:
    security_logger.warning(
        "access_denied",
        user_id=user_id,
        resource=resource,
        action=action,
    )
```

### A10 — Server-Side Request Forgery (SSRF)

```python
import ipaddress
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254"}

def validate_external_url(url: str) -> str:
    """Validate URL is safe to fetch — prevents SSRF."""
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValidationError(f"URL scheme {parsed.scheme!r} not allowed")

    hostname = parsed.hostname or ""
    if hostname in BLOCKED_HOSTS:
        raise ValidationError("URL points to internal network")

    # Block private IP ranges
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            raise ValidationError("URL points to internal network")
    except ValueError:
        pass  # hostname is a domain name, not an IP — OK

    return url
```

---

## 2. Modelagem de Ameaças STRIDE

### Categorias STRIDE

| Ameaça | Descrição | Mitigação |
|--------|-------------|-----------|
| **S**poofing | Personificar outro usuário ou sistema | Autenticação, MFA, tokens assinados |
| **T**ampering | Modificar dados em trânsito ou em repouso | Assinaturas HMAC, TLS, verificações de integridade |
| **R**epudiation | Negar que uma ação ocorreu | Log de auditoria, assinaturas digitais |
| **I**nformation Disclosure | Vazar dados sensíveis | Criptografia, controle de acesso, mascaramento de dados |
| **D**enial of Service | Esgotar recursos | Rate limiting, circuit breakers, CDN |
| **E**levation of Privilege | Obter permissões não autorizadas | Menor privilégio, RBAC, validação de entrada |

### Processo de Modelagem de Ameaças

```
1. IDENTIFY ASSETS
   - What data is sensitive? (PII, credentials, payment data, health data)
   - What operations are privileged? (admin actions, data deletion, payment)
   - What external integrations exist?

2. CREATE DATA FLOW DIAGRAM
   - Map all entry points (APIs, webhooks, queues)
   - Map all data stores (databases, caches, files)
   - Map all trust boundaries (internet, internal network, DMZ)

3. APPLY STRIDE PER COMPONENT
   - For each data flow: which STRIDE threats apply?
   - Rate each threat: Probability (H/M/L) × Impact (H/M/L)

4. DEFINE MITIGATIONS
   - One mitigation per identified threat
   - Verify mitigation in acceptance criteria

5. VALIDATE
   - Security tests cover each mitigation
   - Automated SAST/DAST in CI pipeline
```

---

## 3. Authentication

### Boas Práticas de JWT

```python
from datetime import datetime, timedelta, timezone
import jwt

SECRET_KEY = settings.jwt_secret  # from env, min 256 bits
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)

def create_access_token(user_id: str, roles: list[str]) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": user_id,
        "roles": roles,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE,
        "jti": secrets.token_urlsafe(16),  # unique token ID (for revocation)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_and_validate_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {e}")

    # Check revocation list (Redis)
    if redis.exists(f"revoked:jti:{payload['jti']}"):
        raise AuthenticationError("Token has been revoked")

    return payload
```

### OAuth2 / OIDC

```
Flow selection:
  Public web app (SPA)     → Authorization Code + PKCE
  Server-side web app      → Authorization Code
  Machine-to-machine       → Client Credentials
  Native mobile app        → Authorization Code + PKCE
  Device (TV, CLI)         → Device Authorization

Scopes to request:
  Minimum required: openid, email
  Only request what you need
  Never store access tokens longer than needed
```

### Requisitos de MFA

```
When MFA is required:
- Admin panel access
- Payment operations
- Account settings changes (email, password)
- Data export/deletion
- API key creation

Accepted MFA methods (order of strength):
  FIDO2/WebAuthn (hardware key, passkey) — strongest
  TOTP (authenticator app)
  SMS OTP — weakest (SIM swap risk), avoid for high-value operations
```

---

## 4. Autorização

### RBAC (Controle de Acesso Baseado em Papéis)

```python
from enum import Enum

class Permission(Enum):
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    ORDERS_READ = "orders:read"
    ORDERS_WRITE = "orders:write"
    ADMIN = "admin:*"

ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "viewer": {Permission.USERS_READ, Permission.ORDERS_READ},
    "editor": {Permission.USERS_READ, Permission.USERS_WRITE, Permission.ORDERS_READ, Permission.ORDERS_WRITE},
    "admin": {p for p in Permission},  # all permissions
}

def has_permission(user: User, permission: Permission) -> bool:
    user_permissions: set[Permission] = set()
    for role in user.roles:
        user_permissions |= ROLE_PERMISSIONS.get(role, set())
    return permission in user_permissions or Permission.ADMIN in user_permissions
```

### Regras de Autorização

```
1. Authorization checks at every layer — route handler AND data access layer
2. Deny by default — no permission means no access (never default-allow)
3. Check ownership — user.id == resource.owner_id for non-admin operations
4. Audit trail — log every denied access attempt
5. Separate read from write permissions — read is cheap to grant, write is not
```

---

## 5. Gestão de Segredos

### Regras (Não Negociáveis)

```
1. NEVER hardcode secrets in code
2. NEVER commit secrets to git (even private repos)
3. NEVER log secrets (API keys, tokens, passwords)
4. NEVER pass secrets via URL parameters
5. NEVER store secrets in client-side code (JavaScript bundle, mobile app)
```

### Hierarquia de Armazenamento de Segredos

| Ambiente | Armazenamento | Padrão de Acesso |
|-------------|-------|---------------|
| Dev local | `.env` (no gitignore) + `.env.example` | Variáveis de ambiente diretas |
| CI/CD | Segredos da plataforma (GitHub Actions secrets) | Injetados como variáveis de ambiente |
| Produção | HashiCorp Vault / AWS Secrets Manager | SDK com tokens de curta duração |
| Senhas de banco de dados | Segredos dinâmicos do Vault | Rotacionadas automaticamente |

### Política de Rotação

```
API keys: rotate every 90 days
JWT signing keys: rotate every 30 days
Database passwords: rotate every 30 days (Vault dynamic secrets)
TLS certificates: auto-rotate via cert-manager / Let's Encrypt
After any suspected exposure: rotate immediately
```

### Python: pydantic-settings para Segredos

```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # SecretStr: value is masked in logs/repr
    database_password: SecretStr
    api_key: SecretStr
    jwt_secret: SecretStr = Field(min_length=32)

    def get_database_url(self) -> str:
        # .get_secret_value() only where needed
        return f"postgresql://user:{self.database_password.get_secret_value()}@host/db"
```

---

## 6. Dependency and Supply Chain Security

### Varredura Automatizada

```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request, schedule]
  cron: "0 6 * * 1"  # weekly on Monday

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Python — pip-audit
      - run: pip install pip-audit
      - run: pip-audit --requirement requirements.txt --strict

      # Node.js — pnpm audit
      - run: pnpm audit --audit-level moderate

      # Container images — Trivy
      - name: Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:latest
          exit-code: "1"
          severity: "CRITICAL,HIGH"

      # SAST — Semgrep
      - name: Semgrep SAST
        uses: semgrep/semgrep-action@v1
        with:
          config: auto
```

### Regras de Dependências

```
1. Pin exact versions — never >=, ~=, or ^
2. Audit new dependencies before adding (check CVE history, maintenance status)
3. Prefer small, focused libraries over large frameworks (smaller attack surface)
4. Check package name for typosquatting (requests vs requets)
5. Verify checksums for downloaded artifacts
6. Run dependency audit in CI on every PR and weekly schedule
```

---

## 7. Testes de Segurança

### SAST (Análise Estática)

```bash
# Python
bandit -r src/ -ll  # severity LOW+
semgrep --config=auto src/

# TypeScript/JavaScript
eslint --plugin security src/

# Multi-language
semgrep --config=p/owasp-top-ten .
```

### DAST (Análise Dinâmica)

```bash
# OWASP ZAP — passive scan against running app
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 \
  -r zap-report.html \
  -I  # ignore warnings for CI (exit 0)

# For CI: fail on medium+ severity
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 \
  --exit-code 2  # fail on MEDIUM+
```

### Checklist de Testes de Segurança

```markdown
### Authentication
- [ ] Test expired token → 401
- [ ] Test invalid token signature → 401
- [ ] Test token reuse after logout → 401
- [ ] Test brute force (rate limiting kicks in)

### Authorization
- [ ] Test user A accessing user B's resource → 403
- [ ] Test unauthorized role performing privileged action → 403
- [ ] Test missing auth header → 401
- [ ] Test elevated privilege after role downgrade

### Injection
- [ ] SQL injection in all text inputs
- [ ] OS command injection in path/filename inputs
- [ ] XSS in all user-controlled output

### Secrets
- [ ] No secrets in git history
- [ ] No secrets in logs
- [ ] No secrets in API responses
- [ ] Secrets rotated in staging/production
```

---

## Checklist de Revisão de Segurança

```markdown
### Input Validation
- [ ] All external inputs validated at boundaries (Pydantic, zod, etc.)
- [ ] No SQL/command injection possible (parameterized queries, subprocess list)
- [ ] File uploads validated (type, size, content inspection)
- [ ] URL inputs validated against SSRF (private IP ranges blocked)

### Authentication
- [ ] Passwords hashed with Argon2id (never MD5/SHA-1)
- [ ] JWTs short-lived (<= 15 min access, <= 7 day refresh)
- [ ] MFA required for privileged operations
- [ ] Brute force protection (rate limiting on auth endpoints)

### Authorization
- [ ] Every endpoint has an authorization check
- [ ] Resource ownership verified (not just role)
- [ ] Default-deny (no permission = no access)
- [ ] Access denial logged

### Secrets
- [ ] No secrets in code or git
- [ ] Secrets loaded from environment / vault
- [ ] SecretStr used in Python settings
- [ ] Rotation schedule defined

### Cryptography
- [ ] Argon2id for passwords
- [ ] AES-256-GCM for encryption
- [ ] TLS 1.3 for all transport
- [ ] No custom crypto

### Dependencies
- [ ] Exact versions pinned
- [ ] Dependency audit passes in CI
- [ ] No known CVEs with CRITICAL or HIGH severity

### Logging
- [ ] Security events logged (auth, access denied, data export)
- [ ] No sensitive data in logs (passwords, tokens, PII)
- [ ] Logs are immutable and shipped to SIEM
```

---

