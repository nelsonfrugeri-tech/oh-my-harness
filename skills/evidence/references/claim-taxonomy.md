# Taxonomia de Alegações e Proveniência

Use o status mais estreito que a evidência disponível sustenta. Um rótulo só é útil quando o leitor
consegue inspecionar o registro que o sustenta e reproduzir o raciocínio.

## Testes de status

| Status | Sustentação exigida | Falha comum |
| --- | --- | --- |
| Fato verificado | Observação direta, fonte, escopo e momento da observação | Generalizar além do escopo observado |
| Resultado derivado | Entradas citadas, fórmula ou procedimento, e saída reprodutível | Esconder premissas na aritmética |
| Inferência | Fatos citados mais o raciocínio que os conecta | Chamar correlação de causa |
| Hipótese | Previsão falsificável e um teste que discrimina | Escrever uma explicação infalsificável |
| Estimativa | Premissas, faixa ou modelo de erro, e uso pretendido | Reportar um valor pontual como se medido |
| Desconhecido | A informação que falta e seu impacto na decisão | Preencher a lacuna em silêncio |
| Decisão | Alternativas, critérios, evidência, dono e plano de validação | Apresentar uma preferência como fato |

## Proveniência quantitativa

Para todo número material, registre:

- nome da métrica e unidade;
- população ou denominador;
- janela temporal e momento da observação;
- revisão da fonte, query, comando, dashboard ou documento primário;
- método de coleta e de cálculo;
- exclusões, premissas e limitações conhecidas.

Não transforme rótulos ordinais como baixo, médio e alto em probabilidades numéricas. Use confiança
numérica apenas quando um procedimento de calibração mapeia esse valor a resultados observados.

## Semântica da evidência

- Uma leitura de arquivo sustenta alegações sobre o conteúdo e a revisão inspecionados.
- Uma contagem de busca sustenta a query exata, os paths incluídos e as exclusões.
- Um benchmark sustenta seu hardware, dataset, configuração, warm-up e repetições.
- Telemetria sustenta sua população instrumentada e sua janela, sujeita a sampling e qualidade de
  dados.
- Documentação sustenta o contrato documentado na versão citada, não a saúde em runtime.
- Um transcript sustenta o que foi dito. Revalide qualquer alegação que possa ter ficado obsoleta.

Prefira fontes primárias para comportamento e especificações. Use fontes secundárias para descobrir
evidência primária ou comparar interpretações, não para apagar um conflito entre fontes primárias.

Uma premissa fornecida por usuário ou stakeholder é evidência direta de que a premissa foi
reportada, não de que a alegação de software subjacente é verdadeira. Até ser corroborada,
classifique a afirmação subjacente como hipótese, estimativa ou desconhecido conforme sua forma, e
preserve o relator e o momento como proveniência. Não exija revalidação quando a premissa está
explicitamente declarada como suposição de um exercício hipotético.

Uma previsão quantitativa pode conter uma estimativa e uma hipótese ao mesmo tempo. Use
**Hipótese** como status primário quando a afirmação prevê uma relação ou um resultado a ser
testado; registre o valor numérico e suas premissas como a estimativa dentro dessa hipótese. Use
**Estimativa** sozinha para uma quantidade aproximada de planejamento que não afirma relação causal
ou preditiva.
