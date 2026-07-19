# Otimização de custos

## Otimização de custos

### Cardinalidade de Métricas
- Alta cardinalidade = alto custo (labels com user_id, request_id)
- Meta: < 10K séries temporais únicas por serviço
- Use recording rules para pré-agregar e depois descarte as métricas brutas de alta cardinalidade

### Estratégias de Sampling
| Dados | Sampling |
|------|----------|
| Métricas | Manter tudo (agregadas por natureza) |
| Traces | 1-10% head-based, 100% para erros |
| Logs | Filtrar debug/trace em produção |

### Políticas de Retenção
| Resolução | Retenção |
|-----------|-----------|
| Raw (15s) | 7 dias |
| 1min com downsample | 30 dias |
| 5min com downsample | 1 ano |
| Alertas/incidentes | Para sempre |

### Ganhos Rápidos
1. Descarte métricas não utilizadas (`metric_relabel_configs`)
2. Aumente o intervalo de scrape para serviços não críticos (30s → 60s)
3. Use exemplars em vez de labels de alta cardinalidade
4. Compacte logs: JSON estruturado, sem stack traces para erros conhecidos
