---
order: 5
id: engineering
label: Engenharia
title: Delegue execução. Preserve responsabilidade.
lead: Critérios de aceite, implementação, testes e revisão são trabalhos diferentes.
diagram: engineering
note: "Mostre os critérios antes do código e os testes antes da revisão. Explique Standards e Spec e a diferença entre self-check e avaliação independente."
source: core/skills/feature/SKILL.md
---

## Um fluxo orientado pelo repositório

A skill `feature` coordena escopo, execução delimitada, verificação e handoffs. O trabalho parte dos comandos, padrões e restrições reais do projeto. O humano continua responsável por decisões, autorização e aceite.

A revisão independente examina dois eixos: **Standards**, para padrões de engenharia e riscos observáveis; **Spec**, para aderência ao que foi pedido. Um self-check do autor não substitui essa revisão.

### Gates com cobertura explícita

O PR quality gate atua na criação de PR pelos caminhos documentados e exige confiança explícita no repositório. Não é uma proteção universal para qualquer API, navegador ou push posterior. A configuração de um gate, por si só, não prova que uma execução foi verificada.

### Especialistas sem duplicar o upstream

O OMH pode encaminhar tarefas a skills externas instaladas. Contratos próprios definem o método; conhecimento específico de frameworks pode permanecer com seus mantenedores. Instalação, providers e compatibilidade precisam ser verificados no ambiente.
