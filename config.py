"""Configuration management for Kerala & Hanoi Gold Price Tracker."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "config.json"
DEFAULT_REPORTS_DIR = APP_DIR / "reports"

DEFAULT_CONFIG: dict[str, Any] = {
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "telegram_send_pdf": True,
    "whatsapp_phone": "",
    "whatsapp_mode": "browser_url",  # browser_url | pywhatkit | playwright_pdf
    "auto_refresh_enabled": True,
    "refresh_interval_seconds": 300,
    "reports_dir": str(DEFAULT_REPORTS_DIR),
}


def load_config() -> dict[str, Any]:
    """Load config from config.json, merging with defaults."""
    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                config.update(data)
        except Exception:
            pass
    Path(config["reports_dir"]).mkdir(parents=True, exist_ok=True)
    return config


def save_config(config: dict[str, Any]) -> None:
    """Persist configuration to config.json."""
    merged = dict(DEFAULT_CONFIG)
    merged.update(config)
    Path(merged["reports_dir"]).mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
