#!/usr/bin/env bash
#
# install.sh — link this library's agents and skills into a Claude Code home.
#
# Symlinks (never copies) agents/ and skills/ so `git pull` keeps them current.
# CLAUDE.md and settings.json are copied once (not linked): they carry the
# per-machine capability plug table, which you edit locally.
#
# Usage:
#   ./install.sh                 # install into ~/.claude
#   CLAUDE_HOME=/path ./install.sh   # install into a custom home

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

link() {
  local src="$1" dest="$2"
  ln -sfn "$src" "$dest"
  echo "  linked $(basename "$dest")"
}

echo "Instalando em: $CLAUDE_HOME"
mkdir -p "$CLAUDE_HOME/agents" "$CLAUDE_HOME/skills"

echo "agents:"
for agent in "$REPO_DIR"/agents/*.md; do
  link "$agent" "$CLAUDE_HOME/agents/$(basename "$agent")"
done

echo "skills:"
for skill in "$REPO_DIR"/skills/*/; do
  link "${skill%/}" "$CLAUDE_HOME/skills/$(basename "${skill%/}")"
done

echo "config (copiado só se ainda não existir — edite a tabela de capabilities):"
for file in CLAUDE.md settings.json; do
  dest="$CLAUDE_HOME/$file"
  if [[ -e "$dest" ]]; then
    echo "  mantido $file (já existe)"
  else
    cp "$REPO_DIR/claude-code/$file" "$dest"
    echo "  copiado $file"
  fi
done

echo ""
echo "Pronto. Edite a seção '## Ambiente & Tools' em $CLAUDE_HOME/CLAUDE.md"
echo "para plugar as tools desta máquina (code-host, ci, memory)."
