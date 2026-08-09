#!/usr/bin/env bash
# Claude Code adapter for the shared context loader.

set -uo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  SOURCE_DIR=$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd) || exit 0
  LINK=$(readlink "$SOURCE") || exit 0
  case "$LINK" in
    /*) SOURCE="$LINK" ;;
    *) SOURCE="$SOURCE_DIR/$LINK" ;;
  esac
done
SOURCE_DIR=$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd) || exit 0

exec "$SOURCE_DIR/../../hooks/context-load.sh" "$@"
