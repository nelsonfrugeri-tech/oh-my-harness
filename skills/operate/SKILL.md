---
version: 1.0.0
name: operate
description: |
  Base de conhecimento de SRE e observabilidade moderna (2026). Cobre os três pilares de
  observabilidade (logs, métricas, traces) com OpenTelemetry como padrão, definição de SLI/SLO
  e gestão de error budget, fluxo de resposta a incidentes (DETECT-TRIAGE-MITIGATE-RESOLVE-POSTMORTEM),
  alerting baseado em sintomas (multi-window multi-burn-rate), padrões de dashboard (USE, RED, Four
  Golden Signals), otimização de custo, análise de causa raiz, templates de runbook e boas práticas
  de on-call. Ferramentas: Prometheus, Grafana, Jaeger, OpenTelemetry.
  Use quando: (1) Instrumentar aplicações, (2) Definir SLOs e error budgets,
  (3) Configurar alerting e dashboards, (4) Responder a incidentes, (5) Escrever runbooks,
  (6) Configurar on-call.
  Triggers: /operate, /sre, /observability, SRE, observability, monitoring, alerting, SLO, SLI,
  incident response, postmortem, on-call, dashboards, OpenTelemetry.
type: capability
---

# Operate — SRE e Observabilidade

## Propósito

Esta skill é a base de conhecimento para SRE e observabilidade moderna (2026).

**O que esta skill contém:**
- Pilares de observabilidade (logs, métricas, traces) com OpenTelemetry
- Definição de SLO/SLI e gestão de error budget
- Fluxo de resposta a incidentes (DETECT → TRIAGE → MITIGATE → RESOLVE → POSTMORTEM)
- Estratégias de alerting (baseadas em sintomas)
- Padrões de dashboard (USE, RED, Four Golden Signals)
- Otimização de custo para observabilidade
- Análise de causa raiz (5 Whys, fault trees)
- Templates de runbook
- Boas práticas de on-call

---

## Filosofia

### Observabilidade != Monitoramento

**Monitoramento** diz QUANDO algo está errado.
**Observabilidade** diz POR QUE algo está errado.

Um sistema é observável quando você consegue entender seu estado interno a partir de sinais externos
— sem precisar fazer deploy de código novo para depurar.

### Princípios Fundamentais

1. **OpenTelemetry é o padrão** — vendor-neutral, um único SDK para tudo
2. **SLOs guiam decisões** — error budgets quantificam "quanto posso falhar"
3. **Alerting baseado em sintomas** — alerte sobre impacto no usuário, não sobre causas internas
4. **Cultura blameless** — incidentes são oportunidades de aprendizado, não atribuição de culpa
5. **Consciente de custo** — telemetria tem custo, otimize a relação sinal-ruído

---

## 1. Pilares de Observabilidade

### Os Três Pilares + Eventos

| Pilar | O que | Quando | Ferramenta |
|--------|------|------|------|
| **Logs** | Eventos discretos com contexto | Debug, trilha de auditoria, compliance | OpenTelemetry Logs, structlog |
| **Métricas** | Valores numéricos ao longo do tempo | Tendências, alerting, planejamento de capacidade | Prometheus, OpenTelemetry Metrics |
| **Traces** | Caminho da requisição entre serviços | Análise de latência, mapeamento de dependências | Jaeger, OpenTelemetry Traces |
| **Eventos** | Mudanças de estado significativas | Deployments, mudanças de config, incidentes | Eventos customizados, anotações |

### Setup do OpenTelemetry (Python)

```python
# opentelemetry-sdk==1.40.0
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

resource = Resource.create({
    "service.name": "my-service",
    "service.version": "1.0.0",
    "deployment.environment": "production",
})

# Traces
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
)
trace.set_tracer_provider(tracer_provider)

# Usage
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_order") as span:
    span.set_attribute("order.id", order_id)
    span.set_attribute("order.total", total)
    span.add_event("payment_processed", {"method": "credit_card"})
    try:
        result = process_payment(order_id)
    except Exception as e:
        span.set_status(trace.StatusCode.ERROR, str(e))
        span.record_exception(e)
        raise
```

### Logging Estruturado com Contexto OTel

```python
import structlog
from opentelemetry import trace

def add_otel_context(logger, method_name, event_dict):
    """Add OpenTelemetry trace context to log entries."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_otel_context,
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()
logger.info("order_created", order_id="abc-123", total=99.99)
# {"level":"info","timestamp":"...","trace_id":"...","order_id":"abc-123","event":"order_created"}
```

---

## 2. Gestão de SLI/SLO

### Definições

| Conceito | O que | Exemplo |
|---------|------|---------|
| **SLI** | Métrica quantitativa de um aspecto do serviço | 99.2% das requisições < 200ms |
| **SLO** | Alvo para um SLI | 99.5% das requisições devem ser < 200ms |
| **SLA** | Contrato com consequências | 99.9% de uptime ou créditos |
| **Error Budget** | 100% - SLO | 0.5% = orçamento para experimentar/falhar |

### Fórmula do SLI

```
SLI = (good events / total events) * 100

# Availability SLI
availability = (successful_requests / total_requests) * 100

# Latency SLI
latency = (requests_under_threshold / total_requests) * 100
```

### Escolhendo SLIs por Tipo de Serviço

| Tipo de Serviço | SLIs Primários |
|-------------|-------------|
| **API** | Availability, Latency (p50, p95, p99), Error rate |
| **Pipeline** | Freshness (idade dos dados), Correctness, Throughput |
| **Storage** | Availability, Latency, Durability |
| **Frontend** | LCP, FID, CLS (Core Web Vitals) |
| **AI/LLM** | Latency, Correctness (eval score), Token cost, Error rate |

### Error Budget Policy

```markdown
## Error Budget Policy for [Service]

### Budget calculation
- SLO: 99.5% availability (28-day rolling window)
- Error budget: 0.5% = ~201 minutes / 28 days

### When budget is healthy (>50% remaining)
- Ship features freely
- Experiment with new deployments
- Perform maintenance

### When budget is low (10-50% remaining)
- Slow down feature releases
- Prioritize reliability work
- Increase test coverage

### When budget is exhausted (<10% remaining)
- Feature freeze
- All hands on reliability
- Mandatory postmortem for any new incident
- Rollback risky changes
```

---

## 3. Fluxo de Resposta a Incidentes

```
DETECT -> TRIAGE -> MITIGATE -> RESOLVE -> POSTMORTEM -> IMPROVE
```

### Fase 1: Detect

**Fontes:** Alertas automatizados, reports de clientes, monitoramento sintético, detecção de anomalias

**Regras:**
- Time-to-detect (TTD) é a métrica mais crítica
- Alerte sobre sintomas, não sobre causas
- Todo alerta deve ser acionável

### Fase 2: Triage

**Classificação de severidade:**

| Severidade | Impacto | Tempo de Resposta | Exemplos |
|----------|--------|---------------|---------|
| **SEV-0** | Outage total, perda de dados | Imediato (all hands) | Corrupção de banco, brecha de segurança |
| **SEV-1** | Feature principal quebrada | < 15 min | Pagamento fora do ar, falha de auth |
| **SEV-2** | Serviço degradado | < 30 min | Latência elevada, erros parciais |
| **SEV-3** | Problema menor | < 4 horas | Feature não crítica degradada |

**Papéis:**
- **Incident Commander (IC)** — coordena a resposta, toma decisões
- **Communications Lead (CL)** — atualiza stakeholders, status page
- **Operations Lead (OL)** — debugging e mitigação hands-on

### Fase 3: Mitigate

**Ordem de prioridade:**
1. **Rollback** — voltar ao último estado bom conhecido
2. **Drain** — remover a instância afetada da rotação
3. **Scale** — adicionar capacidade se limitado por recursos
4. **Feature flag** — desabilitar a feature problemática
5. **Hotfix** — apenas se as opções acima não funcionarem

**Regra:** Mitigue primeiro, depure depois. Restaure o serviço o quanto antes.

### Fase 4: Resolve

- Confirme que o serviço se recuperou totalmente
- Verifique se as métricas de SLI voltaram ao normal
- Monitore por regressão (30+ minutos)
- Feche o canal do incidente

### Fase 5: Postmortem Blameless

```markdown
## Postmortem: [Incident Title]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** SEV-N
**Incident Commander:** [name]

### Summary
[1-2 sentences describing what happened]

### Impact
- [N users affected]
- [N minutes of downtime]
- [Error budget consumed: X%]

### Timeline (UTC)
| Time | Event |
|------|-------|
| HH:MM | Alert fired: [alert name] |
| HH:MM | IC declared, triage started |
| HH:MM | Root cause identified: [cause] |
| HH:MM | Mitigation applied: [action] |
| HH:MM | Service restored |

### Root Cause
[Technical description of what went wrong]

### Contributing Factors
- [system or process factor, not person]

### What Went Well
- [item]

### What Went Wrong
- [item]

### Action Items
| Action | Owner | Priority | Due Date |
|--------|-------|----------|----------|
| [action] | [name] | P0/P1/P2 | YYYY-MM-DD |

### Lessons Learned
- [key takeaway]
```

### Fase 6: Improve

- Acompanhe os action items até a conclusão
- Atualize os runbooks com o que foi aprendido
- Melhore os alertas com base nas lacunas de detecção
- Adicione testes automatizados para o modo de falha

---

## 4. Estratégia de Alerting

### Alerting Baseado em Sintomas

```
BAD:  Alert on CPU > 80%         (cause — may have no user impact)
GOOD: Alert on error rate > 1%   (symptom — users are affected)

BAD:  Alert on disk > 90%        (cause — might be fine for weeks)
GOOD: Alert on write failures > 0 (symptom — data loss happening)
```

### Alertas Multi-Window Multi-Burn-Rate

```yaml
# Prometheus alerting rules
groups:
  - name: slo_alerts
    rules:
      # Fast burn: 2% budget in 1 hour = 14.4x burn
      - alert: ErrorBudgetBurnFast
        expr: |
          slo:http_request_error_ratio:rate1h > (14.4 * 0.005)
          and
          slo:http_request_error_ratio:rate5m > (14.4 * 0.005)
        for: 2m
        labels:
          severity: critical
          page: "true"
        annotations:
          summary: "Fast error budget burn ({{ $value | humanizePercentage }})"

      # Slow burn: 5% budget in 6 hours = 1.2x burn
      - alert: ErrorBudgetBurnSlow
        expr: |
          slo:http_request_error_ratio:rate6h > (1.2 * 0.005)
          and
          slo:http_request_error_ratio:rate30m > (1.2 * 0.005)
        for: 15m
        labels:
          severity: warning
          ticket: "true"
        annotations:
          summary: "Slow error budget burn ({{ $value | humanizePercentage }})"
```

### Checklist de Qualidade de Alertas

```markdown
For every alert:
- [ ] Based on a symptom (user impact), not a cause
- [ ] Has a runbook linked
- [ ] Has clear severity and routing
- [ ] Fires for >= 2 minutes (reduce flapping)
- [ ] Tested to confirm it fires when it should
- [ ] Actionable — engineer knows what to do
- [ ] Has been silent for >= 1 week without manual action -> delete/improve
```

---

## 5. Padrões de Dashboard

### Método RED (para serviços orientados a requisições)

| Métrica | O que | Exemplo de SLO |
|--------|------|-------------|
| **R**ate | Requisições por segundo | Sustentar 5K rps |
| **E**rrors | Percentual de taxa de erro | < 0.1% 5xx |
| **D**uration | Distribuição de latência | p99 < 200ms |

### Método USE (para recursos)

| Métrica | O que |
|--------|------|
| **U**tilization | % do tempo em que o recurso está ocupado (CPU, memória) |
| **S**aturation | Quanto trabalho está enfileirado (aguardando) |
| **E**rrors | Contagem de erros por recurso |

### Four Golden Signals (Google SRE)

1. **Latency** — tempo para atender uma requisição
2. **Traffic** — demanda sobre o sistema
3. **Errors** — taxa de requisições que falham
4. **Saturation** — quão "cheio" o serviço está

### Estrutura do Dashboard de Visão Geral do Serviço

```
Row 1: SLO Status
  - Error budget remaining (gauge)
  - Burn rate (last 1h, 6h, 1d)
  - Availability SLI (last 28d)

Row 2: RED Metrics
  - Request rate (graph)
  - Error rate (graph)
  - P50/P95/P99 latency (graph)

Row 3: Infrastructure
  - CPU utilization
  - Memory utilization
  - Disk I/O

Row 4: Dependencies
  - Database query duration
  - External API call duration
  - Cache hit rate
```

---

## 6. Template de Runbook

```markdown
# Runbook: [Service/Component Name]

## Purpose
[What this service does and why it matters]

## On-call Contact
- Primary: [team/person]
- Escalation: [manager/senior]

## Service URLs
- Production: [URL]
- Monitoring: [Grafana dashboard URL]
- Logs: [log aggregation URL]
- Traces: [Jaeger/tracing URL]

## Architecture Overview
[Brief description of dependencies]

## Common Failure Modes

### Symptom: High Error Rate (> 1%)
**Investigation:**
1. Check error logs: `{log query}`
2. Check recent deployments: `{command}`
3. Check database health: `{command}`

**Mitigation:**
- Rollback: `{command}`
- Scale up: `{command}`
- Enable circuit breaker: `{command}`

**Escalate if:** Error rate > 5% for more than 5 minutes

---

### Symptom: High Latency (p99 > 1s)
**Investigation:**
1. Check slow query log
2. Check trace for bottleneck
3. Check resource utilization

**Mitigation:**
- Restart service: `docker compose restart api`
- Flush cache: `{command}`

---

## Deployment
**Deploy command:** `{command}`
**Rollback command:** `{command}`
**Health check:** `curl -sf {url}/health`

## Maintenance
**Scheduled maintenance window:** [schedule]
**Notify:** [stakeholders to notify]
```

---

## 7. Boas Práticas de On-Call

### Cultura de On-Call Saudável

1. **Rotações sustentáveis** — sem cultura de herói, distribua a carga
2. **Postmortems blameless** — sistemas falham, não pessoas
3. **Higiene de alertas** — reduza ruído, todo alerta acionável
4. **Runbooks sempre atualizados** — atualize após cada incidente
5. **Handoffs de on-call** — resumo escrito das questões ativas

### Métricas de On-Call a Acompanhar

| Métrica | Alvo | Por quê |
|--------|--------|-----|
| MTTA (Mean Time to Acknowledge) | < 5 min | Detectar lacunas na cobertura |
| MTTM (Mean Time to Mitigate) | < 1 hora para SEV-1 | Medir a eficácia da resposta |
| Alertas por semana de on-call | < 5 acionáveis | Medir a qualidade dos alertas |
| Pages fora do horário comercial | < 2/semana | Medir a sustentabilidade |

### Handoff de Turno de On-Call

```markdown
## On-Call Handoff: [date]

### Active Incidents
- [none / link to incident]

### Ongoing Issues (watch list)
- {issue}: {status, what to watch for}

### Recent Deployments
- {service} {version}: deployed {date}, {status}

### Known Flaky Alerts
- {alert name}: {why it's noisy, when to ignore}

### Action Items
- {item}: {owner}
```

---

## Reference Files

- [references/alerting-burn-rate.md](references/alerting-burn-rate.md) — Alerting Multi-Window por Burn Rate
- [references/alerting-symptom-based.md](references/alerting-symptom-based.md) — Alerting Baseado em Sintomas
- [references/dashboards-patterns.md](references/dashboards-patterns.md) — Padrões de Dashboard
- [references/incident-response-on-call.md](references/incident-response-on-call.md) — Boas Práticas de On-Call
- [references/incident-response-postmortem-template.md](references/incident-response-postmortem-template.md) — Template de Postmortem Blameless
- [references/incident-response-root-cause-analysis.md](references/incident-response-root-cause-analysis.md) — Técnicas de Análise de Causa Raiz
- [references/incident-response-runbook-template.md](references/incident-response-runbook-template.md) — Template de Runbook
- [references/incident-response-workflow.md](references/incident-response-workflow.md) — Fluxo de Resposta a Incidentes
- [references/opentelemetry-instrumentation.md](references/opentelemetry-instrumentation.md) — Instrumentação do SDK OpenTelemetry
- [references/opentelemetry-setup.md](references/opentelemetry-setup.md) — Setup do OpenTelemetry em Python
- [references/slo-management-defining-slos.md](references/slo-management-defining-slos.md) — Definindo SLOs
- [references/slo-management-error-budgets.md](references/slo-management-error-budgets.md) — Error Budgets
- [references/tools-cost-optimization.md](references/tools-cost-optimization.md) — Otimização de Custo
- [references/tools-grafana.md](references/tools-grafana.md) — Grafana
- [references/tools-jaeger.md](references/tools-jaeger.md) — Jaeger
- [references/tools-langfuse.md](references/tools-langfuse.md) — Langfuse
- [references/tools-prometheus.md](references/tools-prometheus.md) — Prometheus