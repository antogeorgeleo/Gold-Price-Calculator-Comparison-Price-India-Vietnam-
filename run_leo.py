"""
LEO — One-Click Local Desktop Launcher
Created by Anto George Leo

Run this file on your PC (`python run_leo.py`) to launch the LEO server
and automatically open the luxury application window in your browser.
"""

import os
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    env = os.environ.copy()
    env["LEO_OPEN_BROWSER"] = "1"
    app_path = Path(__file__).resolve().parent / "app.py"
    subprocess.run([sys.executable, str(app_path)], env=env, check=True)
