# Técnicas de Análise de Causa Raiz

## 1. Cinco Porquês

Pergunte "por quê" iterativamente para descascar as camadas do sintoma até a causa raiz.

```
Problem: Users getting 500 errors on checkout
Why 1: The payment service is returning errors
Why 2: The payment service can't connect to the database
Why 3: The database connection pool is exhausted
Why 4: A new query is holding connections for 30+ seconds
Why 5: The query lacks an index on the orders.user_id column
Root cause: Missing database index causing slow queries under load
```

**Dicas:**
- Não pare no primeiro "erro humano" -- pergunte por que o sistema permitiu isso
- Múltiplas ramificações são normais (nem sempre linear)
- 5 é uma diretriz, não uma regra -- pare quando alcançar uma causa sistêmica acionável
- Evite "por que alguém não..." -- foque nas lacunas do sistema

## 2. Análise de Árvore de Falhas (FTA)

Análise dedutiva top-down usando gates AND/OR.

```
                    [Service Outage]
                         |
                    [OR gate]
                   /          \
    [Database failure]    [Network failure]
          |                      |
     [OR gate]              [AND gate]
     /       \              /        \
[Disk full] [OOM]   [Switch down] [No failover]
```

**Quando usar:** Incidentes complexos com múltiplas causas potenciais.
Útil para identificar pontos únicos de falha.

## 3. Diagrama de Ishikawa (Espinha de Peixe)

Categorize os fatores contribuintes ao longo de seis ramos:

```
People --------+
Methods -------+
Machines ------+----> [Incident]
Materials -----+
Measurements --+
Environment ---+
```

**Categorias adaptadas para SRE:**

| Categoria | Exemplos |
|----------|---------|
| **People** | Lacunas de treinamento, falhas de handoff, fadiga |
| **Process** | Runbook ausente, sem revisão de mudança, sem plano de rollback |
| **Technology** | Ponto único de falha, monitoramento ausente, defaults ruins |
| **Environment** | Problema no cloud provider, rede, DNS |
| **Data** | Dados corrompidos, incompatibilidade de schema, validação ausente |
| **Dependencies** | Indisponibilidade de terceiros, mudança de API, expiração de certificado |

## 4. Análise de Linha do Tempo

Plote cada evento em uma linha do tempo para identificar:
- **Lacunas:** Longos períodos sem ação (atraso de detecção?)
- **Cascatas:** Evento A causou B causou C
- **Pistas falsas:** Tempo gasto investigando a causa errada
- **Pontos de decisão:** Onde escolhas diferentes mudariam o resultado

## 5. Análise de Mudanças

Compare o estado antes e depois do incidente:
- O que mudou nas últimas 24h? (deploys, configs, infra)
- O que não mudou mas deveria ter mudado? (certificados vencidos, sem patch)
- Use `git log`, logs de deploy, histórico de gerenciamento de configuração

## Escolhendo uma Técnica

| Técnica | Melhor Para | Complexidade |
|-----------|----------|-----------|
| 5 Porquês | Incidentes simples, de causa única | Baixa |
| Árvore de Falhas | Complexo, múltiplas causas potenciais | Média |
| Ishikawa | Exploração ampla, muitos fatores contribuintes | Média |
| Linha do Tempo | Entender sequência e atrasos | Baixa |
| Mudanças | Incidentes correlacionados a mudanças recentes | Baixa |

## Anti-Padrões

- Parar no "erro humano" -- sempre pergunte que lacuna do sistema permitiu isso
- Viés de causa raiz única -- a maioria dos incidentes tem múltiplos fatores contribuintes
- Viés de confirmação -- não apenas valide sua primeira teoria
- Enquadramento de culpa -- "quem" nunca é a causa raiz
