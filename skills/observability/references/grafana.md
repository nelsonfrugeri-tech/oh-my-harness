# Grafana

## Boas Práticas de Dashboard

### Variáveis
```
$namespace = label_values(kube_namespace_created, namespace)
$service = label_values(up{namespace="$namespace"}, job)
```

### Tipos de Painel por Caso de Uso
| Dados | Painel |
|------|-------|
| Tendências de séries temporais | Time series |
| Valor atual | Stat / Gauge |
| Comparações | Bar chart |
| Visão geral de status | State timeline |
| Logs | Logs panel (Loki datasource) |

### Anotações
- Auto-anotar deploys: webhook do ArgoCD → API de anotações do Grafana
- Marcadores de incidente: integração com PagerDuty

### Versão: Grafana 11.x (estável em 2026)
