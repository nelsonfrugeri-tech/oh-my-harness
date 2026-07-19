# Grafana

## Boas práticas de dashboards

### Variáveis
```
$namespace = label_values(kube_namespace_created, namespace)
$service = label_values(up{namespace="$namespace"}, job)
```

### Tipos de painel por caso de uso
| Dados | Painel |
|------|-------|
| Tendências em séries temporais | Time series |
| Valor atual | Stat / Gauge |
| Comparações | Bar chart |
| Visão geral de status | State timeline |
| Logs | Painel de logs (datasource Loki) |

### Anotações
- Anotar deploys automaticamente: webhook do ArgoCD → API de anotações do Grafana
- Marcadores de incidente: integração com PagerDuty

### Versão: Grafana 11.x (estável em 2026)
