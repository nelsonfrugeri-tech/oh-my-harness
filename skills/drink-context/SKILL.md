---
version: 1.1.0
name: drink-context
description: |
  Carrega o contexto do projeto atual na sessão: notas recentes da memória persistente
  (capability memory, se plugada — janela dos últimos ~5 dias, filtrado por projeto) +
  o context.md do projeto em disco. Também atualiza o context.md sob solicitação de
  mudança grande. Degrada com elegância se a capability memory não estiver disponível.
  Triggers: /drink-context, carregar contexto, contexto do projeto, recall contexto.
type: command
---

# drink-context — Carregador de Contexto do Projeto

Ao ser invocado, este skill instrui o harness a abrir o agent `context`
(subagent_type: `context`) e seguir integralmente as instruções dele.

O agent `context` resolve o projeto atual, consulta as fontes disponíveis (memória
persistente via capability `memory`, se plugada, e o `context.md` em disco) e entrega
um bloco de contexto estruturado para a sessão. Nenhuma ação adicional é necessária aqui.
