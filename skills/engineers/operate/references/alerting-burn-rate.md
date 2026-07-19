# Alertas de Burn Rate Multi-Janela

## Conceito
Em vez de thresholds estáticos, alerte com base na rapidez com que o error budget está sendo consumido.

## Fórmula
```
burn_rate = (error_rate_observed / error_rate_allowed)
error_rate_allowed = (1 - SLO_target) / window_days
```

## Estratégia Multi-Janela (Google SRE)
Duas janelas por alerta para equilibrar velocidade vs ruído:
- **Janela longa**: detecta problemas sustentados
- **Janela curta**: confirma que o problema ainda está ocorrendo (evita alerta em spike já resolvido)

```promql
# P1: 2% budget in 1 hour (burn rate 14.4x)
alert: SLOBurnRateHigh
expr: |
  (
    sum(rate(http_errors_total[1h])) / sum(rate(http_requests_total[1h])) > (14.4 * 0.001)
  ) and (
    sum(rate(http_errors_total[5m])) / sum(rate(http_requests_total[5m])) > (14.4 * 0.001)
  )
labels:
  severity: critical

# P2: 5% budget in 6 hours (burn rate 6x)  
alert: SLOBurnRateMedium
expr: |
  (
    sum(rate(http_errors_total[6h])) / sum(rate(http_requests_total[6h])) > (6 * 0.001)
  ) and (
    sum(rate(http_errors_total[30m])) / sum(rate(http_requests_total[30m])) > (6 * 0.001)
  )
labels:
  severity: warning
```

## Ajuste
- Comece com as janelas recomendadas pelo Google e ajuste com base no tempo de resposta da equipe
- Sensível demais → fadiga de alertas; frouxo demais → perde problemas reais
- Sempre combine com um dashboard de error budget para dar contexto
