# Engine: Syncthing (REST API local)

Implementação dos 5 passos do contrato de `sync-transport` para o [Syncthing](https://syncthing.net/) —
sync contínuo peer-to-peer, operado **pela API REST local, sem GUI interativa**. É o caminho
para automação: um agent não clica na interface web.

Todos os exemplos usam placeholders. Substitua pelos valores desta máquina:

| Placeholder | O que é | Como descobrir |
|---|---|---|
| `$API_KEY` | Chave da API local | Passo 0 abaixo |
| `$FOLDER_ID` | ID da pasta compartilhada (≠ label) | `GET /rest/config/folders` |
| `$PEER_ID` | Device ID do peer remoto | `GET /rest/config/devices` |
| `$BASE` | Endpoint da API local | Default `http://127.0.0.1:8384/rest` |

## Passo 0 — Chave de API

A chave fica no `config.xml` do Syncthing. O caminho varia por sistema:

| Sistema | Caminho típico |
|---|---|
| macOS | `~/Library/Application Support/Syncthing/config.xml` |
| Linux | `~/.local/state/syncthing/config.xml` ou `~/.config/syncthing/config.xml` |
| Container | volume de config montado no container |

```bash
CONFIG="$HOME/Library/Application Support/Syncthing/config.xml"   # ajuste ao sistema
API_KEY=$(grep -o '<apikey>[^<]*</apikey>' "$CONFIG" | sed 's/<[^>]*>//g')
BASE="http://127.0.0.1:8384/rest"
```

**A chave é credencial.** Mantenha em variável de ambiente na sessão; nunca escreva o valor
em arquivo, nota, bundle ou chat. Todo request usa o header `X-API-Key: $API_KEY`.

Se o `config.xml` não existir ou o `curl` recusar conexão, o Syncthing não está rodando nesta
máquina → **modo degradado** da skill.

## Passo 1 — Health check do peer

```bash
curl -fsS -H "X-API-Key: $API_KEY" "$BASE/system/connections" \
  | jq -e '.connections | objects'
```

Cada device traz `connected: true|false` e taxas de transferência. O peer precisa estar
`connected: true`. Se estiver `false`, nada vai propagar — reporte e pare aqui.

Devices and folders offered but not accepted yet:

```bash
curl -fsS -H "X-API-Key: $API_KEY" "$BASE/cluster/pending/devices" | jq -e .
curl -fsS -H "X-API-Key: $API_KEY" "$BASE/cluster/pending/folders" | jq -e .
```

If either response contains an item, treat it as a stop condition. Report the exact sanitized
device ID, device name, folder ID, folder path, and proposed share type. Request **explicit
authorization** before accepting a device or folder. A prior request to copy files does not
authorize changing the Syncthing trust graph.

Only after that authorization, accept the exact pending device that was presented:

```bash
curl -fsS -X PUT -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d "{\"deviceID\":\"$PEER_ID\",\"name\":\"<nome-legivel>\"}" \
  "$BASE/config/devices/$PEER_ID"
```

## Passo 2 — Pasta compartilhada existe

```bash
curl -fsS -H "X-API-Key: $API_KEY" "$BASE/config/folders" \
  | jq '.[] | {id, label, path, type, devices: [.devices[].deviceID]}'
```

Confirm that a folder exists whose `path` is the sync root and whose `devices` list contains
the peer. A missing folder or missing peer share is another stop condition: present the exact
folder ID, path, peer ID, and proposed type, then request **explicit authorization**.

### Existing folder: preserve and merge

For an existing folder, retrieve the complete object. The proposed payload preserves every
existing field and device, and appends the peer only when absent:

```bash
CURRENT_FOLDER=$(curl -fsS -H "X-API-Key: $API_KEY" \
  "$BASE/config/folders/$FOLDER_ID" | jq -ce 'select(type == "object")')
PROPOSED_FOLDER=$(printf '%s' "$CURRENT_FOLDER" | jq -ce --arg peer "$PEER_ID" '
  if any(.devices[]?; .deviceID == $peer)
  then .
  else .devices = ((.devices // []) + [{"deviceID": $peer}])
  end
')
diff -u \
  <(printf '%s' "$CURRENT_FOLDER" | jq -S .) \
  <(printf '%s' "$PROPOSED_FOLDER" | jq -S .)
```

Present that exact diff, the resolved folder path, and the peer ID. Stop for **explicit
authorization**. Only after approval of those exact values, publish the full merged object:

```bash
curl -fsS -X PUT -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  --data-binary "$PROPOSED_FOLDER" \
  "$BASE/config/folders/$FOLDER_ID"
curl -fsS -H "X-API-Key: $API_KEY" "$BASE/config/folders/$FOLDER_ID" \
  | jq -e --arg peer "$PEER_ID" 'any(.devices[]?; .deviceID == $peer)'
```

If the diff is empty, the peer is already configured; do not send a PUT.

### Absent folder: create explicitly

Only when the folder is absent, propose a new minimal payload. Prefer `sendonly` for a
publishing machine so a remote peer cannot overwrite the local source of truth:

```bash
curl -fsS -X PUT -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$FOLDER_ID\",
    \"label\": \"<label>\",
    \"path\": \"$HOME/sync\",
    \"type\": \"sendonly\",
    \"devices\": [{\"deviceID\":\"$PEER_ID\"}]
  }" \
  "$BASE/config/folders/$FOLDER_ID"
curl -fsS -H "X-API-Key: $API_KEY" "$BASE/config/folders/$FOLDER_ID" \
  | jq -e --arg peer "$PEER_ID" '.type == "sendonly" and any(.devices[]?; .deviceID == $peer)'
```

Use `sendreceive` only when the user explicitly authorizes bidirectional writes and the source
of truth has been defined. The folder appears as pending on the peer and requires a separate
authorization there.

## Passo 3 — Escrita

Escreva os arquivos normalmente dentro do sync root (é filesystem comum). Nada de especial —
o cuidado está nos passos seguintes.

## Passo 4 — Detecção forçada

```bash
curl -fsS -X POST -H "X-API-Key: $API_KEY" "$BASE/db/scan?folder=$FOLDER_ID"
```

O watcher detecta sozinho com alguns segundos de atraso; o rescan força a detecção imediata e
é barato. Na dúvida, rescan.

Estado local da pasta:

```bash
curl -fsS -H "X-API-Key: $API_KEY" "$BASE/db/status?folder=$FOLDER_ID" \
  | jq -e '{state, localFiles, localDirectories, globalFiles, needFiles}'
```

`state: "idle"` com `needFiles: 0` significa que este lado terminou seu trabalho.

## Passo 5 — Verificação de propagação

```bash
curl -fsS -H "X-API-Key: $API_KEY" \
  "$BASE/db/completion?folder=$FOLDER_ID&device=$PEER_ID" \
  | jq -e '{completion, needBytes, needItems}'
```

`completion` é o percentual **já refletido no peer**. Em loop, com timeout:

```bash
DEADLINE=$(( $(date +%s) + 120 ))          # 2 min de teto
while :; do
  PCT=$(curl -fsS -H "X-API-Key: $API_KEY" \
    "$BASE/db/completion?folder=$FOLDER_ID&device=$PEER_ID" | jq -er '.completion')
  printf 'completion: %s%%\n' "$PCT"
  [ "${PCT%.*}" -ge 100 ] 2>/dev/null && break
  [ "$(date +%s)" -ge "$DEADLINE" ] && { echo "timeout em ${PCT}%"; break; }
  sleep 3
done
```

Ao estourar o timeout, reporte o percentual alcançado e `needItems` — nunca fique preso nem
declare sucesso.

## Notas operacionais

- **`completion` mede transferência, não integridade.** Para arquivo crítico, compare hash
  dos dois lados quando houver acesso ao destino.
- **Conflitos** geram arquivos com sufixo `~conflict-<data>` ao lado do original — sinal de
  edição simultânea nos dois lados. Não apague sem ler.
- **Ignore patterns** (`.stignore` na raiz da pasta) silenciosamente excluem arquivos: se um
  item específico nunca propaga, cheque esse arquivo antes de suspeitar da rede.
- **Sem SSH é o caso normal.** Quando a porta 22 do peer está fechada, esta engine é o único
  canal de escrita — o que torna o passo 5 ainda mais importante: não há outra forma de
  conferir do outro lado.
- **Documentação oficial:** <https://docs.syncthing.net/rest/index.html>
