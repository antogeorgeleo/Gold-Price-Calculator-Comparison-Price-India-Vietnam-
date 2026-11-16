#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller --noconfirm --onefile --windowed --name "KeralaHanoiGoldTracker" --add-data "fonts:fonts" app.py

echo ""
echo "Build complete! Standalone binary is at:"
echo "  $(pwd)/dist/KeralaHanoiGoldTracker"
