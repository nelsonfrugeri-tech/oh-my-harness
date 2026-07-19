---
version: 1.0.0
name: ci-cd
description: |
  Base de conhecimento de pipelines CI/CD (2026). Cobre princípios de design de pipeline (fail fast, trunk-based
  development), padrões de workflow do GitHub Actions (reusable workflows, matrix builds, environments),
  quality gates automatizados (SAST, varredura de dependências, limiares de cobertura, contract tests),
  estratégias de deployment (blue/green, canary, feature flags, rolling), procedimentos de rollback,
  gestão de artefatos (tagueamento de imagens Docker, higiene de registry), promoção de ambientes (dev →
  staging → produção), gestão de releases (versionamento semântico, conventional commits, geração de
  changelog) e disciplina de CI (padrões de commit, branch protection, estratégias de merge).
  Use quando: (1) Projetar pipelines CI/CD, (2) Escrever workflows do GitHub Actions, (3) Escolher
  estratégias de deployment, (4) Configurar quality gates, (5) Implementar automação de releases.
  Gatilhos: /ci-cd, /ci, /cd, GitHub Actions, pipeline, deployment, release, blue/green, canary.
type: knowledge
---

# CI/CD — Base de Conhecimento

## Propósito

Esta skill é a base de conhecimento para design de pipelines CI/CD (2026).
Cobre arquitetura de pipeline, quality gates, estratégias de deployment e automação de releases.

**O que esta skill contém:**
- Princípios de design de pipeline (fail fast, paralelismo, caching)
- Padrões do GitHub Actions (reusable workflows, matrix, environments, OIDC)
- Quality gates (SAST, varredura de dependências, cobertura, contract tests)
- Estratégias de deployment (blue/green, canary, rolling, feature flags)
- Procedimentos de rollback
- Gestão de artefatos (imagens Docker, versionamento, registry)
- Promoção de ambientes (dev → staging → produção)
- Gestão de releases (versionamento semântico, changelog, GitHub releases)
- Disciplina de CI (padrões de commit, branch protection)

---

## Filosofia

### As Três Leis do CI/CD

1. **O build está sempre verde** — um build quebrado bloqueia todos; corrija-o imediatamente
2. **Feedback rápido vence** — desenvolvedores devem saber se sua mudança quebrou algo em < 5 minutos
3. **Automação em vez de cerimônia** — se um humano faz manualmente a cada merge, automatize

### Trunk-Based Development

```
main (trunk)  ←— short-lived feature branches (< 2 days)
               ←— hotfix branches (< hours)

Deployments from main only.
Feature branches merged via PR, never survive more than 2 days.
Feature flags for in-progress work that's merged but not released.
```

---

## 1. Princípios de Design de Pipeline

### Ordenação de Estágios (Fail Fast)

```
1. Lint + Format check     (30s)    — fail immediately on style violations
2. Unit tests              (2-5m)   — fast, isolated, no external dependencies
3. Build                   (2-5m)   — compile, bundle, Docker build
4. Integration tests       (5-10m)  — requires real or mocked services
5. Security scan           (2-5m)   — SAST, dependency vulnerabilities
6. Contract tests          (1-2m)   — API contract validation
7. Performance tests       (5-15m)  — k6/locust, only on staging
8. E2E tests               (10-20m) — Playwright, only on staging
9. Deploy staging          (2-5m)   — automatic on main
10. Smoke tests on staging (1-2m)   — verify deployment health
11. Deploy production      (2-5m)   — manual approval gate
12. Smoke tests production (1-2m)   — verify production health
```

### Paralelismo

```yaml
# Run independent jobs in parallel to reduce total pipeline time
jobs:
  lint:           { ... }  # runs in parallel with tests
  unit-tests:     { ... }  # runs in parallel with lint
  type-check:     { ... }  # runs in parallel with lint and tests
  security-scan:  { needs: [lint, unit-tests] }
  build:          { needs: [lint, unit-tests, type-check] }
  integration:    { needs: [build] }
  deploy-staging: { needs: [integration, security-scan] }
```

---

## 2. Padrões do GitHub Actions

### Workflow Base de CI para Python

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  quality:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install poetry==2.3.3
          poetry install --no-interaction

      - name: Lint (ruff)
        run: poetry run ruff check .

      - name: Format check (black)
        run: poetry run black --check .

      - name: Type check (mypy)
        run: poetry run mypy src/

      - name: Unit tests
        run: poetry run pytest tests/unit -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
          fail_ci_if_error: true
          threshold: 80

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: pip-audit
        run: |
          pip install pip-audit==2.7.3
          pip-audit --requirement requirements.txt --strict

      - name: Semgrep SAST
        uses: semgrep/semgrep-action@v1
        with:
          config: "p/python p/owasp-top-ten"
```

### Workflow de CI para TypeScript

```yaml
# .github/workflows/ci-ts.yml
name: CI TypeScript

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v3
        with:
          version: 10.33.0

      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "pnpm"

      - run: pnpm install --frozen-lockfile

      - run: pnpm run type-check
      - run: pnpm run lint          # biome check
      - run: pnpm run test          # vitest run
      - run: pnpm run build

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage/lcov.info
```

### Reusable Workflows (Workflows Reutilizáveis)

```yaml
# .github/workflows/deploy.yml (reusable)
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      image_tag:
        required: true
        type: string
    secrets:
      DEPLOY_TOKEN:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.environment }}
      url: https://${{ inputs.environment }}.example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: ./scripts/deploy.sh ${{ inputs.environment }} ${{ inputs.image_tag }}
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

# Caller workflow
jobs:
  deploy-staging:
    needs: [build]
    uses: ./.github/workflows/deploy.yml
    with:
      environment: staging
      image_tag: ${{ needs.build.outputs.image_tag }}
    secrets:
      DEPLOY_TOKEN: ${{ secrets.STAGING_DEPLOY_TOKEN }}
```

### Autenticação OIDC (Sem Segredos de Longa Duração)

```yaml
jobs:
  deploy:
    permissions:
      id-token: write   # required for OIDC
      contents: read

    steps:
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions-deploy
          aws-region: us-east-1
          # No AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY needed
```


---

## 3. Quality Gates

### Limiares de Cobertura

```yaml
# pytest — fail if coverage drops below threshold
- name: Unit tests with coverage
  run: |
    poetry run pytest tests/unit \
      --cov=src \
      --cov-fail-under=80 \
      --cov-report=xml \
      --cov-report=term-missing

# vitest — same for TypeScript
- name: Tests with coverage
  run: |
    pnpm vitest run --coverage \
      --coverage.thresholds.lines=80 \
      --coverage.thresholds.branches=80
```

### Contract Testing no CI

```yaml
- name: Run Pact contract tests
  run: |
    poetry run pytest tests/contract -v
    # Publish pacts to Pact Broker
    poetry run pact-broker publish ./pacts \
      --broker-base-url ${{ vars.PACT_BROKER_URL }} \
      --consumer-app-version ${{ github.sha }}

- name: Verify provider contracts
  run: |
    PACT_BROKER_BASE_URL=${{ vars.PACT_BROKER_URL }} \
    GIT_COMMIT=${{ github.sha }} \
    poetry run pytest tests/provider -v
```

### Regras de Branch Protection

```yaml
# Repository settings (via GitHub UI or terraform)
Branch protection for main:
  required_status_checks:
    - CI / Code Quality
    - CI / Security Scan
  required_pull_request_reviews:
    required_approving_review_count: 1
    dismiss_stale_reviews: true
  restrictions:
    push: []  # nobody pushes directly to main
  enforce_admins: true
  require_linear_history: true  # squash or rebase only
```

---

## 4. Build Docker e Registry

### Build Multi-Stage no CI

```yaml
- name: Build Docker image
  id: build
  run: |
    IMAGE_TAG="$REGISTRY/$SERVICE_NAME:${{ github.sha }}"
    LATEST_TAG="$REGISTRY/$SERVICE_NAME:latest"

    docker build \
      --target runtime \
      --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
      --build-arg GIT_COMMIT=${{ github.sha }} \
      --tag "$IMAGE_TAG" \
      --tag "$LATEST_TAG" \
      --cache-from "$REGISTRY/$SERVICE_NAME:cache" \
      .

    echo "image_tag=$IMAGE_TAG" >> $GITHUB_OUTPUT

- name: Scan image for vulnerabilities
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ steps.build.outputs.image_tag }}
    severity: CRITICAL,HIGH
    exit-code: 1

- name: Push image
  run: |
    docker push ${{ steps.build.outputs.image_tag }}
    docker push "$REGISTRY/$SERVICE_NAME:latest"
```

### Estratégia de Tagueamento de Imagens

```
Development:   registry/service:sha-abc1234
Staging:       registry/service:staging-sha-abc1234
Production:    registry/service:v1.2.3
Latest:        registry/service:latest  (always production)

Never tag with "latest" for non-production images.
Never mutate an existing tag (except "latest").
Use SHA tags for auditability and rollback.
```

---

## 5. Estratégias de Deployment

### Deployment Blue/Green

```yaml
# Blue/Green: two identical environments, traffic switch
deploy-blue-green:
  steps:
    - name: Deploy to inactive environment
      run: |
        ACTIVE=$(get_active_env)
        INACTIVE=$([ "$ACTIVE" = "blue" ] && echo "green" || echo "blue")

        # Deploy to inactive
        deploy_to_env $INACTIVE $IMAGE_TAG

        # Run smoke tests on inactive
        run_smoke_tests $INACTIVE

    - name: Switch traffic
      run: |
        switch_traffic_to $INACTIVE  # atomic, < 1s downtime

    - name: Wait and verify
      run: |
        sleep 60
        verify_error_rate $INACTIVE
        if [ $? -ne 0 ]; then
          switch_traffic_to $ACTIVE  # automatic rollback
          exit 1
        fi
```

### Deployment Canary

```yaml
# Canary: gradual traffic shift
deploy-canary:
  steps:
    - name: Deploy canary (5% traffic)
      run: kubectl set image deployment/api api=$IMAGE_TAG --namespace=production
      # Canary gets 5% of traffic via load balancer weights

    - name: Monitor canary metrics (15 min)
      run: |
        for i in {1..15}; do
          ERROR_RATE=$(get_error_rate canary)
          LATENCY=$(get_p99_latency canary)
          if [ "$ERROR_RATE" -gt 5 ] || [ "$LATENCY" -gt 1000 ]; then
            echo "Canary degraded: error_rate=$ERROR_RATE latency=$LATENCY"
            rollback_canary
            exit 1
          fi
          sleep 60
        done

    - name: Promote to 100%
      run: promote_canary_to_stable
```

### Feature Flags

```python
# Use feature flags for risky features merged to main
from typing import Any

class FeatureFlags:
    def __init__(self, posthog_client: Any) -> None:
        self.client = posthog_client

    def is_enabled(self, flag: str, user_id: str) -> bool:
        return self.client.feature_enabled(flag, user_id)

# In code
if feature_flags.is_enabled("new_checkout_flow", request.user.id):
    return new_checkout(cart)
return legacy_checkout(cart)
```


---

## 6. Procedimentos de Rollback

### Matriz de Decisão de Rollback

| Cenário | Método de Rollback | Tempo |
|----------|----------------|------|
| Bug de código (sem migração de BD) | Reimplantar imagem anterior | < 5 min |
| Bug de código (migração reversível) | Reimplantar + rodar migração de reversão | 5-15 min |
| Corrupção de dados | Restaurar banco a partir de backup | 15-60 min |
| Falha de serviço externo | Desabilitar feature flag | < 2 min |
| Blue/green ativo | Voltar tráfego para o blue | < 1 min |

### Gatilhos de Rollback Automatizado

```yaml
- name: Post-deploy health check
  run: |
    # Check error rate for 5 minutes after deploy
    for i in {1..5}; do
      ERROR_RATE=$(curl -s "$METRICS_URL/error_rate" | jq .value)
      if (( $(echo "$ERROR_RATE > 5" | bc -l) )); then
        echo "ERROR: Error rate $ERROR_RATE% exceeds 5% threshold"
        # Trigger rollback
        kubectl rollout undo deployment/api
        exit 1
      fi
      sleep 60
    done
    echo "Deploy healthy: error rate $ERROR_RATE%"
```

---

## 7. Gestão de Releases

### Conventional Commits

```
Format: <type>(<scope>): <description>

Types:
  feat:     New feature                  → MINOR version bump
  fix:      Bug fix                      → PATCH version bump
  perf:     Performance improvement      → PATCH version bump
  refactor: Code change (no feature/fix) → No version bump
  docs:     Documentation only           → No version bump
  test:     Tests only                   → No version bump
  chore:    Build, CI, config changes    → No version bump
  BREAKING CHANGE: (footer)              → MAJOR version bump

Examples:
  feat(auth): add OAuth2 login with Google
  fix(api): handle null response from payment gateway
  feat(checkout)!: replace cart API — BREAKING CHANGE in response format
  chore(ci): upgrade Actions runners to ubuntu-24.04
```

### Workflow de Release Automatizado

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # full history for changelog

      - name: Create release
        uses: googleapis/release-please-action@v4
        id: release
        with:
          release-type: python  # or node
          # Reads conventional commits, bumps version, generates CHANGELOG

      - name: Build and push release image
        if: steps.release.outputs.release_created
        run: |
          VERSION=${{ steps.release.outputs.tag_name }}
          docker build -t "$REGISTRY/$SERVICE:$VERSION" .
          docker push "$REGISTRY/$SERVICE:$VERSION"
          docker tag "$REGISTRY/$SERVICE:$VERSION" "$REGISTRY/$SERVICE:latest"
          docker push "$REGISTRY/$SERVICE:latest"
```

### Versionamento Semântico

```
MAJOR.MINOR.PATCH

MAJOR: Breaking API change, incompatible change for consumers
MINOR: New backward-compatible feature
PATCH: Backward-compatible bug fix

Pre-release: 1.2.0-alpha.1, 1.2.0-rc.1
Build metadata: 1.2.0+20260401.sha1234

Rules:
- Never release from a branch other than main
- Tag releases with git tags (v1.2.3)
- CHANGELOG.md updated in every release commit
- GitHub Release created automatically from tag
```

---

## 8. Disciplina de CI

### Padrões de Commit

```
Rules:
1. Use conventional commit format (feat:, fix:, etc.)
2. One logical change per commit
3. Tests pass before committing (enforced by pre-commit hooks)
4. No merge commits on main (squash or rebase)
5. Commit message explains WHY, not just WHAT

Pre-commit hooks (pre-commit framework):
  - Lint check (ruff / biome)
  - Type check (mypy / tsc)
  - Test evidence check (no commits without test file changes)
  - Secret scanning (detect-secrets)
  - Conventional commit message format
```

### Estratégia de Branches

```
main          ← always deployable, always green
  └── feat/issue-42-user-oauth    (short-lived, < 2 days)
  └── fix/payment-null-response   (same day)
  └── chore/upgrade-python-3-12   (same day)

Rules:
- Never commit directly to main
- PRs require 1 approval + all CI green
- Squash merges: clean git history on main
- Delete branches after merge
```

---

