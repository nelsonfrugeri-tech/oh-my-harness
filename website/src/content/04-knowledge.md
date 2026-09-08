---
order: 4
id: knowledge
label: Conhecimento
title: A sessão acaba. O conhecimento permanece.
lead: Histórico é o que foi dito. Conhecimento curado é o que continua válido.
diagram: knowledge
note: "Dê tempo a este capítulo. Diferencie transcript de nota curada e Markdown de índice. Use um projeto fictício; nunca abra a base pessoal durante uma gravação pública."
source: core/skills/kb-write/SKILL.md
---

## Duas camadas, responsabilidades distintas

Transcripts preservam a memória episódica. O bundle externo **OKF v0.2** preserva notas Markdown curadas com proveniência de harness, sessão, diretório de trabalho e máquina. O agent `knowledge-base` opera essa camada; a escrita curada passa por `kb-write`.

O Markdown é a fonte de verdade. O Qdrant é um índice derivado, reconstruível, com embeddings `BAAI/bge-m3`. Sem o serviço, a navegação estruturada em disco continua disponível em modo degradado declarado.

### Encontrar por identidade antes de semelhança

Projetos, aliases e referências exatas são resolvidos antes do fallback semântico. Um único resultado pode responder; homônimos exigem desambiguação. Depois vêm retrieval híbrido, navegação em disco e busca direcionada no histórico de sessões.

### Preservar não significa acumular sem critério

Notas são imutáveis: uma correção cria outra nota com `supersedes`. Registros de sessão são mutáveis. A identidade atual de projeto usa uma nota `knowledge_type: project`; existe migração preservadora do `context.md` legado.

### Fronteiras importantes

Retrieval e destilação não acontecem magicamente em background: o apontador de `SessionStart` não equivale a memória carregada. Proveniência obrigatória ausente bloqueia a escrita. URLs de remote com credenciais ou assinaturas não devem ser persistidas nem devolvidas. Esta arquitetura não promete concorrência multiusuário.
