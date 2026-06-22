# Runbook: servir a KB para o Claude Mobile (MCP remoto via HTTP + OAuth 2.1)

> Status: **pronto para validar** · Atualizado em: 2026-06-22
>
> Objetivo: expor o MCP da KB (`omh serve`) na internet com OAuth 2.1 para
> adicioná-lo como **custom connector** no claude.ai — depois ele aparece no
> **Claude Mobile**. O lado do servidor (Resource Server: PRM + 401 +
> validação de JWT) já está implementado e testado; os passos abaixo são a
> parte de **conta/infra** que roda na sua máquina/contas.

## Por que precisa de tudo isso

Confirmado por pesquisa: o connector do Claude **não aceita** MCP remoto sem
auth (issue oficial `claude-ai-mcp#402`, "not planned"), e a nuvem da Anthropic
**não alcança localhost** — então precisamos de **HTTPS público + OAuth 2.1**.
Nós somos o **Resource Server**; o **Authorization Server** é externo
(recomendado: **WorkOS AuthKit**, free).

## Pré-requisitos

- Qdrant rodando: `omh start` (as tool calls precisam dele; o boot do serve não).
- Uma conta no provedor de Authorization Server (recomendado **WorkOS AuthKit** — free).
- Um túnel HTTPS: **ngrok** (no plano pago dá domínio fixo, sem interstitial) ou
  **cloudflared** (`trycloudflare` é grátis, porém URL efêmera).

## Passos

### 1. Suba o túnel (HTTPS público → localhost:8765)

```bash
# ngrok (domínio reservado no plano pago é o ideal para "sempre ligado"):
ngrok http 8765
# → anote a URL pública, ex.: https://SEU-SUBDOMINIO.ngrok.app

# alternativa grátis (URL muda a cada execução):
# cloudflared tunnel --url http://localhost:8765
```

A **URL pública do MCP** será `<URL-do-túnel>/mcp`.

### 2. Configure o Authorization Server (WorkOS AuthKit)

No painel do WorkOS (ver `workos.com/docs/authkit/mcp`), habilite AuthKit como
AS OAuth 2.1 para MCP. Anote:
- **issuer URL** (ex.: `https://<seu>.authkit.app`)
- **JWKS URL** (opcional — o serve descobre via OpenID config se você omitir)
- **audience / resource** = a URL pública do MCP do passo 1 (`<túnel>/mcp`)
- garanta que o **DCR** (Dynamic Client Registration) está habilitado e que o
  callback `https://claude.ai/api/mcp/auth_callback` é aceito.

### 3. Suba o servidor em modo OAuth

```bash
omh serve \
  --host 127.0.0.1 --port 8765 \
  --auth-issuer https://<seu>.authkit.app \
  --public-url https://SEU-SUBDOMINIO.ngrok.app/mcp
  # opcional: --jwks-url https://.../jwks   (pula a descoberta)
  # opcional: --auth-scope <scope>          (exige scope no token)
```

Verifique o discovery (deve responder o PRM e 401 sem token):

```bash
curl https://SEU-SUBDOMINIO.ngrok.app/.well-known/oauth-protected-resource/mcp
curl -i -X POST https://SEU-SUBDOMINIO.ngrok.app/mcp/ -H 'Accept: text/event-stream' \
  -d '{}'   # → 401 + WWW-Authenticate apontando o resource_metadata
```

### 4. Adicione o connector no claude.ai (web/desktop)

Settings → Connectors → **Add custom connector** → cole `<túnel>/mcp`. O Claude
faz OAuth discovery → DCR → login no AuthKit → conecta. **No mobile você não
adiciona** — depois de conectar no web/desktop, ele **aparece no Claude Mobile**.

### 5. Teste no Claude Mobile

Abra o app, selecione o connector, e use a KB (`kb_search`, etc.).

## Caveats

- **`public-url` deve casar com o `audience`** que o AuthKit emite nos tokens
  (RFC 8707) — senão a validação do JWT falha (401).
- **ngrok free:** interstitial + sessão de 2h + URL que muda. Para "sempre
  ligado", use domínio reservado (ngrok pago) ou named tunnel da Cloudflare
  (exige domínio seu).
- **Segurança:** o endpoint fica público; a auth protege as tool calls, mas
  mantenha a URL/segredos privados. `kb_write` exposto = cuidado.
- Os passos exatos do WorkOS podem mudar — siga a doc oficial do provedor.

## O que já está pronto no código (lado servidor)

- `omh serve --auth-issuer ... --public-url ... [--jwks-url] [--auth-scope]`
- Resource Server: Protected Resource Metadata (RFC 9728), `WWW-Authenticate`
  em 401, validação de JWT RS256 (assinatura via JWKS do issuer, `aud`/`iss`/
  `exp`, scopes). Provider-agnóstico (qualquer AS OIDC).
- stdio e HTTP local sem auth seguem funcionando para uso local.
