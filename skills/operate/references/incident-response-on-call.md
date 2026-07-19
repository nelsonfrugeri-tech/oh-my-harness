# Boas Práticas de On-Call

## Design da Rotação
- **Duração**: rotações de 1 semana (mais curtas causam overhead de troca de contexto)
- **Overlap**: handoff de 30min entre rotações
- **Shadow**: novos membros da equipe acompanham (shadow) por 1-2 rotações antes de assumir como primário
- **Follow-the-sun**: distribua entre fusos horários para cobertura 24/7 sem turnos noturnos

## Protocolo de Handoff
1. Quem está saindo escreve o documento de handoff: incidentes ativos, investigações em andamento, mudanças agendadas
2. Sync ao vivo de 30 min cobrindo o estado atual
3. Verifique se as rotas de alerta apontam para o on-call que está entrando
4. Transfira o pager/telefone

## Redução de Fadiga de Alertas
- Meta: <5 pages acionáveis por turno de on-call
- Todo alerta deve ter um runbook vinculado
- Silencie (snooze) alertas ruidosos e crie tickets para corrigir thresholds
- Revise mensalmente a relação sinal-ruído dos alertas

## Matriz de Escalação
```
L1 (0-15min): On-call engineer — diagnose and mitigate
L2 (15-30min): Secondary on-call or team lead
L3 (30min+): Incident commander, cross-team escalation
L4 (1h+, P1): VP/Director-level awareness
```

## Compensação
- Bônus (stipend) pago pelo on-call (não apenas "parte do trabalho")
- Folga após incidentes de alta severidade
- Compromissos de sprint reduzidos durante as semanas de on-call

## Ferramentas
- PagerDuty / Opsgenie para roteamento e escalação de alertas
- Canal de incidente no Slack criado automaticamente por incidente
- Atualizações da status page automatizadas via API
