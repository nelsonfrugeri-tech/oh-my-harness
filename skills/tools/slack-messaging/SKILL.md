---
name: slack-messaging
description: >
  Prepara rascunhos de Slack na voz natural do usuário em pt-BR. Adapta cada mensagem ao contexto
  da conversa e diferencia atualizações rápidas, pedidos, propostas, rollouts e lançamentos de
  feature. Gatilhos: rascunhos, replies, anúncios e calibração de voz no Slack.
type: capability
---

# Slack Messaging

Use esta skill sempre que for compor uma mensagem de Slack para o usuário. O objetivo não é uma voz
corporativa genérica: é uma mensagem clara, natural e adequada à conversa, que deixe explícita a
responsabilidade pelo trabalho.

## Segurança e entrega

Resolva a capability abstrata `team-messaging` pela orientação ativa do harness. Prepare um
rascunho; nunca envie diretamente, agende ou publique. Se somente conteúdo privado do Slack puder
estabelecer o contexto necessário, peça consentimento explícito antes de lê-lo. Não copie histórico,
nomes ou identificadores do Slack para repositório, skill ou nota durável.

Antes de redigir, leia a thread raiz ou as mensagens próximas quando estiverem disponíveis. Acompanhe
a formalidade, o nível de detalhe e o ritmo da conversa; o rascunho deve parecer a próxima mensagem
natural, não um template colado.

## Regras de voz não negociáveis

1. Escreva as ações do usuário na **primeira pessoa do singular**: “eu testei”, “eu alterei”, “eu
   encontrei”, “estou verificando”, “vou promover” e “vou monitorar”.
2. Use terceira pessoa para um grupo real: “o time”, “os times” ou o grupo nomeado. Não use “nós”,
   “concluímos” nem voz passiva impessoal para esconder quem executou o trabalho.
3. Comece parágrafos comuns e itens de lista que sejam frases completas com letra minúscula. Nomes
   próprios, nomes de produto e marcadores convencionais como `TL;DR` são exceções.
4. Escreva em pt-BR informal-profissional. Contrações naturais são bem-vindas quando a thread as
   usa; mantenha ortografia, acentuação e pontuação suficientes para leitura rápida.
5. Mantenha mensagens compactas. Não acrescente saudação, título, recapitulação ou entusiasmo se a
   conversa e o tipo de mensagem não pedirem. Nunca use emojis.
6. Diga somente fatos sustentados pela conversa ou pelo que o usuário informou. Não invente
   validação, impacto, métrica, prazo, alinhamento do time ou próximo passo.
7. Resolva uma @-mention por `team-messaging` antes de usá-la. Mencione a pessoa somente quando a
   mensagem for direcionada a ela e ela não já estiver na thread ou DM.

## Escolha a forma de escrita

| Situação | Estrutura | Orientação de voz |
| --- | --- | --- |
| Status rápido | Uma ou duas linhas: estado atual, ação do usuário, próximo passo ou bloqueio. | Sem título ou histórico. Use progresso direto. |
| Reconhecimento ou reply | Uma resposta curta, seguida da próxima ação concreta quando necessário. | Um reconhecimento breve e genuíno basta; não invente elogio. |
| Pedido | Contexto apenas se necessário, depois um pedido claro e o resultado esperado. | Direto e colaborativo, sem tom de comando ou urgência artificial. |
| Proposta | Leitura ou ideia pessoal, justificativa curta e pergunta aberta ou pedido de decisão. | Assuma a proposta: “eu acho”, “eu tentaria”, “minha leitura é”. |
| Rollout ou deploy | Etapa, o que o usuário fez, resultado da validação e próximo monitoramento. | Atualize a mesma thread; use métricas só quando ajudarem a decisão. |
| Lançamento ou evolução de feature | Título curto no estilo `[evolução]`; o que está disponível; impacto prático; ganhos validados; acompanhamento. | Comece pela mudança concluída, separe o trabalho do usuário da contribuição do time e evite linguagem de marketing. |
| Incidente ou bloqueio | Impacto atual, o que o usuário verificou ou alterou, bloqueio e ajuda ou próxima atualização exata. | Seja factual e curto. Não escreva postmortem durante o incidente. |
| Handoff detalhado | `TL;DR`, bullets factuais, limitação conhecida e próximo responsável ou ação. | Use apenas quando a audiência precisar de evidência operacional. |

## Formas rápidas e naturais

Use estas formas como estrutura, nunca como roteiro. Substitua somente fatos conhecidos e preserve
a responsabilidade na primeira pessoa.

| Situação | Forma natural |
| --- | --- |
| Progresso rápido | `testei a canary e funcionou. fiz merge e vou promover.` |
| Estado de espera | `aguardando a pipeline pra promover a próxima etapa.` |
| Reconhecimento | `boa! vou validar aqui e te aviso.` |
| Pedido direto | `opa, conseguiu revisar o MR? se estiver ok, eu sigo com a canary.` |
| Proposta | `eu pensaria em deixar isso transparente por <motivo>. o que acha de avaliarmos <opção> como próxima evolução?` |
| Evolução de feature | Comece com ``[evolução] <feature> em produção`` e siga com `pessoal, concluí <mudança>. na prática, <impacto>. eu validei <evidência> e vou seguir monitorando <sinal>.` |
| Handoff de rollout | Comece com `TL;DR: deploy concluído e integração validada ponta a ponta.`, depois liste etapas, testes executados, limitação honesta e plano de monitoramento. |

## Elegância visual, tabelas e formatação de Slack

Escolha a forma que deixa a decisão mais fácil de ler. Uma mensagem elegante tem hierarquia leve,
espaço em branco entre blocos e somente a estrutura necessária; ela não parece um documento colado
no Slack.

- Use texto fluido para um fato, pedido ou próximo passo. Use bullets para uma lista curta sem
  relação tabular. Use tabela somente para comparar a mesma dimensão entre três ou mais itens.
- Use o **nome canônico** de cada projeto, produto, repositório, time, modelo e serviço. Copie a
  grafia, capitalização e hífens da fonte confiável na conversa, no link, no código ou no ticket.
  Não deduza siglas, não normalize nomes técnicos e não altere um identificador em `code`. Se a
  fonte estiver ausente ou ambígua, pergunte ou evite repetir o nome.
- Para uma tabela, escreva uma frase curta de contexto antes dela, coloque somente a tabela em um
  bloco `text` e feche com a conclusão ou ação que ela sustenta. Não envolva a mensagem inteira em
  um code block.
- Preserve o alinhamento em Slack com colunas compactas, cabeçalhos curtos, uma unidade por coluna e
  valores abreviados de forma consistente (`k`, `M`, `%`). Ordene as linhas pela importância da
  decisão ou por uma métrica explicitamente declarada.
- Mire em até seis colunas e 80 caracteres por linha. Se a tabela ultrapassar essa largura, tiver
  texto explicativo em células ou exigir quebra de linha, divida-a em duas tabelas ou use bullets.
- Use este formato, ajustando os dados sem quebrar as bordas ou alterar o nome canônico dos itens:

  ```text
  | Modelo           | Req | Erros | Tokens |
  |------------------|----:|------:|-------:|
  | gemini-3.5-flash | 38k | 4,3k  | 784M   |
  | gpt-5.5          | 8,8k| 0     | 81M    |
  ```

- Use Markdown padrão: `**negrito**` somente para uma decisão, prazo ou `TL;DR`; `code` para
  identificadores, comandos e termos literais; blockquote apenas para responder a uma afirmação
  específica. Não use sintaxe manual de mrkdwn, fontes decorativas, emojis ou headings em mensagens
  rotineiras.
- Em mensagens longas, abra com `**TL;DR:**`, mantenha uma linha em branco entre contexto, tabela
  ou lista e conclusão, e coloque cada link junto da afirmação que ele comprova.

## Adaptação ao contexto

- Em uma DM entre pares, acompanhe o registro informal já estabelecido e prefira texto fluido a um
  post estruturado. Um `boa` ou `opa` curto pode caber; não introduza termos muito informais em um
  channel público ou formal.
- Em uma thread operacional, publique atualizações incrementais conforme o estado muda; não repita
  contexto que já está visível. Uma mensagem final de validação pode ser mais estruturada ao fechar
  o rollout.
- Em um lançamento público, explique a mudança prática antes de listar benefícios. Use bullets só
  quando tornarem ganhos ou evidências mais fáceis de escanear.
- Em uma proposta, separe fato de interpretação. Peça opinião quando a decisão pertencer a outra
  pessoa; não faça uma ideia pessoal parecer decisão acordada.
- Use um link imediatamente após a afirmação que ele sustenta. Não adicione links apenas para dar
  aparência formal a um status curto.
- Em mensagem longa, abra com `TL;DR`, depois mantenha apenas os detalhes necessários para decisão
  ou validação.

## Revisão final

- Toda ação feita pelo usuário está na primeira pessoa do singular?
- Toda referência coletiva descreve trabalho real de um time ou grupo na terceira pessoa?
- A forma escolhida corresponde ao contexto: status, pedido, proposta, rollout, lançamento,
  bloqueio ou handoff?
- A mensagem está tão curta quanto a thread permite, preservando a evidência ou pedido necessário?
- A tabela, se houver, cabe em 80 caracteres por linha, preserva as bordas e ajuda mais do que
  bullets ajudariam?
- Os nomes de projetos, produtos, repositórios, times, modelos e serviços estão na forma canônica?
- Os parágrafos começam em minúscula, a linguagem está natural e não há emojis?
- É um rascunho, nunca uma mensagem enviada diretamente ou agendada?
