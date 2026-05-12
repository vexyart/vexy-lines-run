#!/usr/bin/env bash
# install.sh - Install vexy-lines-run in editable mode
# Vexy Lines is a macOS vector art application.
# GUI desktop application for Vexy Lines style transfer.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Installing vexy-lines-run in editable mode..."
uv pip install --system -e .

echo "==> Install complete."
