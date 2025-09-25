#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Virtualenv not found; run scripts/setup_venv.sh first" >&2
  exit 2
fi

"$VENV_DIR/bin/python" "$@"
