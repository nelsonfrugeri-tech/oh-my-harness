---
order: 2
id: architecture
label: Arquitetura
title: Uma fonte de intenção. Adapters nativos.
lead: Centralize o que define seu trabalho. Adapte o que depende do ambiente.
diagram: architecture
note: "Percorra o diagrama de cima para baixo. Abra core/agents/routing.json e compare um papel nas representações de Claude Code e Codex. Não descreva o protótipo TypeScript como runtime instalado."
source: core/agents/routing.json
---

## Separe responsabilidade de implementação

O catálogo em `core/agents/routing.json` define responsabilidades e rotas. As skills em `core/skills/` descrevem capacidades. Policies, hooks e evals complementam o sistema compartilhado.

Os diretórios de cada harness preservam seus formatos e mecanismos nativos. O adapter da máquina conecta capabilities abstratas, como `code-host` e `session-memory`, aos providers disponíveis.

### Agents, skills e tools não são sinônimos

- **Agent:** assume uma responsabilidade e escolhe capacidades para cumprir a tarefa.
- **Skill:** define como executar um trabalho delimitado, seus limites e critérios de conclusão.
- **Tool:** permite uma ação concreta; seu provider depende do ambiente.
- **Hook:** atua em um evento específico do ciclo de execução.

### Portabilidade com fidelidade

Um contrato compartilhado não elimina diferenças de isolamento, permissões ou integração. O workflow entregue é orientado pela skill `feature`; o protótipo TypeScript não é um motor instalado de execução.
