#!/usr/bin/env bash
# LEO — Vietnam / India Gold Rate Comparison  ·  Created by Anto George Leo
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  exec python3 leo_desktop.py
else
  echo "Python 3 is required. Install it from https://python.org"
  read -r -p "Press Enter to close…" _
fi
