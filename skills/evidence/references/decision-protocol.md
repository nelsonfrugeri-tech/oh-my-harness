# Protocolo de Decisão Orientado a Evidência

Use este protocolo quando uma decisão de software tem impacto relevante no usuário, risco
operacional, irreversibilidade ou custo não-trivial.

## 1. Enquadre a decisão

Escreva a decisão, o prazo, o sistema e a população afetados, e o custo do atraso. Liste as
restrições separadamente das preferências.

## 2. Monte o registro de evidência

Capture:

```yaml
verified_facts: []
derived_results: []
inferences: []
hypotheses: []
estimates: []
unknowns: []
alternatives: []
decision_criteria: []
```

Todo fato verificado, resultado derivado e inferência aponta para evidência inspecionável; sem essa
sustentação, rerrotule. Hipóteses e estimativas citam a evidência disponível e registram
explicitamente quando não existe nenhuma. Desconhecidos nomeiam a evidência que falta e seu impacto
na decisão. Preserve evidência contraditória em vez de tirar a média dela.

## 3. Escolha a observação decisiva mais barata

Ranqueie as investigações possíveis por valor para a decisão, custo e latência. Prefira uma
reprodução, um teste dirigido, uma medição pequena ou um experimento reversível que distinga
hipóteses concorrentes. Pare de coletar evidência quando outra observação dificilmente mudaria a
escolha o bastante para justificar seu custo.

## 4. Compare alternativas

Para cada alternativa viável, declare benefício esperado, modo de falha, reversibilidade, custo de
implementação e a evidência que a sustenta. Não fabrique scores. Uma matriz ponderada só é válida
quando seus pesos e notas têm evidência definida ou estão claramente rotulados como julgamento de
stakeholder.

Trate o conjunto de opções apresentado como uma alegação, não como uma fronteira. Cheque o status
quo, passos graduais ou reversíveis e combinações de opções antes de aceitar uma escolha binária.

## 5. Decida e pré-registre a validação

Registre:

- a alternativa selecionada e o dono;
- a evidência e os critérios que controlaram a escolha;
- as alternativas rejeitadas e os trade-offs materiais;
- métricas leading e de guardrail com requisitos de proveniência;
- um resultado que falsificaria as premissas escolhidas;
- condições de rollback ou revisão e o momento da próxima observação.

Quando a evidência é fraca e a falha é cara, reduza o blast radius, adicione instrumentação ou
escolha um passo reversível. Para um hotfix urgente, distinga a mitigação imediata da correção
durável e registre a evidência exigida antes de alegar causa raiz.
