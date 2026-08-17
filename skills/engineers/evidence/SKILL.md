---
version: 1.0.0
name: evidence
description: |
  Raciocínio orientado a evidência para alegações e decisões de engenharia de software. Cobre a
  taxonomia de alegações (fato verificado, resultado derivado, inferência, hipótese, estimativa,
  desconhecido, decisão), proveniência quantitativa (unidade, população, janela temporal, fonte e
  método), o protocolo de decisão para trade-offs materiais e hotfixes, e a rubrica de review
  independente de evidência.
  Use quando: (1) design de feature, diagnóstico de bug ou análise de causa raiz, (2) arquitetura,
  priorização, implementação, review, entrega ou operações, (3) métricas, estimativas, benchmarks e
  trade-offs — sempre que fatos precisarem ser separados de hipóteses ou uma escolha material
  precisar de evidência defensável.
  Gatilhos: evidence, evidência, fato vs hipótese, decisão orientada a dados, causa raiz.
type: capability
---

# Engenharia de Software Orientada a Evidência

Torne alegações de software rastreáveis e decisões testáveis, sem bloquear progresso seguro quando a
evidência é incompleta. Trate o contrato global de software-evidence como vinculante.

## Aplique o workflow

1. **Enquadre a alegação ou decisão.** Defina escopo, população afetada, janela temporal e impacto.
2. **Inventarie o registro atual.** Separe fatos verificados, resultados derivados, inferências,
   hipóteses, estimativas, desconhecidos e decisões.
3. **Inspecione a evidência mais forte disponível.** Prefira observações diretas do repositório,
   testes executados, telemetria, comandos reprodutíveis e fontes primárias versionadas.
4. **Cheque proveniência e escopo.** Rejeite ou rerrotule alegações que excedem o que a evidência
   prova.
5. **Reduza a incerteza relevante para a decisão.** Selecione a observação mais barata que distingue
   hipóteses concorrentes ou muda materialmente o trade-off.
6. **Decida proporcionalmente.** Compare alternativas, reversibilidade, blast radius, custo de
   atraso e custo do erro. Evidência fraca pede passos menores, observáveis e reversíveis.
7. **Pré-registre a validação.** Defina condições de sucesso, guardrail, falsificação, rollback e
   revisão antes de observar o resultado.
8. **Comunique o status.** Cite a evidência junto de cada alegação material e rotule o que permanece
   incerto.

## Preserve a incerteza útil

Não fabrique certeza para uma resposta parecer completa. Uma hipótese segura pode sustentar um
experimento ou uma implementação reversível quando inclui uma previsão falsificável. Uma estimativa
pode sustentar planejamento quando suas premissas e incerteza estão visíveis. Um desconhecido se
torna acionável quando seu impacto na decisão e a próxima observação estão declarados.

Não alegue causa raiz a partir de correlação, bug corrigido a partir de um teste que passou, saúde
de produção a partir de configuração, nem verdade atual a partir de histórico de sessão. Estreite a
afirmação ou obtenha a observação que falta.

## Desafie decisões colaborativamente

Para uma proposta material, identifique o risco mais forte sustentado por evidência, apresente o
caso razoável mais forte a favor dela, ofereça uma alternativa viável e diga que evidência mudaria a
recomendação. Solicite um `evidence-reviewer` independente quando impacto, irreversibilidade ou
incerteza tornarem o self-review insuficiente.

Trate uma decisão como material quando ela pode afetar usuários de produção, segurança, privacidade,
integridade de dados, gasto significativo, múltiplos times ou um rollback difícil — ou quando uma
métrica sem sustentação ou uma alegação causal controla o resultado. Escolhas rotineiras e
reversíveis não exigem review independente.

## Carregue a referência relevante

- Use [claim-taxonomy.md](references/claim-taxonomy.md) para classificar alegações e validar
  proveniência.
- Use [decision-protocol.md](references/decision-protocol.md) para trade-offs materiais e decisões
  de hotfix.
- Use [review-rubric.md](references/review-rubric.md) para review independente de evidência.
