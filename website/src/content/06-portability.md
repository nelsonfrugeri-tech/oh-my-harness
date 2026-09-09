---
order: 6
id: portability
label: Portabilidade
title: Troque a execução. Não reinicie a engenharia.
lead: O core permanece harness-invariant; adapters traduzem formatos, permissões e integrações nativas.
diagram: boundaries
note: "Mostre as três fronteiras: core versionado, representação instalada no harness e capabilities da máquina. Portabilidade não significa respostas idênticas nem suporte automático a qualquer ferramenta."
source: README.md
---

## Evolua o método uma vez

O core compartilhado reúne agents, skills, policies, workflows, hooks e evals. Ele descreve como investigar, decidir, implementar, verificar, revisar e comunicar — sem codificar o nome de um provider em cada contrato.

Claude Code e Codex recebem representações nativas desse core. Cada adapter respeita o formato de configuração, as permissões, o isolamento e o lifecycle do ambiente. O objetivo não é produzir arquivos idênticos; é preservar a mesma intenção com fidelidade.

### Capabilities desacoplam comportamento de ferramenta

Agents pedem capacidades abstratas, como `web`, `code-host`, `code-graph` ou `session-memory`. A máquina conecta cada capability a um provider disponível. Assim, trocar uma integração não exige reescrever todas as skills que dependem dela.

### O conhecimento também atravessa o harness

Identidade, memória episódica recuperável e conhecimento curado vivem fora dos repositórios de produto e fora do código dos harnesses. Os adapters acessam a mesma base conceitual sem criar uma memória concorrente para cada ferramenta.

### Portabilidade é um contrato de extensão

O suporte entregue nesta versão é para **Claude Code e Codex**. Outro harness precisa representar agents e skills, mapear capabilities, preservar fronteiras de autorização e passar por validação própria. “Plugar” significa implementar esse adapter — não assumir compatibilidade sem evidência.

No Codex, instalar apenas o plugin também não equivale a sincronizar o adapter completo com custom agents. O caminho de instalação depende do comportamento que se deseja disponibilizar.
