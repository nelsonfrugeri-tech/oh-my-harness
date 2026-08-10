---
version: 1.0.0
name: sync-transport
description: |
  Move e verifica a travessia de arquivos entre máquinas pela capability `file-sync`,
  de forma agnóstica de engine. Cobre: a resolução do sync root, o contrato de 5 passos
  que toda engine precisa cumprir (health check do peer → pasta compartilhada existe →
  escrita → detecção forçada → verificação de propagação até 100%), o playbook de
  diagnóstico quando não propaga (peer offline, pasta não compartilhada, conflito de
  arquivo, ignore pattern), a regra dura de que escrever arquivo não é sincronizar, e o
  modo degradado quando não há engine plugada. A implementação concreta por engine vive
  em `references/` — hoje `syncthing.md` (REST API local, sem GUI). Invocada pelo agent
  `sync` para transportar/verificar — não destinada a invocação direta pelo usuário.
type: capability
---

# Sync Transport — A Travessia Entre Máquinas

Você garante que o que foi escrito de um lado **existe do outro**. Essa é a única coisa que
importa aqui, e ela não se prova com `ls` local.

A engine que faz a replicação varia por máquina (ferramenta de sync contínuo, storage
sincronizado, cópia sob demanda). Você não depende de uma: você cumpre um **contrato** e
descobre qual engine esta máquina tem pela capability `file-sync` na tabela *Ambiente & Tools*
do `AGENTS.md` aplicável.

## Sync root

O *sync root* é o único diretório replicado entre as máquinas. Resolva nesta ordem:

1. O caminho declarado na capability `file-sync` do `AGENTS.md` aplicável.
2. A pasta compartilhada que a engine reporta (ver a reference da engine).
3. Convenção de fallback: `~/sync`.

Confirme que o diretório existe antes de escrever. Se não existir, **não crie às cegas** — um
sync root fora da pasta que a engine replica é um diretório local comum que nunca vai
atravessar. Pergunte ou crie a pasta compartilhada pela engine primeiro.

## O contrato (5 passos)

Toda engine, qualquer que seja, precisa cumprir estes passos na ordem. A reference da engine
diz *como*; esta seção diz *o quê*.

| # | Passo | Critério de sucesso |
|---|---|---|
| 1 | **Health check do peer** | O device/destino remoto aparece como conectado |
| 2 | **Pasta compartilhada existe** | O sync root está registrado na engine e compartilhado com o peer |
| 3 | **Escrita** | Arquivos gravados dentro do sync root |
| 4 | **Detecção forçada** | A engine reconheceu os arquivos novos (não espere só o watcher) |
| 5 | **Verificação de propagação** | Propagação em 100% para o peer — em *loop com timeout*, nunca uma leitura única |

**Passo 5 é o único que autoriza dizer "chegou".** Enquanto ele não fecha, o relato correto é
"escrito localmente, propagação em N%".

## Diagnóstico quando não propaga

| Sintoma | Causa provável | Verificação |
|---|---|---|
| Propagação travada em 0% | Peer offline | Passo 1 — o device está conectado? |
| Arquivos não aparecem no inventário da engine | Pasta não é a compartilhada, ou detecção não rodou | Passos 2 e 4 |
| Propagação sobe e volta | Edição concorrente dos dois lados | Procure arquivos de conflito gerados pela engine |
| Um arquivo específico nunca vai | Ignore pattern, tamanho, ou permissão | Cheque os padrões de exclusão da engine e as permissões do arquivo |
| Propagação em 100% mas conteúdo antigo | Cópia parcial ou cache de leitura no destino | Force nova detecção e compare tamanho/hash |

Propagação a 100% prova **transferência**, não integridade. Para arquivo crítico, compare
hash dos dois lados quando tiver acesso ao destino.

## Regras duras

1. **Escrever arquivo não é sincronizar.** Nunca relate sucesso a partir de uma listagem
   local. O passo 5 é obrigatório.
2. **Nunca exponha credencial da engine.** Chave de API, token ou senha da engine são lidos
   em runtime para variável de ambiente e **jamais** aparecem em arquivo versionado, em nota
   da knowledge base, em bundle ou no chat. Ao mostrar um comando ao usuário, mostre a
   variável (`$API_KEY`), nunca o valor.
3. **Nunca escreva fora do sync root.** O escopo de escrita desta skill é exatamente o sync
   root — nada acima, nada em repositório do usuário.
4. **Não interprete silêncio como sucesso.** Comando sem erro ≠ propagação concluída.
5. **Timeout explícito.** O loop de verificação tem limite; ao estourar, relate o percentual
   alcançado e o que falta, em vez de esperar indefinidamente.

## Modo degradado

Se a capability `file-sync` estiver **vazia** ou a engine não estiver rodando:

- Escreva o bundle no destino local mesmo assim (o conteúdo não se perde).
- **Declare com todas as letras** que a propagação não aconteceu e por quê.
- Ofereça o caminho manual: o usuário mesmo copia o diretório, ou pluga a engine e você
  repete apenas os passos 4 e 5.

Nunca simule sucesso e nunca invente uma engine que a máquina não tem.

## Engines

A mecânica concreta de cada engine vive em `references/`:

- **Syncthing** (sync contínuo peer-to-peer, operado pela REST API local, sem GUI) —
  `references/syncthing.md`

Ao plugar uma engine nova, escreva uma reference que cumpra os 5 passos do contrato e
registre-a nesta lista.
