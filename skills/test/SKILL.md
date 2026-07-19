---
version: 1.0.0
name: test
description: |
  Base de conhecimento moderna de Quality Assurance (2026). Cobre estratégia de testes (pyramid vs trophy),
  testes E2E (Playwright, pytest), gerenciamento de dados de teste (fixtures, factories, seeding),
  testes de integração (dependências reais vs mocks, testcontainers), testes de contrato de API (Pact),
  testes de performance (k6, Locust), testes de acessibilidade (axe-core, WCAG 2.2),
  testes de regressão visual, smoke testing, relatórios de teste, validação da Definition of Done,
  e checklist de prontidão para produção.
  Use quando: (1) Definir estratégia de testes, (2) Configurar ambientes de teste isolados,
  (3) Implementar testes E2E/integração/contrato/performance/a11y/visuais, (4) Validar
  a Definition of Done, (5) Avaliar a prontidão para produção.
  Gatilhos: /test, /qa, QA, quality assurance, testing strategy, test plan, smoke test.
type: capability
---

# Test — Metodologia de Quality Assurance

## Propósito

Esta skill é a base de conhecimento para Quality Assurance moderna (2026).
Ela complementa as skills de linguagem (`python`, `typescript`) com padrões e estratégias específicos de QA.

**O que esta skill contém:**
- Estratégia de testes (pyramid vs trophy, o que testar em cada camada)
- Testes E2E (Playwright, pytest, isolamento, prevenção de flakiness)
- Gerenciamento de dados de teste (fixtures, factories, seeding, limpeza)
- Testes de integração (dependências reais vs mocks, testcontainers)
- Testes de contrato de API (Pact, contratos orientados ao consumidor)
- Testes de performance (k6, Locust, load/stress/soak)
- Testes de acessibilidade (axe-core, Lighthouse, WCAG 2.2)
- Testes de regressão visual
- Configuração e teardown de ambiente
- Smoke testing
- Checklist de validação da Definition of Done
- Checklist de prontidão para produção

**O que esta skill NÃO contém:**
- Padrões de código específicos de linguagem (esses ficam em `python` / `typescript`)
- Configuração de pipeline CI/CD (isso fica em `ci-cd`)
- Fluxo de execução (os agentes cuidam disso)

---

## Filosofia

### Testes são Engenharia, Não uma Reflexão Tardia

Qualidade é construída, não testada no final. Testes são artefatos de primeira classe com os mesmos padrões
do código de produção: tipados, revisados, mantidos e refatorados.

### Princípios Fundamentais

1. **Teste o que importa, não o que é fácil** — foque no comportamento visível ao usuário e nos caminhos críticos de negócio
2. **Testes determinísticos ou nenhum teste** — cada teste deve produzir o mesmo resultado em toda execução
3. **Ciclos de feedback rápidos** — unit: <1s, integração: <5s, E2E: <30s, suíte total: <10 min no CI
4. **Isolamento é inegociável** — cada teste começa com estado limpo
5. **Teste o contrato, não a implementação** — faça asserções sobre o comportamento observável, não sobre o estado interno

---

## 1. Estratégia de Testes — Pyramid vs Trophy

### A Pirâmide de Testes (Martin Fowler)

```
        /  E2E  \          Few, slow, expensive
       /----------\
      / Integration \      Some, moderate speed
     /----------------\
    /    Unit Tests     \  Many, fast, cheap
   /____________________\
```

**Quando usar:** Serviços de backend, bibliotecas, utilitários com fronteiras de função bem definidas.

### O Troféu de Testes (Kent C. Dodds)

```
        ___E2E___          Few, high confidence
       /         \
      | Integration |      MOST tests here
      |_____________|
       \  Unit   /         Some, pure logic only
        \_______/
       |  Static  |        TypeScript, ESLint, mypy
       |__________|
```

**Quando usar:** Aplicações frontend, APIs, sistemas onde os pontos de integração são o risco principal.

### Framework de Decisão

| Sinal | Prefira Pyramid | Prefira Trophy |
|--------|---------------|---------------|
| Lógica de negócio pura | Sim | |
| Algoritmos complexos | Sim | |
| Aplicação com muita UI | | Sim |
| API com muitas integrações | | Sim |
| Biblioteca / SDK | Sim | |
| Microsserviços | | Sim |
| Pipeline de dados | Sim | |

### O que Testar em Cada Camada

**Análise Estática (base):**
- Verificação de tipos (mypy, TypeScript strict)
- Linting (ruff, Biome)
- Varredura de segurança (bandit, semgrep)

**Testes Unitários:**
- Funções puras sem efeitos colaterais
- Cálculos de lógica de negócio
- Transformações de dados, regras de validação
- Casos extremos e condições de fronteira

**Testes de Integração:**
- Comportamento de endpoint de API (request -> response)
- Consultas e mutações de banco de dados
- Interações com serviços externos
- Fluxos de autenticação e autorização

**Testes E2E:**
- Jornadas críticas do usuário (signup, compra, fluxos principais)
- Fluxos entre serviços
- Comportamento específico de navegador
- Conformidade de acessibilidade

---

## 2. Configuração de Ambiente de Teste

### Princípios

1. **Reproduzível** — mesmo ambiente toda vez
2. **Isolado** — os testes não podem interferir uns nos outros
3. **Efêmero** — criado antes dos testes, destruído depois
4. **Rápido** — a configuração do ambiente leva segundos, não minutos

### Docker Compose para Dependências de Teste

```yaml
# docker-compose.test.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data  # RAM disk for speed

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  localstack:
    image: localstack/localstack:3
    ports:
      - "4566:4566"
    environment:
      SERVICES: s3,sqs,sns
```

### Testcontainers (Programático)

```python
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url()

@pytest.fixture(scope="session")
def redis():
    with RedisContainer("redis:7-alpine") as r:
        yield r.get_connection_url()
```

### Checklist de Teardown

Após cada execução de testes:
- [ ] Tabelas do banco de dados truncadas ou removidas
- [ ] Chaves do Redis limpas (flush)
- [ ] Arquivos temporários deletados
- [ ] Containers Docker parados e removidos
- [ ] Portas liberadas
- [ ] Variáveis de ambiente restauradas

### Padrão conftest.py (pytest)

```python
import pytest

@pytest.fixture(autouse=True)
def clean_database(db_session):
    """Roll back all changes after each test."""
    yield
    db_session.rollback()

@pytest.fixture(autouse=True)
def reset_redis(redis_client):
    """Flush Redis after each test."""
    yield
    redis_client.flushdb()
```

---

## 3. Testes E2E

### Seleção de Ferramenta

| Ferramenta | Linguagem | Melhor Para |
|------|----------|----------|
| **Playwright** | Python, JS/TS, .NET, Java | Cross-browser, API + UI, web moderna |
| **pytest** | Python | E2E de backend, testes de API |
| **Vitest** | TypeScript | Unit + integração de frontend |

### Boas Práticas do Playwright

```python
# Page Object Model
class LoginPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.email = page.get_by_label("Email")
        self.password = page.get_by_label("Password")
        self.submit = page.get_by_role("button", name="Sign in")

    async def login(self, email: str, password: str) -> None:
        await self.email.fill(email)
        await self.password.fill(password)
        await self.submit.click()

async def test_login_success(page: Page) -> None:
    login_page = LoginPage(page)
    await page.goto("/login")
    await login_page.login("user@test.com", "password123")
    await expect(page).to_have_url("/dashboard")
```

### Estratégia de Locators (Ordem de Prioridade)

1. `get_by_role()` — semântico, acessível, resiliente
2. `get_by_label()` — elementos de formulário
3. `get_by_text()` — conteúdo de texto visível
4. `get_by_test_id()` — último recurso, data-testid explícito

**Nunca use:** seletores CSS atrelados à estilização, XPath, nomes de classe gerados automaticamente

### Prevenção de Flakiness

```python
# BAD: arbitrary sleep
await page.wait_for_timeout(3000)

# GOOD: wait for specific condition
await page.wait_for_selector("[data-loaded='true']")
await expect(page.get_by_role("heading")).to_be_visible()
```

### O que Testar com E2E

- [ ] Registro e login de usuário
- [ ] Fluxo de negócio principal (aquele que gera receita)
- [ ] Fluxo de pagamento/checkout
- [ ] Fronteiras de permissão (admin vs usuário)
- [ ] Recuperação de erro (falha de rede, entrada inválida)

### O que NÃO Testar com E2E

- Renderização de componente individual (use testes unitários)
- Detalhes de estilização CSS (use regressão visual)
- Schemas de resposta de API (use testes de contrato)
- Performance sob carga (use testes de performance)

---

## 4. Gerenciamento de Dados de Teste

### Abordagens

| Abordagem | Quando Usar | Prós | Contras |
|----------|-------------|------|------|
| **Fixtures** | Dados de referência estáticos | Simples, legível | Frágil se o schema mudar |
| **Factories** | Objetos de teste dinâmicos | Flexível, DRY | Requer código de setup |
| **Seeding** | Pré-população do banco de dados | Dados realistas | Mais lento, mais difícil de manter |
| **Builders** | Grafos de objetos complexos | API fluente, componível | Mais código para manter |

### Padrão Factory (Python — factory_boy)

```python
import factory

class UserFactory(factory.Factory):
    class Meta:
        model = User

    name = factory.Faker("name")
    email = factory.LazyAttribute(lambda o: f"{o.name.lower().replace(' ', '.')}@test.com")
    role = "user"
    is_active = True

class AdminFactory(UserFactory):
    role = "admin"

# Usage
user = UserFactory()
admin = AdminFactory(name="Admin User")
users = UserFactory.create_batch(10)
```

### Regras de Limpeza de Dados

1. **Cada teste cria seus próprios dados** — nunca dependa de dados pré-existentes
2. **Cada teste faz sua própria limpeza** — use rollback de transação ou truncamento
3. **Nunca use dados de produção nos testes** — gere dados sintéticos
4. **Evite suposições sobre IDs auto-incrementais** — use UUIDs ou consulte por atributos
5. **Dados de seed são apenas para referência compartilhada** — países, moedas, papéis (roles)

---

## 5. Testes de Integração

### Dependências Reais vs Mocks

| Use Dependências Reais | Use Mocks |
|---------------|-----------|
| Consultas de banco de dados (testcontainers) | APIs de terceiros (Stripe, Twilio) |
| Comportamento de cache do Redis | Envio de e-mail |
| Integração com fila de mensagens | Envio de SMS |
| Operações de sistema de arquivos | Serviços externos com rate limit |
| Provedor de autenticação (Keycloak local) | Serviços que você não controla |

### Testando com Banco de Dados Real

```python
@pytest.fixture(scope="session")
def db_engine(postgres_url: str):
    engine = create_engine(postgres_url)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

### Escopo do Teste de Integração

Cada teste de integração valida UM ponto de integração:
- Endpoint de API + banco de dados
- Serviço + fila de mensagens
- Serviço + cache
- Serviço + API externa (mockada)

Nunca teste o sistema completo em um teste de integração — isso é E2E.

---

## 6. Testes de Contrato de API (Pact)

### Contratos Orientados ao Consumidor

```
Consumer (frontend/client)          Provider (backend/API)
        |                                   |
        |  1. Write consumer test           |
        |  2. Generate Pact file            |
        |                                   |
        |  --------- Pact file --------->   |
        |                                   |
        |                    3. Verify Pact against real API
        |                    4. Publish verification result
```

### Teste de Consumer (Python)

```python
from pact import Consumer, Provider

pact = Consumer("frontend").has_pact_with(
    Provider("user-service"),
    pact_dir="./pacts",
)

def test_get_user():
    expected = {"id": 1, "name": "Alice", "email": "alice@test.com"}

    (pact
     .given("a user with ID 1 exists")
     .upon_receiving("a request for user 1")
     .with_request("GET", "/users/1")
     .will_respond_with(200, body=expected))

    with pact:
        result = get_user(pact.uri, 1)
        assert result["name"] == "Alice"
```

### Quando Usar Testes de Contrato

- Microsserviços comunicando via HTTP/gRPC
- Frontend consumindo uma API de backend
- Múltiplos times mantendo serviços separados

### Quando NÃO Usar

- Aplicações monolíticas
- Um único time sendo dono tanto do consumer quanto do provider
- Fase inicial de prototipação

---

## 7. Testes de Performance

### Tipos de Teste

| Tipo | Propósito | Duração | Padrão de Carga |
|------|---------|----------|--------------|
| **Smoke** | Verificar se o sistema funciona sob carga mínima | 1-5 min | 1-5 VUs |
| **Load** | Validar sob tráfego esperado | 15-30 min | Ramp até os VUs alvo |
| **Stress** | Encontrar o ponto de ruptura | 30-60 min | Ramp além do alvo |
| **Soak** | Detectar vazamentos de memória | 2-8 horas | Carga alvo sustentada |
| **Spike** | Testar picos súbitos de tráfego | 5-10 min | Ramp súbito para cima/baixo |

### Exemplo k6

```javascript
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "2m", target: 50 },   // ramp up
    { duration: "5m", target: 50 },   // sustain
    { duration: "2m", target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],  // 95th percentile < 500ms
    http_req_failed: ["rate<0.01"],    // error rate < 1%
  },
};

export default function () {
  const res = http.get("https://api.example.com/users");
  check(res, {
    "status is 200": (r) => r.status === 200,
    "response time < 500ms": (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

### Exemplo Locust

```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_users(self) -> None:
        self.client.get("/users")

    @task(1)
    def create_user(self) -> None:
        self.client.post("/users", json={"name": "Test", "email": "t@t.com"})
```

### Orçamentos de Performance

| Métrica | Alvo |
|--------|--------|
| Tempo de resposta p95 | < 500ms |
| Tempo de resposta p99 | < 1000ms |
| Taxa de erro | < 0.1% |
| LCP (frontend) | < 2.5s |
| FID (frontend) | < 100ms |
| CLS (frontend) | < 0.1 |

---

## 8. Testes de Acessibilidade

### Testes Automatizados (detectam ~57% dos problemas de WCAG)

```python
# Playwright + axe-core (Python)
from axe_playwright_python.sync_playwright import Axe

def test_homepage_accessibility(page: Page) -> None:
    page.goto("/")
    axe = Axe()
    results = axe.run(page)
    assert results.violations_count == 0, results.generate_report()
```

```typescript
// TypeScript variant
import AxeBuilder from "@axe-core/playwright";

test("homepage has no a11y violations", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

### Critérios-Chave do WCAG 2.2

| Nível | Critério | O que |
|-------|-----------|------|
| A | 2.4.7 | Foco visível na navegação por teclado |
| AA | 1.4.3 | Razão de contraste >= 4.5:1 para texto |
| AA | 2.5.8 | Alvo de toque >= 24x24px |
| AA | 2.4.11 | Foco não obscurecido por elementos fixos (sticky) |

### O que a Automação Detecta

- Texto alternativo (alt) ausente em imagens
- Labels de formulário ausentes
- Contraste de cor insuficiente
- Atributos ARIA ausentes

### O que Requer Teste Manual

- Fluxo de navegação por teclado (ordem lógica de tab)
- Experiência com leitor de tela
- Gerenciamento de foco em conteúdo dinâmico (modais, drawers)
- Refluxo de conteúdo com zoom de 400%

---

## 9. Testes de Regressão Visual

### Abordagens

| Abordagem | Ferramenta | Prós | Contras |
|----------|------|------|------|
| **Comparação de pixels** | Playwright nativo | Grátis, sem dependências externas | Sensível a diffs de renderização |
| **Baseado em nuvem** | Percy, Chromatic | Cross-browser, diffing inteligente | Pago |
| **Nível de componente** | Storybook + Chromatic | Isolado, rápido | Apenas componentes, não páginas |

### Comparação de Screenshot com Playwright

```python
async def test_homepage_visual(page: Page) -> None:
    await page.goto("/")
    await expect(page).to_have_screenshot("homepage.png", max_diff_pixels=100)

# Disable animations for stable screenshots
await page.emulate_media(reduced_motion="reduce")
await page.add_style_tag(
    content="*, *::before, *::after { animation-duration: 0s !important; }"
)
```

### Quando Usar

- Componentes de design system
- Landing pages e páginas de marketing
- Após refatorações de CSS/Tailwind

---

## 10. Smoke Testing

Smoke tests são a **suíte de testes mínima viável** que valida se o sistema está vivo.
Execute após cada deployment.

### Características

- **Rápido:** < 2 minutos no total
- **Apenas caminhos críticos:** login, funcionalidade principal, health endpoints
- **Sem casos extremos:** apenas o happy path
- **Idempotente:** seguro executar várias vezes

```python
class SmokeTests:
    def test_health_endpoint(self, client) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_database_connectivity(self, client) -> None:
        response = client.get("/health/db")
        assert response.status_code == 200

    def test_login_works(self, client) -> None:
        response = client.post("/auth/login", json={
            "email": "smoke-test@example.com",
            "password": "smoke-test-password",
        })
        assert response.status_code == 200
        assert "token" in response.json()
```

### Smoke vs Sanity vs Regression

| Tipo | Escopo | Quando | Duração |
|------|-------|------|----------|
| **Smoke** | Apenas caminhos principais | Após deploy | < 2 min |
| **Sanity** | Funcionalidades alteradas | Após correção de bug | 5-15 min |
| **Regression** | Suíte completa | Antes do release | 30-120 min |

---

## 11. Definition of Done — Validação de Testes

Uma entrega está pronta SOMENTE quando todos estes itens forem verificados:

### Qualidade de Código
- [ ] Análise estática limpa (mypy, TypeScript, ruff, biome — zero warnings)
- [ ] Nenhum novo warning de lint
- [ ] Type hints completos

### Cobertura de Testes
- [ ] Testes unitários escritos para nova lógica de negócio
- [ ] Testes de integração para novos endpoints de API
- [ ] Testes E2E para novos fluxos visíveis ao usuário
- [ ] Cobertura de testes atinge o limiar do projeto

### Qualidade dos Testes
- [ ] Todos os testes determinísticos (nenhum teste flaky introduzido)
- [ ] Testes cobrem o happy path E os caminhos de erro
- [ ] Nomes dos testes descrevem o comportamento
- [ ] Nenhum teste comentado

### Ambiente
- [ ] Testes executam em ambiente isolado
- [ ] Ambiente faz teardown de forma limpa após os testes
- [ ] Nenhum conflito de porta

### Evidências
- [ ] Resultados dos testes documentados
- [ ] Relatório de cobertura gerado

---

## 12. Checklist de Prontidão para Produção

Antes de qualquer release:

### Testes
- [ ] Resultados completos de testes de regressão (contagens de pass/fail/skip)
- [ ] Relatório de cobertura (limiar de >80% atingido)
- [ ] Resultados de testes de performance (p95, p99, taxa de erro)
- [ ] Resultados de auditoria de acessibilidade (WCAG 2.2 AA)
- [ ] Smoke tests passando em staging
- [ ] Nenhum problema BLOCKER em aberto da revisão

### Operações
- [ ] Endpoints de health check implementados
- [ ] Logging estruturado configurado
- [ ] Métricas expostas (método RED)
- [ ] Alertas configurados para taxa de erro e latência
- [ ] Runbook existente para modos de falha conhecidos
- [ ] Procedimento de rollback documentado e testado

### Segurança
- [ ] Varredura SAST limpa (bandit, semgrep)
- [ ] Auditoria de dependências limpa (pip-audit, npm audit)
- [ ] Nenhum segredo no codebase
- [ ] Autenticação/autorização revisada

---

## Reference Files

- [references/accessibility-automated-testing.md](references/accessibility-automated-testing.md) — Testes Automatizados de Acessibilidade
- [references/contract-testing-pact.md](references/contract-testing-pact.md) — Testes de Contrato Orientados ao Consumidor com Pact
- [references/e2e-playwright.md](references/e2e-playwright.md) — Padrões de Testes E2E com Playwright
- [references/e2e-strategy.md](references/e2e-strategy.md) — Estratégia de Testes -- Pyramid vs Trophy
- [references/environment-setup-teardown.md](references/environment-setup-teardown.md) — Configuração e Teardown de Ambiente
- [references/integration-patterns.md](references/integration-patterns.md) — Padrões de Testes de Integração
- [references/performance-load-testing.md](references/performance-load-testing.md) — Testes de Carga
- [references/reporting-evidence-collection.md](references/reporting-evidence-collection.md) — Relatórios de Teste & Coleta de Evidências
- [references/test-data-management.md](references/test-data-management.md) — Gerenciamento de Dados de Teste
- [references/visual-regression-screenshot-testing.md](references/visual-regression-screenshot-testing.md) — Testes de Regressão Visual
## 13. QA Pré-Merge — O que Verificar Antes de Dizer PASS

Seis verificações estruturais que capturam o que as suítes automatizadas rotineiramente deixam passar.
Aplique em cada passagem de QA de PR antes de emitir um veredito.

### 13.1 Caminho de Smoke-Test Documentado

**Por quê:** Sem um caminho de teste manual documentado, o agente de QA precisa fazer engenharia reversa do
contrato de env-var em cada passagem e os revisores não conseguem reproduzir os resultados de forma independente.

**Procure por:** `TESTING.md`, seção de smoke-test no `CONTRIBUTING.md`, `.env.example` cobrindo
toda variável que o assistente de instalação lê, um script como `scripts/smoke_test.sh`.

**Quando ausente:** Registre uma constatação estrutural — não uma reclamação de doc ausente:
> "Nenhum caminho de smoke-test manual documentado existe. Adicione TESTING.md listando env vars,
> pré-requisitos, e a sequência exata de comandos para validar o fluxo principal em uma máquina limpa."

```bash
ls TESTING.md CONTRIBUTING.md docs/testing* 2>/dev/null
grep -ri "smoke\|TESTING" README.md 2>/dev/null | head -5
```

---

### 13.2 Nomes de Recursos Hardcoded Impedem Isolamento

**Por quê:** Nomes de container, portas ou caminhos hardcoded significam que duas execuções de teste não podem coexistir e
o container de teste pode colidir com um real do usuário.

**Procure por:** Literais de string para nomes de container, portas ou nomes de volume dentro de
comandos de instalação ou passos do assistente. Padrão: `name="my-app-service"`, `port=6333`.

**Quando encontrado:**
> "O nome de recurso '{name}' está hardcoded. Adicione um override via env-var (ex.: CONTAINER_NAME,
> CONTAINER_PORT) para que execuções paralelas isoladas e a separação teste-vs-produção sejam possíveis."

```bash
grep -rn 'name="' src/ --include="*.py" | grep -v test | head -20
grep -rn 'port\s*=\s*[0-9]\{4,5\}' src/ --include="*.py" | grep -v '#' | head -20
```

---

### 13.3 Rótulos de Checkpoint Devem Corresponder ao que Verificam

**Por quê:** Um passo que imprime "[OK]" enquanto engole exceções é uma mentira silenciosa — mais difícil de
debugar do que uma falha explícita, e engana operadores durante incidentes.

**Abordagem de teste:** Deliberadamente torne cada dependência indisponível (pare o daemon, bloqueie
a porta) e execute novamente. Se o passo ainda imprimir "[OK]", a verificação é vazia.

**Quando encontrado:**
> "[Step N] imprime '{label}' mas não lança erro quando {dependency} está inacessível. Propague
> a falha (raise/exit não-zero) para que o rótulo seja verdadeiro."

---

### 13.4 Contrato de Idioma/Locale para Fluxos Interativos

**Por quê:** Misturar o idioma da UI com o locale padrão de uma biblioteca faz com que entradas válidas do usuário
(ex.: 's' para 'sim') sejam rejeitadas como "entrada inválida".

**Procure por:** O idioma de contrato do projeto — verifique `locale/`, `i18n/`, arquivos de template,
ou literais de string usados em prompts de CLI. Se os prompts estão no idioma X, toda
confirmação interativa também deve aceitar as entradas afirmativas/negativas daquele idioma.

**Abordagem de teste:** Execute cada passo do assistente de ponta a ponta usando as entradas esperadas
do idioma de contrato. Confirme que nenhum prompt recai no padrão de um locale diferente.

**Quando encontrado:**
> "O prompt de confirmação no passo N renderiza '{library_default}' mas o contrato da UI é
> {language}. Sobrescreva as opções do prompt para corresponder ao idioma de contrato."

---

### 13.5 Baseline de Falhas de Teste Antes da Branch do PR

**Por quê:** `make check` terminando em N falhas é ambíguo sem um baseline — novas regressões
parecem idênticas a falhas pré-existentes.

**Protocolo:**
```bash
# On the merge-target branch first
git stash && git checkout <target-branch>
make check 2>&1 | tail -20   # record: N passed, N failed, N skipped
git checkout -
make check 2>&1 | tail -20   # compute delta: (PR failures) - (baseline failures)
```

**Quando o baseline está vermelho e as falhas não estão marcadas:**
> "make check em {target-branch} termina com {N} falhas. Falhas pré-existentes devem ser
> marcadas com @pytest.mark.xfail ou listadas em known_failures.txt para que regressões sejam imediatamente
> distinguíveis do débito conhecido."

---

### 13.6 Smoke Tests de CLI em Nível de Subprocesso

**Por quê:** Testes unitários mockados verificam apenas o encanamento interno. O caminho do usuário passa pelo
entry point instalado; testes em nível de subprocesso são a única forma de o CI capturar falhas de instalação,
importação e parsing de argumentos.

**Procure por:** Arquivos de teste chamando `subprocess.run(["<cli>", ...])` ou usando o
`CliRunner` do framework contra o entry point *instalado* — não uma função importada diretamente.

**Quando ausente:** Registre uma constatação estrutural:
> "Todos os testes de CLI mockam a implementação. Adicione ao menos um smoke test em nível de subprocesso
> que invoque o entry point instalado para que o CI valide o caminho do usuário, não apenas o encanamento
> interno."

```python
import subprocess

def test_cli_entrypoint_reachable():
    result = subprocess.run(["<cli>", "--help"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
```
