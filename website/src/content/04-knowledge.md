---
order: 4
id: knowledge
label: Conhecimento
title: Memória não é contexto infinito.
lead: O OMH separa o que foi dito do que deve continuar válido — com curadoria, provenance e recuperação em camadas.
diagram: knowledge
note: "Este é o deep dive central. Percorra escrita e retrieval separadamente. Reforce: transcript é memória episódica; nota curada é conhecimento; Qdrant é índice, não fonte de verdade."
source: core/skills/kb-write/SKILL.md
---

## Duas memórias, duas responsabilidades

**Memória episódica** preserva o que aconteceu: prompts, respostas, comandos e decisões registradas nos transcripts. Ela ajuda a recuperar contexto, mas contém tentativas, contradições e conclusões que podem ter expirado.

**Conhecimento curado** preserva o que continua válido. Ele vive fora dos repositórios de produto em um bundle **OKF v0.2**, composto por notas Markdown com identidade, tipo, conteúdo, provenance e relações de lifecycle.

### Como um conhecimento é gravado

1. **Recuperar antes de escrever:** procurar notas existentes, decisões anteriores e possíveis conflitos.
2. **Destilar:** transformar a sessão em uma unidade de conhecimento reutilizável — não copiar o transcript.
3. **Registrar provenance:** identificar harness, sessão, diretório de trabalho e máquina que originaram a nota.
4. **Persistir de forma imutável:** correções criam uma nova nota com `supersedes`; o histórico não é silenciosamente reescrito.
5. **Indexar:** gerar representações densas e esparsas com `BAAI/bge-m3` para retrieval híbrido.

Se provenance obrigatória estiver ausente, a escrita é bloqueada. A memória de longo prazo não deve aceitar conhecimento cuja origem não possa ser reconstruída.

### Como o conhecimento é recuperado

A busca começa por **identidade exata**: projeto, alias, referência ou entidade conhecida. Quando isso não basta, o Qdrant combina retrieval denso e esparso; os resultados são fundidos para equilibrar semântica e termos exatos. A navegação estruturada em disco funciona como fallback declarado. Quando necessário, uma busca direcionada consulta a memória episódica das sessões.

O Markdown é a fonte de verdade. O Qdrant é um índice derivado e reconstruível. Sem o serviço vetorial, o conhecimento continua existindo e pode ser navegado em modo degradado.

### Uma base fora do harness

A knowledge base pertence ao operador, não ao Claude Code, ao Codex ou ao repositório de um produto. Os adapters suportados acessam o mesmo bundle por meio do agent `knowledge-base` e das skills de escrita, retrieval, sessão e infraestrutura.

Novos harnesses não ganham compatibilidade por mágica: precisam de um adapter que preserve o contrato, conecte as capabilities necessárias e seja validado naquele ambiente. A arquitetura torna essa extensão possível sem duplicar a fonte de verdade.
