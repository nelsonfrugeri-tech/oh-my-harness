---
version: 1.1.0
name: codex
description: |
  Instala e sincroniza oh-my-harness no Codex. Cobre o plugin nativo com Git, agents customizados,
  conteúdo gerenciado de AGENTS.md global, lifecycle hooks, verificações de integração MCP,
  tratamento de conflitos e validação pós-instalação. Use para o primeiro setup do Codex,
  sincronização após atualização do repositório ou diagnóstico de uma instalação parcial do Codex.
type: capability
---

# Codex — Instalação e sincronização global

Use o plugin nativo para skills compartilhadas, a skill de instalação exclusiva do Codex e lifecycle hooks.
Use o adapter versionado em `codex/` para agents customizados, orientações globais e integrações locais
da máquina; não reinterprete arquivos do Claude Code durante a instalação. O installer preserva a
configuração global pertencente ao usuário.

## Instalar ou atualizar o plugin nativo

```bash
codex plugin marketplace add nelsonfrugeri-tech/oh-my-harness
codex plugin add oh-my-harness@oh-my-harness
codex plugin list
```

Use `codex plugin marketplace upgrade oh-my-harness` para atualizar o catálogo com Git antes de
instalar uma versão mais nova do manifesto. Inicie uma nova sessão após a instalação ou upgrade. Abra
`/hooks`, revise os comandos incluídos e confie em suas definições exatas; o Codex ignora hooks não
gerenciados novos ou alterados até que essa revisão explícita seja concluída.

O quality gate de commit exige um segundo opt-in por repositório, pois executa comandos
descobertos nele. Em um checkout cujo código você revisou, execute uma vez:

```bash
common_git_dir=$(git rev-parse --path-format=absolute --git-common-dir)
repo_sig=$(printf '%s' "$common_git_dir" | shasum -a 256 | cut -d' ' -f1 | cut -c1-12)
trust_dir="${XDG_CACHE_HOME:-$HOME/.cache}/omh-quality-gate/trusted"
mkdir -p "$trust_dir"
touch "$trust_dir/$repo_sig"
```

Confiar via `/hooks` autoriza a definição do hook do plugin. O marcador acima autoriza separadamente
os comandos de format, lint, typecheck e teste controlados pelo repositório. Sem ambos, o gate
intencionalmente adia a execução em vez de executar código do projeto.

O context hook exclusivo do plugin instrui o Codex a executar diretamente a skill `explorer` incluída.
Quando o adapter global também estiver presente, seu agent customizado `context` pode orquestrar esse workflow.

## Instalar ou sincronizar o adapter global

Na raiz do repositório, execute:

```bash
python3 codex/install.py
python3 codex/install.py --check
```

O installer:

1. cria links das skills compartilhadas e exclusivas do Codex em `~/.agents/skills/<name>/`, excluindo a
   skill de instalação exclusiva do Claude;
2. cria links dos TOMLs de agents customizados do Codex em `~/.codex/agents/`;
3. cria o link do adapter completo em `~/.codex/oh-my-harness`;
4. substitui somente o bloco `omh-managed` dentro de `~/.codex/AGENTS.md` global;
5. substitui somente o context hook gerenciado em `~/.codex/hooks.json`, preservando hooks não relacionados;
6. configura Deja, Graphify, as integrações oficiais de skills e documentação LangChain e as skills oficiais AI Evals;
7. reporta integrações vinculadas a conta que ainda exigem autorização humana.

Execute com `--skip-integrations` quando somente os artefatos de filesystem precisarem ser sincronizados.
Use `--replace-global-agents` apenas ao migrar um arquivo global legado confirmado de oh-my-harness;
o installer cria `AGENTS.md.omh.bak` antes de substituí-lo.

## Política de conflitos

Nunca sobrescreva um arquivo ou diretório pertencente ao usuário onde for esperado um symlink gerenciado. Pare e mostre
o path exato. O usuário deve decidir se quer preservá-lo, movê-lo ou substituí-lo. Blocos de texto gerenciados
e entradas de hooks gerenciadas podem ser atualizados com segurança porque seus marcadores de posse são explícitos.

Antes de alterar um arquivo global editável, o installer cria um sibling `.omh.bak` de uso único.

## Validação

`--check` é somente leitura e deve passar antes de reportar o setup como concluído. Em seguida, verifique o
inventário MCP ativo pela superfície de configuração MCP do Codex. Providers vinculados a conta podem permanecer
pending, mas o relatório deve distinguir software ausente de autorização ausente.

## Conduta no repositório

Este repositório é a fonte de verdade. A instalação escreve somente no estado global do Codex e no
diretório pessoal de skills. Diagnósticos temporários pertencem a `/tmp`, nunca ao repositório.
