---
order: 3
id: evidence
label: Governança
title: Não confie na fluência. Governe o que é conhecido.
lead: Evidência, hipótese, inferência e desconhecido ocupam lugares diferentes antes de qualquer decisão.
diagram: evidence
note: "Apresente o nome completo: governança epistemológica. Evidence é a skill que operacionaliza essa disciplina. Não prometa eliminar alucinações; mostre como o sistema governa evidência, inferência, hipótese e desconhecido."
source: core/skills/evidence/SKILL.md
---

## Alucinação não se resolve com “não alucine”

Modelos de linguagem geram continuações prováveis; eles não possuem acesso intrínseco à verdade. Em determinadas classes de fatos, existe inclusive um limite estatístico para evitar alucinações — e esse resultado não depende especificamente da arquitetura Transformer. Treinamentos e benchmarks também podem recompensar o modelo por adivinhar em vez de reconhecer incerteza.

O contrato `evidence` operacionaliza uma forma de **governança epistemológica**: antes de agir, o sistema precisa distinguir o que sabe, como sabe, o que está apenas inferindo e o que ainda precisa ser testado.

### Sete estados para não esconder incerteza

- **Fato verificado:** sustentado por fonte citada e inspecionável.
- **Resultado derivado:** calculado de entradas conhecidas por método reproduzível.
- **Inferência:** conclusão sustentada, mas não observada diretamente.
- **Hipótese:** explicação falsificável que ainda precisa de teste.
- **Estimativa:** aproximação com premissas e incerteza declaradas.
- **Desconhecido:** informação material que ainda não foi estabelecida.
- **Decisão:** escolha feita com trade-offs e critério de revisão explícitos.

### A fonte precisa ser capaz de provar a afirmação

Uma leitura de arquivo prova o conteúdo daquela revisão — não o sistema inteiro. Um comando prova aquela execução — não todas as configurações. Um teste passando prova os casos exercitados — não a ausência de defeitos. Documentação prova o contrato documentado — não o comportamento em runtime.

Por isso, fatos do projeto pedem inspeção do repositório; decisões passadas pedem memória; comportamento executável pede testes; informação externa e volátil pede fontes atuais e primárias.

### Verificação reduz risco, não cria infalibilidade

Pesquisa, atribuição, revisão e verificação podem reduzir conteúdo sem suporte, mas as próprias fontes podem estar erradas e o modelo pode interpretá-las mal. O ganho do OMH é tornar a cadeia de confiança visível — inclusive quando a resposta correta é **desconhecido**.

Leitura complementar: [por que modelos alucinam](https://openai.com/index/why-language-models-hallucinate/), [limites estatísticos da alucinação](https://arxiv.org/abs/2311.14648), [RARR](https://aclanthology.org/2023.acl-long.910/) e [Chain-of-Verification](https://aclanthology.org/2024.findings-acl.212/).
