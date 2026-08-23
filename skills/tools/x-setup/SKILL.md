---
version: 1.0.0
name: x-setup
description: |
  Runbook de conexão da plataforma X (Twitter) ao harness, agnóstico a conta e a harness.
  Cobre: a escolha entre o MCP oficial hospedado (api.x.com/mcp) e o MCP de docs
  (docs.x.com/mcp, sem auth); a criação do app no X Developer Portal com OAuth 2.0 e
  redirect URI; a instalação do bridge `xurl` (brew, npm, script, go); os comandos de
  autenticação (`xurl auth apps add`, `xurl auth oauth2`, `--headless`, `app-only`);
  onde o token é cacheado (`~/.xurl/auth.yml`, mode 600 — sempre fora de qualquer repo);
  o plug por harness (Claude Code, Codex, Cursor e qualquer cliente MCP); o mapeamento da
  capability `social-x`; a realidade de custo da X API pay-as-you-go (2026); e o
  diagnóstico das falhas comuns de auth. Invocada pelo agent `x-social` quando a intenção
  é conectar, reconectar ou diagnosticar o acesso — não destinada a invocação direta solta.
type: capability
---

# X Setup — Conectando a Plataforma X ao Harness

Você conecta a conta do X do usuário ao harness dele. O princípio que governa esta skill:
**a biblioteca é agnóstica a conta.** Nenhum `CLIENT_ID`, `CLIENT_SECRET`, token ou handle
entra no repositório. A identidade vive na máquina do usuário, resolvida em runtime por OAuth.

Você não escreve um servidor MCP — o X já hospeda o dele. Seu trabalho é plugá-lo.

---

## 1. Escolha o servidor

O X publica **dois** servidores MCP hospedados:

| Servidor | Endpoint | Auth | Para quê |
|---|---|---|---|
| **X API MCP** | `https://api.x.com/mcp` | OAuth 2.0 ou bearer | Posts, busca full-archive, users, bookmarks, news/trends, Articles |
| **Docs MCP** | `https://docs.x.com/mcp` | **nenhuma** | Busca na documentação da X API (`search_x`, `get_page_x`) |

O **Docs MCP é grátis e sem auth** — plugue-o primeiro. Ele não toca a conta do usuário nem
gasta um centavo, e serve para explorar a API antes de qualquer decisão de custo.

O **X API MCP** é o que exige app, OAuth e dinheiro. As seções seguintes tratam dele.

### Rotas de auth

| Rota | Como | Ganha | Perde |
|---|---|---|---|
| **OAuth 2.0 PKCE** (padrão) | bridge local `xurl mcp` | contexto de usuário: age **como o usuário** — lê, posta, acessa bookmarks; refresh automático | exige um app no Developer Portal e um processo local |
| **App-only bearer** | token estático, sem bridge | simplicidade: puro remoto, sem processo local | **read-only**, sem contexto de usuário, sem refresh, sem bookmarks |

**Padrão desta biblioteca: OAuth 2.0 via bridge.** Ofereça o bearer apenas quando o usuário
disser que só quer leitura ou estiver num ambiente onde não pode rodar processo local.

---

## 2. Crie o app no X Developer Portal

Este passo é **do usuário** — exige o login e o cartão dele. Você não consegue fazê-lo e não
deve fingir que fez. Instrua e espere.

1. Acessar o X Developer Portal e criar um **Project + App**.
2. Em *User authentication settings*, habilitar **OAuth 2.0**.
3. App type: **Web App / Automated App or Bot** (é o tipo que emite `CLIENT_SECRET`).
4. Cadastrar o **Callback URI / Redirect URL**: `http://localhost:8080/callback`
5. Copiar o **Client ID** e o **Client Secret**.

> **Regra dura:** peça ao usuário para **não colar o secret no chat**. Ele deve ir direto para
> a variável de ambiente ou o config local do harness. Se ele colar mesmo assim, avise que o
> segredo foi exposto no transcript e recomende rotacionar no portal.

**Redirect URI é a causa nº 1 de falha.** O valor cadastrado no portal precisa ser
byte-a-byte igual ao que o bridge usa. A precedência do `xurl` é: variável `REDIRECT_URI` →
`redirect_uri` salvo no app → default `http://localhost:8080/callback`.

---

## 3. Instale o bridge `xurl`

`xurl` é a CLI oficial da X API (`xdevplatform`). Ele guarda a identidade do app, faz o fluxo
OAuth, cacheia e renova o token, e expõe o subcomando `mcp` que ponte stdio ↔ servidor
hospedado.

```bash
# escolha UM
brew install --cask xdevplatform/tap/xurl          # macOS
npm install -g @xdevplatform/xurl                  # qualquer plataforma com node
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash   # → ~/.local/bin
go install github.com/xdevplatform/xurl@latest     # via Go
```

Descubra o gerenciador que o usuário já usa antes de escolher — não imponha o Homebrew a quem
vive de npm. Instalar via npm global também dispensa instalação prévia: o config MCP pode
chamar `npx -y @xdevplatform/xurl` direto.

---

## 4. Autentique

```bash
# registra o app (guarda client id/secret em ~/.xurl/auth.yml, mode 600)
xurl auth apps add omh --client-id "$CLIENT_ID" --client-secret "$CLIENT_SECRET" \
  --redirect-uri http://localhost:8080/callback

# fluxo OAuth 2.0 PKCE — abre o browser, usuário aprova, token é cacheado
xurl auth oauth2 --app omh
```

Máquina sem browser (servidor, container, SSH):

```bash
xurl auth oauth2 --app omh --headless
```

O modo headless imprime a URL de autorização; o usuário aprova em qualquer browser e cola de
volta a URL de redirect (ou o `code`).

Rota app-only (read-only), quando escolhida:

```bash
xurl auth app-only "$BEARER_TOKEN"
# ou, sem passar o segredo por argv (não fica no histórico do shell):
cat token.txt | xurl auth app-only -
```

### Onde o segredo mora

| Arquivo | Conteúdo |
|---|---|
| `~/.xurl/auth.yml` | client id/secret, tokens OAuth e bearer, por app — **mode 600** |
| `~/.xurl/keys.yml` | chaves privadas de XChat |

Sempre no `$HOME`, **nunca** dentro de um repositório. Se você encontrar credencial do X dentro
de um working tree, trate como incidente: avise o usuário, recomende rotacionar no portal e
verifique se o arquivo foi commitado.

**Verificação de sanidade** — confirme que o token responde antes de plugar o MCP:

```bash
xurl -X GET "https://api.x.com/2/users/me"
```

Retornou o objeto do usuário → auth OK. Retornou 401/403 → volte ao passo 4.

---

## 5. Plugue no harness

O servidor é o mesmo em todos os harnesses — MCP é o protocolo comum. Só muda **onde** o
config vive.

### Claude Code

```bash
claude mcp add xapi --scope user \
  -e CLIENT_ID="$CLIENT_ID" -e CLIENT_SECRET="$CLIENT_SECRET" \
  -- npx -y @xdevplatform/xurl mcp https://api.x.com/mcp

# grátis, sem auth — vale sempre
claude mcp add --transport http x-docs --scope user https://docs.x.com/mcp

claude mcp list   # confirme o handshake
```

`--scope user` deixa o server disponível em todos os projetos da máquina. Use `--scope local`
se o usuário quiser restringir a um projeto.

> **Autentique antes de plugar.** Rode o passo 4 (`xurl auth oauth2 --app omh`) **antes** de
> escrever qualquer config. O primeiro start do bridge abre o browser e fica esperando o
> usuário aprovar; se o cliente tiver timeout curto, o server morre no handshake e o sintoma
> aparece como "MCP não conecta". Com o token já cacheado, o start é imediato em todo cliente.

### Codex — TOML, não JSON

O Codex configura MCP em `~/.codex/config.toml`, com tabelas `[mcp_servers.<nome>]`. **Não é
o formato `mcpServers` em JSON** dos demais clientes:

```toml
[mcp_servers.xapi]
command = "npx"
args = ["-y", "@xdevplatform/xurl", "mcp", "https://api.x.com/mcp"]
startup_timeout_sec = 300

[mcp_servers.xapi.env]
CLIENT_ID = "..."
CLIENT_SECRET = "..."
```

O `env` é uma **sub-tabela própria** (`[mcp_servers.xapi.env]`), não uma chave inline — e ela
precisa vir depois das chaves escalares da tabela pai, senão o TOML fica inválido.
`startup_timeout_sec` é chave do Codex; nos clientes JSON ela não existe.

### Cursor, Claude Desktop e demais clientes MCP

Forma canônica de servidor stdio em JSON, no config do cliente (`~/.cursor/mcp.json` no
Cursor):

```json
{
  "mcpServers": {
    "xapi": {
      "command": "npx",
      "args": ["-y", "@xdevplatform/xurl", "mcp", "https://api.x.com/mcp"],
      "env": { "CLIENT_ID": "...", "CLIENT_SECRET": "..." }
    },
    "x-docs": { "url": "https://docs.x.com/mcp" }
  }
}
```

Prefira `env` apontando para variáveis já exportadas no shell do usuário a colar o segredo
literal no arquivo de config — e confirme que esse arquivo não está versionado.

**Descubra o formato antes de escrever.** Um harness fora desta lista pode usar TOML, YAML ou
JSON. Leia um server já configurado no config do cliente e espelhe a forma dele — nunca
presuma JSON.

> **Atalho sem bridge (opcional, não verificado):** clientes que suportam OAuth 2.0 com client
> credentials pré-registradas podem tentar falar direto com `https://api.x.com/mcp` por HTTP,
> sem processo local — no Claude Code, `claude mcp add --transport http xapi https://api.x.com/mcp
> --client-id ... --client-secret ... --callback-port 8080`. O X não faz dynamic client
> registration, então isso depende do cliente aceitar credenciais estáticas. Se funcionar,
> ótimo — é mais limpo. Se falhar, volte ao bridge, que é o caminho suportado.

---

## 6. Mapeie a capability

Feito o plug, edite a tabela de capabilities do `CLAUDE.md` do usuário:

| Capability | Papel | Tool concreta nesta máquina |
| --- | --- | --- |
| `social-x` | Ler e publicar na plataforma X (Twitter) | `mcp__xapi__*` |

Use o prefixo real que o harness atribuiu ao server (o nome que você deu no `mcp add`) — não
presuma `xapi` se o usuário nomeou diferente. Confirme com `claude mcp list`.

Sem esse mapeamento o agent `x-social` não encontra a capability e cai em degradação.

---

## 7. O custo — diga antes, não depois

A X API mudou em **fevereiro de 2026**: o free tier acabou para novos developers e o padrão
passou a ser pay-as-you-go.

| Operação | Preço |
|---|---|
| Post lido | **$0.005** (teto de 2M reads/mês) |
| Post criado | **$0.015** |
| Post criado **com link** | **$0.20** |

Os tiers fixos legados (Basic $200/mês, Pro $5.000/mês) seguem apenas para assinantes
existentes — estão fechados para novos cadastros, e os remanescentes vêm sendo migrados para
pay-as-you-go desde junho de 2026.

**Consequência prática:** uma busca que devolve 100 posts custa ~$0.50. Um cron varrendo
menções de hora em hora vira uma conta de verdade no fim do mês. Deixe isso explícito para o
usuário **antes** de ele criar o app — é o passo em que ele ainda pode desistir.

Se o caso de uso for "ler minha timeline e postar de vez em quando", diga a verdade: automação
de browser sobre a sessão já logada resolve com custo zero. A API só compensa para automação
headless de verdade.

---

## 8. Diagnóstico

| Sintoma | Causa provável | Remédio |
|---|---|---|
| Browser não abre / trava no start | primeiro start esperando aprovação, ou timeout curto | suba `startup_timeout_sec`; ou autentique antes com `xurl auth oauth2 --app omh` |
| `redirect_uri_mismatch` | URI do portal ≠ URI do bridge | alinhe portal, `REDIRECT_URI` e `--redirect-uri`; a precedência é env → app → default |
| 401 depois de funcionar | token expirado e refresh falhou | `xurl auth oauth2 --app omh` de novo |
| 403 em escrita | app sem permissão de write, ou auth app-only | habilite Read+Write no portal e **reautentique** (escopo só muda com token novo) |
| Bookmarks vazio ou 403 | sem contexto de usuário | está em app-only; migre para OAuth |
| Tool do X não aparece | server não plugado, ou tool deferida | `claude mcp list`; se deferida, carregue via `ToolSearch` |
| 429 | rate limit da X API | recue com backoff; reduza `max_results` |
| Cobrança inesperada | leitura em volume | veja a guarda de custo em `x-ops` |

**Ao diagnosticar, reporte estado — nunca valor.** "Token expirado", "app não registrado",
"redirect divergente" são diagnósticos legítimos. Imprimir o token, o secret ou o conteúdo de
`~/.xurl/auth.yml` não é, em nenhuma hipótese.

---

## Desconectar

```bash
claude mcp remove xapi --scope user
```

Revogar de verdade o acesso exige o usuário: remover o app no X Developer Portal. Diga isso —
tirar o MCP do harness não revoga o token que ainda vive em `~/.xurl/auth.yml`. Para limpar o
cache local, apague a entrada do app nesse arquivo.
