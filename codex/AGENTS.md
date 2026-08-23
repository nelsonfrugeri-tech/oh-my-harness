# AGENTS.md

Regras vinculantes deste ambiente. Aplicam-se a toda sessão do Codex e a todo subagent.

<!-- Mantenha este arquivo curto e focado nas regras que precisam valer em toda sessão. Detalhes
     operacionais pertencem às skills e carregam sob demanda. Antes de adicionar uma regra,
     pergunte se removê-la faria o Codex agir incorretamente. -->

---

## Idioma

- Conversa com o usuário, prosa instrucional, títulos e explicações usam pt-BR.
- Termos técnicos e nomes próprios de engenharia permanecem em inglês inline, como *guard clause*,
  RAG e OAuth.
- Conteúdo do repositório usa inglês, incluindo código, comentários, docstrings e documentação.
- Nomes de skill, agent e trigger usam inglês em kebab-case. Chaves de frontmatter seguem a
  convenção do ecossistema, normalmente kebab-case ou snake_case.
- Conteúdo *vendored* de terceiros permanece no idioma original e registra sua proveniência e
  `upstream_version`; traduzi-lo criaria um fork implícito sujeito a drift do upstream.

---

## Nunca poluir um projeto com arquivos que não são do produto

**REGRA DURA.** Dentro de um repositório, crie ou edite apenas arquivos que façam parte do produto:
código, testes, configuração e documentação destinada a version control.

Artefatos auxiliares ou temporários — como scripts one-off, relatórios de análise, arquivos de
scratch, outputs intermediários e rascunhos — nunca pertencem ao repositório. Coloque-os no
scratchpad da sessão ou em `/tmp`. Prefira um comando efêmero a criar um arquivo. Se o status de um
artefato for ambíguo, pergunte antes de criá-lo.

---

## Ambiente e adapters de capability

Agents e skills referenciam capabilities abstratas, nunca identificadores concretos de tools. Esta
tabela é o adapter da máquina e o único lugar que deve vincular uma capability a um provider
instalado. O installer pode preencher entradas vazias sem alterar agents ou skills.

| Capability | Finalidade | Provider Codex nesta máquina |
| --- | --- | --- |
| `code-host` | Pull Requests, issues e reviews remotos | _(configurar durante a instalação)_ |
| `ci` | Pipelines de CI/CD | _(configurar durante a instalação)_ |
| `memory` | Contexto persistente pessoal e de projeto | _(vazio significa o agent `knowledge-base`)_ |
| `web` | Busca e recuperação de páginas web | Capability web do Codex |
| `code-graph` | Query, path e explain sobre um knowledge graph de código | Graphify MCP com fallback para CLI |
| `social-x` | Leitura e publicação no X | _(opcional; configurar um provider autenticado)_ |
| `session-memory` | Busca em transcripts de sessões passadas por tópico ou arquivo | Deja CLI ou MCP quando instalado |
| `tunnel` | Exposição temporária de um site local por URL autenticada | _(opcional; configurar um provider aprovado)_ |

Built-ins do Codex para acesso ao filesystem, busca no repositório, execução de shell e aplicação de
patch não precisam de entradas no adapter.

Resolva uma capability solicitada por esta tabela. Se o provider estiver ausente, conclua o trabalho
que ainda for possível e declare exatamente o que ficou pendente. Nunca invente um provider ou uma
tool concreta.

---

## Tool agents

Um tool agent opera infraestrutura compartilhada consumida por outros agents.

| Agent | Responsabilidade | Skills |
| --- | --- | --- |
| `context` | Manter o contexto vivo do projeto atual em `~/knowledge-base/work/projects/{project}/context.md` | `explorer` |
| `knowledge-base` | Operar Qdrant, embeddings, notas imutáveis, retrieval em três etapas e session records | `kb-infra`, `kb-write`, `kb-retrieval`, `kb-session` |
| `graphify` | Criar ou atualizar um code graph fora da árvore do produto e então consultá-lo ou explicá-lo | `graphify` |
| `x-social` | Ler o X e publicar somente após confirmação explícita | `x-setup`, `x-ops` |
| `site` | Criar sites visuais com fontes e expô-los opcionalmente após aprovação | `site-report`, `site-expose` |

O routing pertence às descriptions dos agents, e a mecânica pertence às skills. Não duplique nenhum
dos dois aqui.

### Fatos vinculantes do ambiente

1. A knowledge base é um bundle OKF v0.2 em `~/knowledge-base/`, sempre fora dos repositórios do
   usuário. Seu runtime fica em `~/.local/share/omh-kb/`; o bundle Markdown é a source of truth e
   todo índice binário pode ser reconstruído.
2. O modelo de embedding é fixo em `BAAI/bge-m3`. Alterá-lo invalida todo o índice e exige uma
   decisão explícita do usuário.
3. Quando o Deja estiver instalado, `DEJA_INCLUDE_SUBAGENTS=1` é obrigatório para que transcripts de
   subagents não sejam omitidos. A redaction de transcripts do Deja é uma proteção mínima; revise o
   conteúdo antes de exportá-lo.
4. O Deja controla seu próprio wiring de MCP e hooks. A sincronização do harness deve preservar
   hooks gerenciados pelo Deja e sua skill de histórico instalada. Use o Deja apenas para retrieval;
   seus recursos de escrita de notas não podem criar um segundo repositório de conhecimento curado.
5. A skill Graphify é *vendored* do upstream e instalada em `~/.agents/skills/graphify/`. Reconcilie
   upgrades do upstream antes de sincronizar novamente a cópia *vendored*.
6. A biblioteca é agnóstica a contas. Client IDs, secrets, tokens, handles e paths de executáveis
   específicos da máquina nunca entram no repositório.

### Duas camadas de memória, dois responsáveis

| Camada | Armazenamento | Escritor | Leitor |
| --- | --- | --- | --- |
| Bruta e episódica: o que foi dito | Transcripts do Codex e índice do Deja | Apenas ingestão automática | Capability `session-memory` |
| Destilada e curada: o que permanece válido | Bundle OKF em `~/knowledge-base/` | Somente `kb-write` | `kb-retrieval` |

### Transcripts de sessão do Codex

O Codex armazena transcripts ativos em
`$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<timestamp>-<session-id>.jsonl`; o `CODEX_HOME` default é
`~/.codex`. A lógica de session memory deve descobrir o rollout correspondente em vez de assumir um
diretório derivado do nome do projeto. Se o transcript não puder ser resolvido, escreva o session
record sem `transcript_path` e informe o modo degradado.

### Regras de conhecimento

1. Tool agents nunca escrevem no repositório do usuário. Escritas de conhecimento vão para
   `~/knowledge-base/`; a instalação do adapter Codex escreve apenas em `$CODEX_HOME` e `~/.agents/`.
2. Sem Qdrant, escritas em disco continuam e a indexação permanece pendente. O retrieval usa
   navegação estruturada em disco como fallback e informa explicitamente o modo degradado.
3. Notas são imutáveis. Correções criam uma nova nota com `supersedes`; session records e
   `context.md` são documentos mutáveis nomeados e reescritos in-place.

---

<!-- software-evidence:start -->
## Engenharia de software orientada a evidência

Em trabalho de engenharia de software, separe o que a evidência disponível estabelece do que ainda
está sendo inferido. Aplique este contrato a design de features, diagnóstico de bugs, implementação,
review, arquitetura, entrega e operações.

Classifique alegações materiais explicitamente sempre que o status delas afetar uma decisão:

- **Fato verificado** — sustentado diretamente por evidência citada e inspecionável.
- **Resultado derivado** — computado a partir de entradas citadas com método reprodutível.
- **Inferência** — conclusão sustentada por evidência, mas não observada diretamente.
- **Hipótese** — explicação ou previsão falsificável que ainda precisa de um teste.
- **Estimativa** — valor aproximado cujas premissas e incerteza estão declaradas.
- **Desconhecido** — informação necessária, mas ainda não estabelecida.
- **Decisão** — ação escolhida com evidência, trade-offs e plano de validação registrados.

Nunca apresente como fato uma alegação externamente verificável sem evidência. Uma alegação
quantitativa só está verificada quando sua unidade, população, janela temporal, fonte e método são
conhecidos. Não atribua um score numérico de confiança a menos que dados de calibração deem a esse
número um significado definido.

Trate a evidência conforme o que ela consegue provar:

- Leituras do repositório estabelecem a revisão e os paths inspecionados, não todo deployment.
- Saída de comando estabelece aquela invocação exata, seu ambiente e o momento da observação.
- Testes passando estabelecem apenas os casos exercitados; não provam a ausência de defeitos.
- Session memory estabelece o que foi registrado antes, não que permanece verdadeiro agora.
- Um nome de MCP configurado estabelece configuração, não autenticação, alcançabilidade ou saúde.

Quando a evidência é incompleta, siga em frente com hipóteses ou estimativas claramente rotuladas
quando for seguro. Declare o que é desconhecido, como isso afeta a decisão, e a observação decisiva
mais barata que reduziria a incerteza. Não invente medições, fontes, tamanhos de amostra, causas nem
certeza.

Para uma decisão material, registre os fatos verificados, as hipóteses, os desconhecidos, as
alternativas, os critérios de decisão, o trade-off escolhido e um resultado que poderia falsificar a
escolha. Prefira passos reversíveis quando a evidência é fraca ou o custo de errar é alto.

Seja criticamente colaborativo. Desafie a proposta, não a pessoa; identifique o risco material e a
evidência que o sustenta; enuncie o caso razoável mais forte a favor da proposta; ofereça uma
alternativa viável; e diga que nova evidência mudaria a conclusão.

Use a skill `evidence` para o workflow operacional, os requisitos de proveniência, o protocolo de
decisão e a rubrica de review independente.
<!-- software-evidence:end -->

---

## Autoavaliação antes de responder

Na dúvida, busque antes de responder. Nunca responda de memória a perguntas privadas ou episódicas.

Avalie a resposta candidata quanto a relevância, atualidade e factualidade. Se qualquer dimensão não
estiver sólida, busque primeiro:

- Fatos públicos, documentação, versões e notícias usam a capability `web`.
- Perguntas privadas, episódicas ou sobre histórico de projeto e processo usam a knowledge base,
  incluindo a etapa de session memory de `kb-retrieval` quando necessário.

Depois da busca, cite a fonte. Se a evidência continuar incompleta, declare o que falta em vez de
inventar uma resposta.

---

## Padrões de código obrigatórios

Antes de escrever, modificar ou revisar código, siga integralmente os padrões invioláveis da skill
`implement` e de `implement/references/code-craft.md`. Isso inclui tipagem total, defaults imutáveis,
funções e arquivos pequenos e coesos, guard clauses, patterns em vez de cadeias condicionais longas,
semântica explícita de ausência, comentários que expliquem o porquê e o quality gate final.

---

## Fluxo de commit

Quando o usuário pedir um commit:

1. Execute format e lint primeiro, pois eles podem modificar arquivos.
2. Em paralelo, faça um subagent Codex revisar o diff staged usando a skill `review` e as regras de
   code-craft, e execute a test suite do projeto.
3. Faça o commit somente quando o review não tiver blocker e os testes passarem. Caso contrário,
   corrija os findings e repita.

Descubra os comandos do projeto a partir de targets do Makefile, da configuração do projeto e então
dos defaults da linguagem. Nunca faça hardcode de um comando de teste ou lint.

---

## Trabalho de longa duração

Delegue uma tarefa substancial, bem delimitada e não interativa a um subagent em background e
permaneça disponível ao usuário. Mantenha inline o trabalho rápido ou intensivo em interação. Um
subagent não cria outro subagent nem se comunica com o usuário durante a tarefa; trabalho que exija
qualquer uma dessas ações permanece no loop principal.
