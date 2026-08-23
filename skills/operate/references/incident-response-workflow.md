# Fluxo de Resposta a Incidentes

## As Cinco Fases

### 1. Detectar

**Objetivo:** Minimizar o time-to-detection (TTD).

- Alertas baseados em sintomas disparam (impacto visível ao usuário, não causa interna)
- Alertas de burn-rate na trajetória de violação do SLO
- Relatos de clientes via canais de suporte
- Falhas de monitoramento sintético

**Métrica chave:** TTD = tempo do início do incidente até o primeiro alerta.

### 2. Triagem

**Objetivo:** Avaliar a severidade, reunir os responders, comunicar.

**Níveis de severidade:**

| Nível | Impacto | Tempo de Resposta | Exemplo |
|-------|--------|---------------|---------|
| SEV1 | Indisponibilidade total, perda de dados | Imediato, all-hands | Sistema de pagamento fora do ar |
| SEV2 | Degradação grave | 15 min, equipe de on-call | 50% de taxa de erro |
| SEV3 | Degradação leve | 1 hora, on-call primário | Respostas lentas, uma região |
| SEV4 | Baixo impacto | Próximo dia útil | Problemas cosméticos |

**Ações de triagem:**
1. Designe o Incident Commander (IC)
2. Abra o canal de incidente (Slack #inc-YYYYMMDD-short-desc)
3. Poste a avaliação inicial: o quê, quando, quem é afetado, severidade
4. Acione (page) responders adicionais se necessário

### 3. Mitigar

**Objetivo:** Restaurar o serviço o mais rápido possível. Corrija depois, mitigue agora.

**Mitigações comuns:**
- Rollback do deployment
- Desligar feature flag
- Scale up / failover
- Rate limit / shed load
- Redirecionar o tráfego para uma região saudável
- Reiniciar processos que travaram

**Anti-padrões:**
- Depurar a causa raiz antes de mitigar
- Fazer mudanças não testadas em prod
- Várias pessoas fazendo mudanças simultaneamente sem coordenação

### 4. Resolver

**Objetivo:** Confirmar a recuperação total, monitorar recorrência.

- Verifique se todas as métricas voltaram ao baseline
- Confirme via synthetic checks e monitoramento de usuários reais
- Remova as mitigações temporárias (ou documente se permanecerem)
- Feche o canal de incidente com um resumo
- Atualize a status page

### 5. Postmortem

**Objetivo:** Aprender e prevenir recorrência. Consulte `postmortem-template.md`.

**Prazos:**
- Rascunho em até 48 horas
- Revisão em até 1 semana
- Itens de ação acompanhados até a conclusão

## Comunicação Durante Incidentes

### Template de Atualização de Status

```
[HH:MM UTC] Status Update #N
Impact: {what users see}
Current status: {investigating | mitigating | monitoring | resolved}
Next update: {time or "in 30 minutes"}
```

### Cadência
- SEV1: A cada 15 minutos
- SEV2: A cada 30 minutos
- SEV3: A cada hora

## Papéis

| Papel | Responsabilidade |
|------|---------------|
| **Incident Commander** | Coordena a resposta, delega, comunica |
| **Tech Lead** | Conduz a investigação técnica e a mitigação |
| **Communications** | Atualiza a status page, stakeholders, clientes |
| **Scribe** | Documenta a linha do tempo, ações, decisões |

## Checklist Pós-Incidente

- [ ] Linha do tempo documentada
- [ ] Causa raiz identificada (consulte `root-cause-analysis.md`)
- [ ] Postmortem escrito (consulte `postmortem-template.md`)
- [ ] Itens de ação criados com responsáveis e prazos
- [ ] Runbook atualizado se aplicável
- [ ] Lacunas de monitoramento/alertas tratadas
