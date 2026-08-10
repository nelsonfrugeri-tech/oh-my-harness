---
version: 1.0.0
name: sync-bundle
description: |
  Monta um *case bundle* — o pacote portátil de conhecimento que atravessa de uma máquina
  para outra. Cobre: a anatomia do bundle (raiz do case + `MANIFEST.md` + `sessions/`,
  `chat/`, `kb/`, `artifacts/`), o pipeline de coleta em 4 passos (escopo → inventário de
  fontes → coleta por fonte → manifest), como converter cada tipo de fonte para um formato
  que outro agent lê sozinho (transcript de harness, thread/DM de chat, nota e context da
  knowledge base, artefato de projeto), o schema do `MANIFEST.md`, as regras duras de
  cópia-nunca-move, redação de segredos e declaração de lacunas. Invocada pelo agent `sync`
  quando a intenção é reunir conhecimento para outra máquina — não destinada a invocação
  direta pelo usuário. O transporte e a verificação de propagação ficam na skill
  `sync-transport`.
type: capability
---

# Sync Bundle — O Pacote Portátil de Conhecimento

Você monta o artefato que um agent **em outra máquina** vai abrir sem contexto nenhum. Esse é
o critério de qualidade: se o leitor do outro lado precisar perguntar "de onde veio isso?",
"quando foi coletado?" ou "isso está completo?", o bundle falhou.

Um bundle é sempre sobre **um assunto** — um case. Não existe bundle "geral": um case tem
fronteira, e essa fronteira é o que decide o que entra.

## Anatomia

```text
<sync-root>/<area>/case/<case-name>/
├── MANIFEST.md          # LEIA PRIMEIRO — o que é, quando, de onde, o que falta
├── sessions/            # transcripts de sessão do harness (bruto + índice legível)
├── chat/
│   └── <canal-ou-conversa>/   # threads e DMs exportadas em markdown cronológico
├── kb/
│   ├── notes/           # cópias de notas da knowledge base
│   ├── context/         # cópias de context.md de projeto
│   └── session-records/ # cópias de session records relevantes
└── artifacts/           # anexos: diagramas, planilhas, exports de dashboard, logs
```

Regras da árvore:

- **`MANIFEST.md` é obrigatório.** Um case sem manifest é um diretório órfão.
- **Pasta nasce quando tem conteúdo.** Não crie `chat/` vazio "por simetria" — a árvore
  descreve o que existe.
- **`<area>` agrupa cases relacionados** (por tema, produto ou domínio). É opcional: com um
  case só, `<sync-root>/case/<case-name>/` basta.
- **`<case-name>` em kebab-case**, estável e específico o bastante para não colidir.

## Pipeline

### 1. Escopo

Antes de coletar, fixe três coisas com o usuário (ou infira e **declare** o que assumiu):

| O quê | Por quê |
|---|---|
| **Nome do case** | Vira o diretório; precisa ser estável |
| **Fronteira** | O que é "sobre esse assunto" e o que não é — decide o corte |
| **Destino** | Qual sync root, qual `<area>` |

### 2. Inventário de fontes

Levante **onde** o conhecimento desse case vive antes de copiar qualquer coisa. As fontes
típicas, na ordem em que costumam render mais:

| Fonte | Onde buscar | Vira |
|---|---|---|
| Sessões do harness | memória de sessão do harness corrente (ver `kb-session`) | `sessions/` |
| Knowledge base | busca semântica + navegação em disco (ver `kb-retrieval`) | `kb/` |
| Conversas | canais e DMs das ferramentas de chat plugadas | `chat/` |
| Repositório / artefatos | o projeto relacionado, dashboards, exports | `artifacts/` |

Registre o inventário antes de copiar: ele vira a seção *Fontes* do manifest, e a diferença
entre o que você queria e o que conseguiu vira a seção *Lacunas*.

### 3. Coleta por fonte

Cada tipo de fonte tem uma conversão própria. A regra comum: **preserve autor, timestamp e
ordem cronológica**; sem esses três, o texto perde o valor de evidência.

**Transcript de sessão do harness**
Copie o arquivo bruto (JSONL ou equivalente) **e** escreva um `INDEX.md` ao lado com: id da
sessão, nome, período, máquina/harness de origem e um resumo do arco da conversa. O bruto é
grande e o leitor do outro lado não deve precisar parseá-lo para saber se vale a pena abrir.

**Thread ou DM de chat**
Exporte em markdown cronológico: uma entrada por mensagem com autor, handle, timestamp e o
texto; preserve as reações e os links quando houver. Cabeçalho com canal/conversa, período,
total de mensagens e participantes. Se a ferramenta permitir baixar o conteúdo bruto **e** ele
for legível como texto, leve o bruto junto. Anexos binários viram menção no texto, não são
copiados às cegas.

**Nota / context da knowledge base**
Copie o markdown como está — frontmatter incluído. O frontmatter é a procedência (id, tipo,
data, proveniência); removê-lo transforma conhecimento rastreável em texto solto. Relações
entre notas são links markdown que podem apontar para fora do bundle: no manifest, diga quais
links ficaram quebrados por estarem fora do escopo do case.

**Artefato de projeto**
Copie apenas o que é evidência do case. Arquivo grande, gerado ou reconstruível (build output,
dependências, binário) não entra — entra a referência de onde obtê-lo.

### 4. Manifest

Escreva o `MANIFEST.md` **por último**, quando você já sabe o que de fato entrou.

```markdown
# Case: <nome-do-case>

**O que é:** <2-3 frases: o assunto, e por que este case existe>
**Coletado em:** <ISO 8601 UTC>
**Origem:** <harness / tipo de máquina — sem identificar pessoa ou host, se desnecessário>

## Como ler

<Por onde o agent do outro lado deve começar e em que ordem. 3-5 linhas.>

## Conteúdo

| Caminho | Fonte | Itens | Período coberto |
|---|---|---|---|
| `sessions/` | sessão do harness | 2 transcripts | 2026-07-17 → 2026-07-31 |
| `chat/<conversa>/` | thread de chat | 45 mensagens | ... |
| `kb/notes/` | knowledge base | 6 notas | ... |

## Fatos-chave

<Bullets do que o case estabelece. É o resumo executivo que evita releitura integral.>

## Lacunas

<O que ficou de fora e por quê: fonte inacessível, capability ausente, redação de segredo,
arquivo grande demais. Explícito, nunca omitido.>
```

## Regras duras

1. **Cópia, nunca movimento.** A fonte da verdade permanece onde vive. `cp`, jamais `mv`.
2. **Nenhum segredo atravessa.** Inspecione antes de copiar; redija valores sensíveis para
   `<redacted>` e registre a redação no manifest. Na dúvida, não copie e declare a omissão.
3. **Nada de dado pessoal desnecessário.** Um bundle é sobre um assunto, não sobre pessoas.
   Identifique participantes pelo que a evidência exige e nada além disso.
4. **Formato legível por agent.** Markdown ou texto puro. Screenshot e binário opaco não
   transportam conhecimento — no máximo acompanham um texto que os descreve.
5. **Snapshot datado.** Recolher a mesma fonte de novo cria uma cópia nova identificada por
   data; o manifest é reescrito, o conteúdo anterior fica.
6. **Escrita confinada ao sync root.** Nunca escreva no repositório do usuário nem dentro da
   knowledge base — nesses destinos você é read-only.

## Encerramento

Depois de escrever o bundle, **o trabalho não acabou**: invoque a skill `sync-transport` para
forçar a detecção e verificar a propagação. Só então relate ao usuário — com o caminho do
case, a contagem por fonte, o percentual de propagação e as lacunas.
