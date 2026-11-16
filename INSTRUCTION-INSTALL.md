# Terminal zsh no Ubuntu

Este guia replica, num Ubuntu, o terminal zsh usado no macOS. O setup **não usa oh-my-zsh**. O
resultado vem de zsh + Starship + plugins e ferramentas de linha de comando.

## O que compõe o setup

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

## 1. Instalar os pacotes

```bash
sudo apt update
sudo apt install -y zsh git curl unzip \
  zsh-autosuggestions zsh-syntax-highlighting \
  zoxide fzf eza bat
```

## 2. Instalar Starship e fnm

```bash
curl -sS https://starship.rs/install.sh | sh
curl -fsSL https://fnm.vercel.app/install | bash -s -- --skip-shell
```

## 3. Tornar o zsh o shell padrão

```bash
chsh -s "$(which zsh)"
```

A troca vale a partir do próximo login.

## 4. Criar o `~/.zshrc`

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

## 5. Instalar uma Nerd Font

O `eza --icons` e o Starship precisam de uma **Nerd Font**. Sem ela, os ícones aparecem como
quadrados.

1. Baixe uma fonte em <https://www.nerdfonts.com/font-downloads> (exemplo: JetBrainsMono Nerd Font).
2. Extraia os arquivos para `~/.local/share/fonts` e rode `fc-cache -fv`.
3. Selecione a fonte nas preferências do terminal.

## Cuidados

- **Chaves de API:** não coloque chaves no `.zshrc`. Use um arquivo `~/.secrets`, protegido com
  `chmod 600`, contendo linhas como `export OPENAI_API_KEY=...`. O `.zshrc` acima já carrega esse
  arquivo.
- **Ubuntu 22.04 ou anterior:** o `eza` pode não estar disponível no `apt`. Nesse caso, use
  `cargo install eza`. O `fzf` do `apt` pode ser antigo demais para `fzf --zsh`. O `.zshrc` acima já
  usa o arquivo de atalhos do pacote como fallback. Confira a versão com `lsb_release -a`.
- **Ferramentas específicas da máquina** (LM Studio, rustup, deja-vu etc.): instale só se for usá-las
  no Ubuntu.

## Alternativa: Homebrew no Linux

O Homebrew também roda no Linux e deixa o `.zshrc` quase igual ao do macOS. Em troca, você tem um
setup mais pesado e um segundo gerenciador de pacotes. Prefira o `apt` + scripts oficiais.
