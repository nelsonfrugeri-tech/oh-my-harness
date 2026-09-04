# Note body template

Este arquivo define a **estrutura do corpo** de toda nota da knowledge base. Ele
**não** define o `summary` — que é prosa escrita à parte, pelas regras do `SKILL.md`.

O corpo é markdown puro. Seções marcadas **(required)** devem estar presentes; seções
**(optional)** podem ser omitidas quando não se aplicam.

---

## Seções comuns (toda nota tem)

### Contexto (obrigatória)

Um parágrafo curto: *por que esta nota existe?* Que situação, pergunta ou gatilho levou
a registrar isso? Mantenha enxuto — poucas frases. Se o contexto é longo, provavelmente
é uma nota separada — e então vira um link para ela.

### Referências (obrigatória quando a fonte contém endereços materiais)

Contextualize repository URLs, websites, documentos, issues e artifact paths que
sustentam a nota. Cada target desta seção também deve aparecer no campo estruturado
`references` do frontmatter com `kind`, `label`, `target`, entidade relacionada e
status de verificação. Isso permite responder deterministicamente perguntas como
"qual o link do repo X?" sem depender apenas do embedding.

Preserve nomes canônicos e targets exatos; paths locais são absolutos. Nunca inclua
credentials, tokens, signed URLs ou query params secretos. Se não houver endereço
material na fonte, omita a seção em vez de inventar uma referência.

> **Links internos entre notas não moram aqui.** Eles moram na frase que explica a
> relação, dentro da seção onde a relação aparece — porque o OKF não tipa
> relacionamentos: quem diz que a relação é "substitui", "foi causada por" ou "opera"
> é a prosa em volta do link. Use caminho absoluto ao bundle:
> `[rotação de chave KMS](/work/projects/api-gateway/procedures/kms-rotation.md)`.
> Uma lista de "ver também" no rodapé não carrega informação nenhuma.

---

## Seções por tipo

Use o bloco que corresponde ao `type`. Não misture.

### `decision`

#### Decisão (required)

A decisão em uma ou duas frases, no presente. "Adotamos X." Se um parágrafo não basta
para enunciar a decisão, você provavelmente está registrando várias decisões — separe.

#### Alternativas consideradas (required)

Lista curta das alternativas pesadas. Para cada uma, uma linha sobre o que era e por
que não foi escolhida. O ponto é tornar o *trade-off* visível ao próximo leitor.

#### Consequências (required)

O que esta decisão implica agora: o que faremos, o que não faremos, o que precisará ser
revisitado, quem é dono do follow-up. Dois a cinco bullets.

### `event`

#### O que aconteceu (required)

Narrativa factual e datada. Quando, onde, o quê, quem estava envolvido. Passado. Sem
interpretação nesta seção — mantenha neutro.

#### Impacto (required)

O que quebrou, o que atrasou, o que se perdeu, o que se aprendeu. Se o evento foi
positivo (um launch, um marco), o que mudou por causa dele.

#### Causa raiz (optional)

Se a causa raiz é conhecida. Não especule — na dúvida, omita e linke a nota de
investigação.

#### Próximos passos (optional)

Follow-ups concretos (com dono, se aplicável).

### `procedure`

#### Quando usar (required)

A precondição para executar este procedimento. "Use quando o release do api-gateway
tem menos de 30 minutos e a latência p99 passa de 500ms." Sem esta seção, leitores
futuros executarão o procedimento na situação errada.

#### Passos (required)

Numerados, executáveis, copy-pasteable. Cada passo é um verbo no imperativo. Inclua
comandos, paths de arquivo, outputs esperados.

#### Validação (required)

Como confirmar que o procedimento funcionou. A métrica, o dashboard, o comando cujo
output prova o sucesso.

#### Reversão (optional, quando aplicável)

Como desfazer, ou link para o procedimento inverso.

### `reference`

#### Conteúdo (required)

O fato, a definição, a restrição. Seja preciso — referências são citadas por outras
notas. Se a referência pode driftar (versão, valor de configuração), inclua a data em
que foi observada.

#### Aplicabilidade (optional)

Onde esta referência se aplica e onde não. Referências sem escopo tendem a ser mal
aplicadas.

### `conversation`

#### Resumo do diálogo (required)

Sobre o que foi a conversa e quem participou. Passado.

#### Decisões / próximos passos (required)

O que a conversa produziu. **Se há decisões concretas, escreva notas `decision`
separadas para cada uma, linkando de volta para esta conversa.** A nota de conversa é o
*rastro*; as notas de decisão são o *resultado*.

---

## Regras duras

1. **Não coloque o summary no corpo.** O summary é campo próprio do frontmatter e passa
   pelo embedding; o corpo é para o leitor que já decidiu que a nota é relevante.
2. **Não cole transcripts crus**, a menos que o transcript em si seja o conhecimento
   (ex.: entrevista de postmortem). Fora isso, resuma.
3. **Formatação mínima.** Headers markdown pelas seções acima, code blocks para
   comandos, parágrafos normais no resto. Sem HTML, sem badges, sem emoji decorativo.
4. **Date tudo que pode driftar.** Versões, custos, latências, valores de política —
   inclua a data em que foram escritos, para o leitor futuro saber se ainda valem.
