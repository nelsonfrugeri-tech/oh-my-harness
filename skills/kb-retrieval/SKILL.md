---
version: 2.2.0
name: kb-retrieval
description: |
  Recuperação de conhecimento da knowledge base (bundle OKF v0.2 em ~/knowledge-base/)
  como uma escada de 3 degraus: (1) busca semântica híbrida no Qdrant sobre notas E
  session records (query → embedding BAAI/bge-m3 dense+sparse → dois prefetch fundidos
  com Reciprocal Rank Fusion, filtros por kind/type/knowledge_type/domain/data e
  provenance de harness/sessão/máquina via payload); (2) navegação estruturada do
  bundle em disco — descida pelos index.md dos
  bounded contexts e pastas de tipo de entidade — como fallback sem Qdrant; (3) deep
  search na session memory bruta do harness via kb-session, quando os degraus
  anteriores não respondem. Cobre também travessia de relacionamentos por links
  markdown, resolução de cadeias supersedes (sempre preferir a nota mais recente da
  cadeia), leitura dos sinais de confiança (generated/verified) e frescor (stale_after),
  e montagem de resposta com citação das fontes. Cobre ainda a **entrada lateral por
  arquivo**: quando a pergunta é ancorada num path ("quando mexemos nisso?", "por que
  esta linha ficou assim?"), não sobe a escada — vai direto ao blame por arquivo da
  capability `session-memory`, complementar ao git log (o git diz o que mudou; a session
  memory diz o que estava sendo discutido quando mudou). Invocada pelo agent
  `knowledge-base` quando a intenção é buscar/recuperar conhecimento — também usada por
  kb-write para descobrir relacionamentos.
type: capability
---

# KB Retrieval — Recuperação de Conhecimento

Você responde perguntas a partir da knowledge base em `~/knowledge-base/`, subindo uma
**escada de 3 degraus** — do mais barato ao mais profundo:

| Degrau | Via | Quando descer para o próximo |
|---|---|---|
| **1** | Busca semântica híbrida no Qdrant — notas **e** session records | Qdrant fora do ar → degrau 2. Resposta ausente ou parcial com Qdrant saudável → degrau 3. |
| **2** | Navegação estruturada em disco — `notes/` **e** `sessions/` | Resposta ausente ou parcial → degrau 3 (usando os session records achados em disco). |
| **3** | Deep search na session memory bruta do harness, via `kb-session` | Último degrau — se nada, diga que não foi encontrado. |

Duas obrigações transversais: **anuncie na resposta qual degrau a respondeu** (a
diferença entre "busca semântica", "grep estrutural" e "trecho do transcript de uma
sessão" importa para o leitor) e **nunca escale silenciosamente** — a descida de degrau
é sempre declarada, nunca disfarçada de resultado do degrau anterior.

### Entrada lateral: quando a pergunta é sobre um *arquivo*

A escada acima busca por **tema**. Quando a pergunta é ancorada num **path** — "quando
mexemos neste arquivo?", "por que esta linha ficou assim?", "que sessão introduziu isso?"
— não suba a escada: vá direto ao `blame` por arquivo da capability `session-memory`
(via `kb-session` §4.1), que lista as sessões que tocaram aquele path, da mais recente
para a mais antiga.

Isso é **complementar ao `git log`**, não redundante: o git diz *o que* mudou e a mensagem
de commit; a session memory diz **o que estava sendo discutido** quando mudou — a
intenção que nenhum commit registra. Numa investigação de "por que isso está assim", use
os dois.

**Sem a capability**, degrade: `git log --follow` no path para a cronologia, mais o deep
search degradado (`kb-session` §4.2) usando o basename do arquivo como termo de busca.
Declare a limitação — sem o índice, só enxergam-se as sessões que têm session record.

---

## 1. Degrau 1 — Busca semântica híbrida (via principal)

Desenho validado na era oh-my-kb — espelhe-o:

1. **Embede a query** com bge-m3 (padrão de `kb-infra`): um forward pass produz o vetor
   dense (1024) e o sparse (`indices`/`values`).
2. **Dois prefetch, um por espaço vetorial**, cada um com limite `top_k * 4` (o fusion
   precisa de um candidate set profundo por lista; 4x equilibra recall e custo):
   - dense → named vector `"dense"`
   - sparse → named vector `"sparse"`
3. **Fusão com RRF** (`FusionQuery(fusion=Fusion.RRF)`) e `limit=top_k`.
4. **Filtros server-side no nível do prefetch** (não depois da fusão): `domain` (match
   no payload — o bounded context), `type` (o substantivo do domínio),
   `knowledge_type` (o enum epistêmico), janela de `created_at` (range DATETIME), e
   `must_not archived=true` por padrão. Quando a pergunta pedir origem, filtre também
   por `harness`, `session_id`, `session_name`, `machine_id` ou `machine_label`.

   Os dois eixos de tipo servem a perguntas diferentes: filtre por `type` quando a
   pergunta é sobre uma **classe de coisa** ("quais serviços temos?"), e por
   `knowledge_type` quando é sobre a **natureza do conhecimento** ("que decisões
   tomamos?"). Filtrar pelos dois ao mesmo tempo quase sempre estreita demais.

   Provenance responde perguntas auditáveis: `session_id` é a identidade canônica da
   sessão, `session_name` é o nome legível quando existe, `machine_id` é a identidade
   estável e `machine_label` é o nome operacional (`m4`, `m1`, `ifood`). Use campos
   exatos, nunca inferência por path. Pontos legacy podem ter esses campos `null`; um
   filtro de provenance os exclui deliberadamente e isso deve ser informado.

A collection indexa **dois kinds** de ponto (payload `kind`, ver `kb-infra`): notas
(`kind: "note"`, embedding do summary) e session records (`kind: "session"`, embedding
de `name + description + resume` — mantidos por `kb-session`). Por padrão busque
**sem filtro de `kind`** — sessões passadas são fonte legítima de resposta; filtre por
`kind` só quando a pergunta é claramente de um lado ("qual o procedimento de X?" →
`note`; "em que sessão falamos de Y?" → `session`). O `must_not archived=true` não
exclui sessões: session records não carregam `archived`.

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition, Filter, Fusion, FusionQuery, MatchValue, Prefetch,
    SparseVector,
)

client = QdrantClient(url="http://localhost:6333")
flt = Filter(
    must=[FieldCondition(key="domain", match=MatchValue(value=domain))],
    must_not=[FieldCondition(key="archived", match=MatchValue(value=True))],
)
prefetch = [
    Prefetch(query=dense, using="dense", filter=flt, limit=top_k * 4),
    Prefetch(query=SparseVector(indices=idx, values=vals), using="sparse", filter=flt, limit=top_k * 4),
]
points = client.query_points(
    collection_name="knowledge-base",
    prefetch=prefetch,
    query=FusionQuery(fusion=Fusion.RRF),
    limit=top_k,
    with_payload=True,
).points
```

**Interpretação do score**: o score é RRF, **não** similaridade de cosseno. O Qdrant usa
`k = 2` e rank começando em zero — ou seja, `score = Σ 1/(2 + rank_i)` sobre as listas em
que o ponto apareceu. *(Medido empiricamente contra o Qdrant v1.18 em 2026-08-01: seis
previsões bateram com o score real na quarta casa. Não confie no `k = 60` da literatura
de RRF — não é o que esta implementação faz.)*

Consequência: o **teto é 1.0** (primeiro lugar nas duas listas), e ancorar a leitura em
posições é mais útil que decorar faixas:

| Score | O que significa |
|---|---|
| `1.0` | 1º nas duas listas |
| `>= 0.5` | 1º em pelo menos uma lista (ou 3º nas duas) — hit forte |
| `0.2 – 0.5` | presente nas duas, fora do topo — relevante |
| `< 0.2` | cauda profunda, ou só numa lista e mal posicionado — provável ruído |

Duas armadilhas: o score é **puramente posicional** — um ponto com similaridade medíocre
fica em 1º se for o menos ruim do corpus, e o RRF dá 0.5 a ele sem hesitar; e o piso das
faixas **desce quando o `limit` do prefetch sobe** (com `limit = L`, a cauda vale
`2/(2+L)`). Em corpus pequeno (≤ 50 notas) tudo pontua alto e o filtro não discrimina —
julgue pela relação semântica real, sempre.

Collection inexistente **não é erro** — significa "nenhuma nota indexada ainda":
devolva resultado vazio e sugira o fallback em disco ou o reindex de `kb-infra`.

## 2. Degrau 2 — Navegação estruturada em disco (fallback sem Qdrant)

O disco é a fonte da verdade e não depende de infra nenhuma. O bundle OKF é desenhado
para ser navegado **sem busca**, descendo por `index.md`. Layout:

```
~/knowledge-base/                   # raiz do bundle (index.md declara okf_version)
  index.md
  person/                           # bounded context
    index.md
    people/  finances/  ideas/      # pastas de tipo de entidade
      index.md
      <YYYY-MM-DD>--<slug>.md       # uma nota por arquivo, frontmatter + corpo
  work/
    ifood/                          # bounded context
      index.md  log.md
      systems/  teams/  rituals/
    projects/
      <repo>/                       # bounded context
        index.md  context.md  log.md
        decisions/  procedures/  components/
        sessions/
          <session_id>.json         # session record vivo (mantido por kb-session)
```

O runtime (volume do Qdrant e venv de embedding) **não fica aqui** — mora em
`~/.local/share/omh-kb/`, fora do bundle. Ver `kb-infra`.

**Navegação progressiva (o caminho preferido).** Comece pelo `index.md` da raiz, escolha
o bounded context que a pergunta habita, leia o `index.md` dele, desça para a pasta do
tipo de entidade. Três leituras baratas costumam levar direto à nota certa — sem grep,
sem embedding. Este é o degrau 2 feito bem.

Quando a navegação não basta, caia no grep:

- **Por data**: os nomes de arquivo começam com a data — `ls` ordenado já é uma
  timeline. Recentes: `ls -1 ~/knowledge-base/<domain>/*/*.md | sort -r | head`.
- **Por tipo de entidade**: é a própria pasta — `ls ~/knowledge-base/work/ifood/systems/`.
- **Por natureza do conhecimento**: grep no frontmatter —
  `grep -rl "^knowledge_type: decision" ~/knowledge-base/<domain>/`.
- **Por assunto**: grep por termos no `title`/`description`/`summary`/`entities` do
  frontmatter; leia só os frontmatters (head) antes de abrir corpos.
- **Por provenance**: grep nos campos `harness`, `session_id`, `session_name`,
  `machine_id` ou `machine_label` das notas e session records. Notas legacy sem
  `provenance` não entram em filtros de origem; declare essa limitação.
- **Cross-context**: o mesmo padrão com glob `~/knowledge-base/**/*.md`.

E os session records: grep por termos nos campos `name`/`description`/`resume` dos
JSONs — `grep -rl -i "<termo>" ~/knowledge-base/**/sessions/*.json` — e ordene por
`updated_at` para privilegiar sessões recentes.

`index.md` e `log.md` são **arquivos reservados**, não conceitos: use-os para navegar e
para ler a cronologia de um contexto, mas nunca os apresente como nota-fonte.

Ao usar o fallback, **diga explicitamente** que a busca foi estrutural (navegação/grep),
não semântica — e ofereça subir a infra via `kb-infra` se o volume de notas justificar.

## 3. Degrau 3 — Deep search na session memory (via `kb-session`)

Os degraus 1–2 buscam sobre o que foi **destilado** (summaries de notas, resumes de
sessões). Mas nem tudo que foi dito numa sessão virou nota ou entrou no resume — a
resposta pode existir apenas na **memória bruta** do harness. O degrau 3 vai atrás dela.

**Quando descer** (qualquer um destes):

- Os degraus 1–2 não encontraram **nada** relevante e a pergunta tem cheiro de memória
  episódica ("o que falamos sobre X?", "por que decidimos Y naquela conversa?", "qual
  era o erro que apareceu quando tentamos Z?").
- Os degraus 1–2 responderam **parcialmente** — ex.: uma nota cita a decisão mas não o
  raciocínio, ou um session record indica que o tema foi discutido numa sessão sem que
  exista nota sobre ele.
- O usuário pede explicitamente para buscar em sessões passadas.

**Como descer**:

1. Delegue ao **playbook de deep search de `kb-session`** (seção 4), passando a query. Ele
   busca pela capability `session-memory`, que varre os transcripts de **todos os
   harnesses e todos os projetos** da máquina.
2. Incorpore os trechos recuperados à resposta **com a citação de sessão** exigida por
   `kb-session` (session name + session_id + harness), sinalizando quando o trecho vier
   de outro projeto/cwd.

> **Session record não é pré-requisito.** Numa versão anterior este degrau exigia
> selecionar antes os session records candidatos, porque a busca só sabia mergulhar num
> transcript já apontado por um record. Com a capability isso caiu: a busca alcança
> sessões que **nunca tiveram record**. Os hits `kind: "session"` do degrau 1 seguem
> úteis como **pista de ranking** ("o tema apareceu nesta sessão"), mas não são mais o
> portão de entrada. No modo degradado (sem capability) o pré-requisito volta a valer —
> ver `kb-session` §4.2.

**Nunca desça silenciosamente**: anuncie que os degraus estruturados não bastaram e que
o deep search foi acionado — e, se nem ele encontrar, diga que a knowledge base e as
sessões registradas não contêm a resposta.

## 4. Travessia de relacionamentos

Os relacionamentos entre notas são **links markdown no corpo** — não há campo
estruturado a seguir. Depois de abrir uma nota relevante, varra o corpo por links de
caminho absoluto ao bundle (`](/...)`) e siga os que enriquecem a resposta: o
procedimento citado por uma decisão, o evento que a motivou, o sistema que ela opera.

Duas restrições: **um salto de profundidade**, nunca uma travessia do grafo inteiro; e
**leia a prosa em volta do link antes de segui-lo** — é ela que diz qual é a relação (o
OKF não tipa relacionamentos). Link cuja frase não explica a relação provavelmente não
vale o salto.

## 5. Confiança e frescor

Toda nota carrega sinais que mudam **como** você deve apresentá-la. Leia-os antes de
responder:

| Sinal | Leitura |
|---|---|
| `verified` com `by: human:...` | O usuário confirmou. Apresente como conhecimento firme. |
| só `generated` (sem `verified`) | Escrito por agent, nunca confirmado. Apresente **dizendo isso** — "registrado automaticamente, ainda não confirmado por você". |
| `stale_after` no passado | Conteúdo vencido. Responda, mas **avise que expirou** e ofereça revalidar. |
| `status: draft` | Rascunho. Nunca apresente como decisão vigente. |
| `status: deprecated` | Superado — trate como a cadeia `supersedes` abaixo. |

Nunca silencie um sinal fraco para deixar a resposta mais limpa: a marca de confiança é
o único antídoto contra a KB se encher de conhecimento que nenhum humano validou.

## 6. Resolução de cadeias `supersedes`

Antes de montar a resposta, resolva as cadeias:

1. Para cada nota candidata, verifique se **outra nota a superseda** (alguma nota com
   `supersedes: <id-da-candidata>`). No Qdrant, notas supersedidas já têm
   `archived: true` e são excluídas por padrão; em disco, elas carregam
   `status: deprecated` — e o grep por `supersedes: <id>` nos frontmatters acha quem as
   substituiu.
2. Siga a cadeia até a ponta: **sempre prefira a nota mais recente da cadeia** — ela é
   o conhecimento vigente.
3. As versões antigas são história: cite-as apenas se o usuário pedir a evolução da
   decisão ("por que mudamos?"), deixando claro o que está arquivado.

## 7. Montagem da resposta

- Responda a pergunta em prosa direta, sintetizando o conteúdo das notas — não despeje
  arquivos inteiros.
- **Cite as notas-fonte** ao final, cada uma com título, os dois eixos de tipo, data e
  path absoluto:

```
Fontes:
- [decision · decision] Adoção de OIDC com PKCE (2026-05-12) — ~/knowledge-base/work/projects/api-gateway/decisions/2026-05-12--oidc-pkce.md
- [system · reference] Gateway de autenticação (2026-04-02, não confirmado) — ~/knowledge-base/work/ifood/systems/2026-04-02--auth-gateway.md
- [session] "Refactor da biblioteca portable" (55cb8ac6…, claude-code) — deep search no transcript
```

  O formato é `[<type> · <knowledge_type>]`; anote entre parênteses quando a nota não
  tiver `verified` ou estiver vencida.

- **Anuncie o degrau usado** — "via busca semântica", "via navegação no bundle (sem
  Qdrant)", "via deep search na sessão X" — sempre, em toda resposta.
- Se nada relevante foi encontrado, diga claramente — não invente conhecimento que não
  está registrado.

## Regras de execução

1. **Read-only** — recuperação nunca escreve nada, nem em `~/knowledge-base/`.
2. **Filtros no servidor** — domain/type/knowledge_type/data/archived e provenance via
   payload filter no prefetch, nunca filtragem client-side após a fusão.
3. **No degrau 2, navegue antes de grepar** — a descida pelos `index.md` é mais barata e
   mais precisa que varredura por padrão.
4. **Cadeias supersedes sempre resolvidas** — nunca apresente conhecimento arquivado
   como vigente (vale para notas; session records são vivos e não têm cadeia).
5. **Sinais de confiança nunca são silenciados** — nota sem `verified` é apresentada
   como não confirmada; nota com `stale_after` vencido, como expirada.
6. **Toda resposta cita as fontes** — título, os dois eixos de tipo, data e path para
   notas; session name + session_id + harness para trechos de sessão.
7. **Escada explícita, nunca silenciosa** — anuncie o degrau que respondeu; a descida
   ao degrau 2 (bundle em disco) ou 3 (deep search via `kb-session`) é sempre declarada.
8. **Scripts efêmeros via heredoc** com o venv de `kb-infra` — nunca crie arquivos de
   script no projeto do usuário.
9. **Pergunta ancorada num arquivo não sobe a escada** — vai direto ao blame por arquivo
   da capability `session-memory`, e se combina com `git log` quando o "porquê" importa.
