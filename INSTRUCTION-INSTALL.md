# Instruções de instalação

Este guia tem duas fases. Execute na ordem.

| Fase | O que configura | Resultado |
| --- | --- | --- |
| 1 | Permissões do Kiro | O agente trabalha sem pedir permissão e só pergunta antes de excluir algo ou de ler dados sensíveis. |
| 2 | Terminal zsh no Ubuntu | Prompt Starship, plugins do zsh e ferramentas de linha de comando. |


## Pré-requisito: dar `sudo` ao usuário `<usuario>`

Troque `<usuario>`, `<dominio>` e `<usuario-sem-ponto>` (o usuário com `-` no lugar de `.`). Depois, na conta **administrador**, cole o bloco. Quando o terminal pedir, digite a
senha do **administrador**.

```bash
printf '%s\n' '<usuario>@<dominio> ALL=(ALL:ALL) ALL' '<usuario> ALL=(ALL:ALL) ALL' | sudo tee /etc/sudoers.d/<usuario-sem-ponto> >/dev/null && sudo chmod 440 /etc/sudoers.d/<usuario-sem-ponto> && sudo visudo -c && echo "SUDO OK"
```

O resultado precisa terminar com `SUDO OK`. Se aparecer erro, apague o arquivo e cole o bloco
de novo:

```bash
sudo rm -f /etc/sudoers.d/<usuario-sem-ponto>
```

Depois, saia da conta administrador, entre na conta `<usuario>` e copie e cole:

```bash
sudo -v && echo "SUDO OK"
```

Digite a senha do `<usuario>`. O resultado precisa ser `SUDO OK`.

---

## Fase 1: permissões do Kiro

### Objetivo

Configurar o Kiro (IDE 1.x e CLI v3) para:

- **executar tudo sem pedir permissão**, como o modo `bypassPermissions` do Claude Code;
- **pedir permissão só em dois casos**:
  1. excluir arquivos, diretórios ou outros artefatos;
  2. ler dados sensíveis, como chaves de API, credenciais, tokens, chaves privadas e arquivos `.env`.

### Como o Kiro decide

- As regras ficam em `permissions.yaml`. Cada regra tem `capability`, `match` (opcional), `exclude`
  (opcional) e `effect`.
- Os efeitos são `allow`, `ask` e `deny`. A precedência é `deny` > `ask` > `allow`. O efeito mais
  restritivo vence, em qualquer escopo.
- `capability: all` cobre todas as capabilities, exceto `sandbox_network`.
- Nos padrões de `fs_read` e `fs_write`, `*` casa dentro de um diretório e `**` atravessa
  diretórios. Nos padrões de `shell`, só existe `*`, que casa qualquer sequência de caracteres.
- Comandos compostos (`;`, `&&`, `||`, `|`) são divididos, e o Kiro avalia cada parte.

Referência: <https://kiro.dev/docs/permissions/>

### Passo 1: fazer backup da configuração atual

```bash
mkdir -p ~/.kiro/settings
[ -f ~/.kiro/settings/permissions.yaml ] && \
  cp ~/.kiro/settings/permissions.yaml ~/.kiro/settings/permissions.yaml.bak
```

Se o arquivo já existir, **leia-o antes de alterar**. Preserve as regras `deny` que já estiverem
lá. Não remova nenhuma regra sem confirmar com o usuário.

### Passo 2: escrever as regras no escopo do usuário

Arquivo: `~/.kiro/settings/permissions.yaml` (vale para todos os projetos).

```yaml
rules:
  # 1. Base: libera tudo sem perguntar (equivalente ao bypass)
  - capability: all
    effect: allow

  # 2. Pergunta antes de ler segredos pela tool nativa de leitura
  - capability: fs_read
    match:
      - "**/.env"
      - "**/.env.*"
      - "**/*.pem"
      - "**/*.key"
      - "**/*.p12"
      - "**/*.pfx"
      - "**/*credentials*"
      - "**/*secret*"
      - "~/.ssh/**"
      - "~/.aws/**"
      - "~/.kube/**"
      - "~/.gnupg/**"
      - "~/.config/gh/**"
      - "~/.docker/config.json"
      - "~/.netrc"
      - "~/.npmrc"
      - "~/.pypirc"
      - "~/.secrets"
    effect: ask

  # 3. Pergunta antes de excluir pelo shell
  - capability: shell
    match:
      - "rm *"
      - "rmdir *"
      - "unlink *"
      - "shred *"
      - "git rm *"
      - "git clean *"
      - "find * -delete*"
    effect: ask

  # 4. Pergunta antes de ler segredos pelo shell (filtro por texto do comando)
  - capability: shell
    match:
      - "*.env*"
      - "*.ssh/*"
      - "*.aws/*"
      - "*.kube/*"
      - "*.gnupg/*"
      - "*credentials*"
      - "*.pem*"
      - "*secret*"
      - "*token*"
      - "env"
      - "printenv*"
    effect: ask
```

### Passo 3: bloquear a exclusão pela tool nativa

A tool `delete_file` usa a capability `fs_write`, a mesma de criar e editar arquivos. Uma regra
em `permissions.yaml` filtra só por caminho, então não consegue separar "excluir" de "editar".

A solução é tirar a tool do agente. Sem ela, a única forma de excluir é pelo shell (`rm`), que
cai na regra 3 e pergunta.

No custom agent que será usado, adicione `delete_file` em `excludedTools`:

```json
{
  "excludedTools": ["delete_file"]
}
```

Antes de editar, consulte o formato atual do profile de agent:
<https://kiro.dev/docs/custom-agents/configuration-reference/>

### Passo 4: escolher o modo

- **IDE:** use o modo **"Accept file changes"** ou **"Approve for me"**. Nos dois, as regras `ask`
  continuam perguntando. Não use **"Supervised"**, porque ele pergunta tudo.
- **CLI:** as regras bastam. Não é necessário usar `--trust-all-tools`.

### Passo 5: validar

Abra uma sessão nova e teste cada caso:

| Teste | Comportamento esperado |
| --- | --- |
| Criar e editar um arquivo comum | Executa sem perguntar |
| Rodar `ls`, `git status`, `npm test` | Executa sem perguntar |
| `rm` de um arquivo de teste | **Pergunta** |
| Ler um arquivo `.env` de teste | **Pergunta** |
| `cat ~/.aws/credentials` (ou outro arquivo sensível) | **Pergunta** |
| Pedir para excluir um arquivo sem citar `rm` | Usa `rm` pelo shell e **pergunta** |

Se algum teste não se comportar como esperado, pare e informe o usuário. Não afrouxe as regras
para fazer o teste passar.

### Limitações conhecidas

- **A leitura pelo shell é heurística.** A regra 4 compara o texto do comando. Um comando
  indireto, como `python -c "open(...)"`, pode escapar dela. Com o sandbox local do Kiro ativo, as
  regras de `fs_read` também se aplicam aos comandos do shell. Não está confirmado se, nesse caso,
  um `ask` pergunta ou bloqueia. Consulte <https://kiro.dev/docs/sandbox/> antes de ativar.
- **Falsos positivos:** padrões como `*token*` e `*secret*` também perguntam em comandos
  inofensivos. Ajuste a lista com o uso.
- **Perguntas fixas do Kiro:** o Kiro sempre pergunta antes de alterar `.git/**`, `.vscode/**`,
  agents, hooks, workflows e powers. Esse comportamento não pode ser desligado.
- **Modo headless:** sem interface interativa, todo `ask` vira `deny`.

### Referências da Fase 1

- <https://kiro.dev/docs/permissions/>
- <https://kiro.dev/docs/tools/>
- <https://kiro.dev/docs/custom-agents/configuration-reference/>
- <https://kiro.dev/changelog/ide/1-4-154/>

---

## Fase 2: terminal zsh no Ubuntu

Esta fase replica um terminal zsh completo num Ubuntu. O setup **não usa oh-my-zsh**. O
resultado vem de zsh + Starship + plugins e ferramentas de linha de comando.

### O que compõe o setup

| Peça | Função | Instalação no Ubuntu |
| --- | --- | --- |
| `starship` | Prompt (preset padrão, sem `starship.toml`) | Script oficial |
| `zsh-autosuggestions` | Sugestões enquanto você digita | `apt` |
| `zsh-syntax-highlighting` | Cores na linha de comando | `apt` |
| `zoxide` | Navegação com `z <pasta>` | `apt` |
| `fzf` | Busca fuzzy, `Ctrl+R` no histórico | `apt` |
| `eza` | `ls` com ícones e status do git | `apt` |
| `bat` | `cat` com cores (o binário se chama `batcat`) | `apt` |
| `fnm` | Gerenciador de versões do Node | Script oficial |

### 1. Instalar os pacotes

```bash
sudo apt update
sudo apt install -y zsh git curl unzip \
  zsh-autosuggestions zsh-syntax-highlighting \
  zoxide fzf eza bat
```

### 2. Instalar Starship e fnm

```bash
curl -sS https://starship.rs/install.sh | sh
curl -fsSL https://fnm.vercel.app/install | bash -s -- --skip-shell
```

### 3. Tornar o zsh o shell padrão

```bash
chsh -s "$(which zsh)"
```

A troca vale a partir do próximo login.

### 4. Criar o `~/.zshrc`

```zsh
export PATH="$HOME/.local/bin:$HOME/.local/share/fnm:$PATH"

# Prompt
eval "$(starship init zsh)"

# Plugins
source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# Navegação e busca
eval "$(zoxide init zsh)"
if fzf --zsh >/dev/null 2>&1; then
  source <(fzf --zsh)
else
  source /usr/share/doc/fzf/examples/key-bindings.zsh
fi

# Aliases
alias ls='eza --icons --git'
alias ll='eza -la --icons --git'
alias cat='batcat'

# Node
eval "$(fnm env --use-on-cd --shell zsh)"

# Segredos (fora do .zshrc)
[ -f ~/.secrets ] && source ~/.secrets
```

Depois, instale o Node:

```bash
fnm install 24
```

### 5. Instalar uma Nerd Font

O `eza --icons` e o Starship precisam de uma **Nerd Font**. Sem ela, os ícones aparecem como
quadrados.

1. Baixe uma fonte em <https://www.nerdfonts.com/font-downloads> (exemplo: JetBrainsMono Nerd Font).
2. Extraia os arquivos para `~/.local/share/fonts` e rode `fc-cache -fv`.
3. Selecione a fonte nas preferências do terminal.

### Cuidados

- **Chaves de API:** não coloque chaves no `.zshrc`. Use um arquivo `~/.secrets`, protegido com
  `chmod 600`, contendo linhas como `export OPENAI_API_KEY=...`. O `.zshrc` acima já carrega esse
  arquivo. A Fase 1 já pede permissão antes de o Kiro ler `~/.secrets`.
- **Ubuntu 22.04 ou anterior:** o `eza` pode não estar disponível no `apt`. Nesse caso, use
  `cargo install eza`. O `fzf` do `apt` pode ser antigo demais para `fzf --zsh`. O `.zshrc` acima já
  usa o arquivo de atalhos do pacote como fallback. Confira a versão com `lsb_release -a`.
- **Ferramentas opcionais** (LM Studio, rustup etc.): instale só se for usá-las.

### Alternativa: Homebrew no Linux

O Homebrew também roda no Linux e deixa o `.zshrc` quase igual ao do macOS. Em troca, você tem um
setup mais pesado e um segundo gerenciador de pacotes. Prefira o `apt` + scripts oficiais.
