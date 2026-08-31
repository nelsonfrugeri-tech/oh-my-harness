---
version: 1.1.0
name: didactic-visual
description: |
  Use ao explicar um conceito técnico, decisão, trade-off, arquitetura, modo de falha ou abordagem
  de implementação em conversa quando um visual compacto facilitar a compreensão da relação.
  Requer a skill evidence e funciona tanto na instalação plugin-only quanto com o adapter global.
  Torne explainability central: conecte conclusões a evidência, mecanismo, limitações e ação.
  Prefira conclusão primeiro, progressive disclosure, linguagem simples e tables, diagramas ASCII
  ou terminal charts úteis. Não use em código-fonte, comentários, docstrings ou documentação do
  repositório, onde prevalecem as convenções do projeto. Triggers comuns: explique isto, compare
  estas opções, mostre o flow, torne visual, qual é o trade-off, esta abordagem faz sentido,
  /didactic-visual.
type: capability
---

# Didactic Visual

Explique material técnico para que uma pessoa experiente compreenda a decisão na primeira leitura.
Responda no idioma do usuário e preserve termos técnicos estabelecidos em inglês quando mais claros.

> A formatação só merece espaço quando reduz o esforço cognitivo.

## Prerequisite: evidence first

1. Carregue `oh-my-harness:evidence` antes de redigir. Se a skill estiver indisponível, pare e
   informe exatamente o prerequisite ausente.
2. Quando houver um evidence contract ativo no harness, aplique-o como additional constraints;
   sua ausência não é um blocker porque esta skill é autocontida na instalação plugin-only.
3. Deixe o workflow de evidence estabelecer alegações, provenance, incerteza, alternativas e
   decisões.
4. Aplique esta skill somente como camada de apresentação depois que a base factual estiver sólida.

```text
evidence skill + additional constraints opcionais → conteúdo rigoroso → apresentação didática
```

Nunca reclassifique, esconda ou simplifique incerteza para deixar um visual mais limpo.

## Construa a resposta

1. Comece pela conclusão ou resposta direta.
2. Dê somente o contexto necessário para compreender essa conclusão.
3. Separe fatos observados, resultados derivados, inferências, hipóteses, estimativas, desconhecidos
   e decisões sempre que misturá-los puder mudar a ação do leitor.
4. Escolha prosa, lista, table ou diagrama ASCII conforme o tipo de relação.
5. Adicione a próxima camada apenas quando ela ajudar materialmente ou o usuário pedir detalhes.

## Construa uma narrativa explicativa

Para uma explicação substancial, use esta estrutura e omita somente etapas inaplicáveis:

```text
problema → componentes → método → evidência → resultados → limitações → próximos passos
```

- Abra respostas longas com um executive summary compacto; omita-o quando a resposta já for curta.
- Use nomes oficiais de serviços e sistemas na primeira menção e depois defina abreviações.
- Explique conceitos de dados em linguagem acessível sem perder precisão técnica.
- Diferencie fatos verificados de conclusões derivadas no ponto em que cada um aparece.
- Adicione flows, comparison tables e exemplos somente quando melhorarem a compreensão.

## Torne a explicação auditável

Trate explainability como a capacidade de inspecionar por que uma conclusão decorre da evidência,
não como exposição de chain-of-thought privado. Para cada conclusão material, exponha a justificativa
concisa e verificável:

```text
alegação → evidência → mecanismo → limitações → ação
```

- Explique o mecanismo que conecta causa e efeito, em vez de citar apenas o resultado.
- Identifique a evidência ou fator de decisão que sustenta cada conclusão importante.
- Declare limitações, contraexemplos e condições que mudariam a resposta.
- Nomeie alternativas relevantes e por que a recomendação difere delas.
- Nunca use "best practice" no lugar de uma justificativa inspecionável.

## Prefira visuals terminal-native

Antes de criar um visual, aplique uma guard clause: se a resposta for um fato único, um mapeamento
de uma etapa ou couber claramente em uma frase, responda sem visual. Um pedido explícito não elimina
esse critério nem cria obrigação de desenhar; explique a omissão somente se o usuário pediu o visual.
Para uma explicação substancial que passe essa guard clause, inclua pelo menos um visual útil.

| Relação | Prefira | Use quando |
| --- | --- | --- |
| Sequência ou mudança de estado | ASCII flow ou timeline | Três ou mais etapas dependentes |
| Mapeamentos exatos ou campos repetidos | Table | Linhas compartilham os mesmos eixos |
| Hierarquia ou ownership | Tree | Nesting é mais difícil em prosa |
| Magnitude ou ranking | Horizontal bars | Valores pedem comparação proporcional |
| Tendência temporal | Sparkline ou time-series bars | Medidas ordenadas mostram movimento |
| Distribuição | Histogram | Buckets revelam concentração ou dispersão |

Para todo terminal-native chart quantitativo, declare escala, unidade, população ou denominador,
janela temporal, fonte e método. Preserve comprimentos proporcionais, marque valores ausentes e
nunca fabrique dados ou falsa precisão. Mantenha labels curtas e interprete o visual em uma frase.

## Mantenha a resposta escaneável

- Limite parágrafos a aproximadamente três frases.
- Use headings apenas para seções reais e bold como âncora visual esparsa, não como decoração.
- Use inline code para identificadores, comandos, campos e valores técnicos.
- Deixe uma linha em branco ao redor de listas, headings, tables e code blocks em CommonMark.
- Use emoji somente como status signal quando acrescentar significado.
- Não repita a conclusão como resumo final.

## Exemplo compacto

```text
installer --check
      │
      ├── arquivos estáticos ─── verificados
      └── trust em runtime ───── não inspecionado
                                      │
                                      ▼
                             alegação de saúde limitada
```

Declare o resultado verificado e seu limite junto ao visual; não deixe a formatação insinuar mais.
