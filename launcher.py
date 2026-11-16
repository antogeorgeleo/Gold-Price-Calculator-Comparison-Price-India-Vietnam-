"""Zero-setup bootstrap launcher for Kerala & Hanoi Live Gold Tracker.

Double-clicking or running this script automatically:
1. Creates a local .venv (if not already running inside one)
2. Installs core dependencies (requests, beautifulsoup4, reportlab) on first run
3. Launches the desktop GUI (app.py)
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
VENV_DIR = APP_DIR / ".venv"
CORE_MODULES = ("requests", "bs4", "reportlab")


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _has_core_modules(py_exe: str) -> bool:
    code = "import requests, bs4, reportlab"
    res = subprocess.run([py_exe, "-c", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0


def _ensure_environment() -> str:
    # 1. If current interpreter already has everything, use it directly
    if all(importlib.util.find_spec(m) is not None for m in CORE_MODULES):
        return sys.executable

    # 2. Otherwise use/create local .venv
    vpy = _venv_python()
    if not vpy.exists():
        print("[Setup] Creating isolated Python virtual environment (.venv)...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

    if not _has_core_modules(str(vpy)):
        print("[Setup] Installing core dependencies (requests, beautifulsoup4, reportlab)...")
        subprocess.check_call([str(vpy), "-m", "pip", "install", "--upgrade", "pip", "-q"])
        subprocess.check_call(
            [str(vpy), "-m", "pip", "install", "-r", str(APP_DIR / "requirements.txt"), "-q"]
        )

    return str(vpy)


def main() -> None:
    target_py = _ensure_environment()
    app_script = str(APP_DIR / "app.py")

    if Path(target_py).resolve() == Path(sys.executable).resolve():
        # Already in the right Python environment — run app directly
        sys.path.insert(0, str(APP_DIR))
        import app
        app.main()
    else:
        # Relaunch inside .venv
        if os.name == "nt":
            pythonw = Path(target_py).with_name("pythonw.exe")
            exe = str(pythonw) if pythonw.exists() else target_py
            subprocess.Popen([exe, app_script], cwd=str(APP_DIR))
        else:
            os.execv(target_py, [target_py, app_script])


if __name__ == "__main__":
    main()
