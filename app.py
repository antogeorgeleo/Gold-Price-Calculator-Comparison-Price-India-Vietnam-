"""
LEO — Luxury Vietnam & India Gold Rate Comparison Application
Created by Anto George Leo

Main Python Flask server providing:
- Interactive real-time gold comparison in Chi (3.75g), Gram (1.00g), and Pavan (8.00g)
- 10 switchable luxury color themes
- Built-in ambient background music tracks + custom audio support
- Export to PDF, Excel (.xlsx), WhatsApp, Telegram, and Print-ready executive layout
"""

from __future__ import annotations

import io
import os
import threading
import webbrowser
from pathlib import Path
from typing import Any, Dict

from flask import Flask, Response, jsonify, render_template, request, send_file

from export_service import (
    generate_excel_report,
    generate_pdf_report,
    send_via_telegram_bot,
)
from gold_engine import (
    DEFAULT_FX_INR_TO_VND,
    DEFAULT_IN_GRAM_INR,
    DEFAULT_VN_CHI_VND,
    THEMES,
    calculate_gold_comparison,
    get_live_fx_rate,
)
from music_generator import ensure_ambient_tracks

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"

app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    template_folder=str(TEMPLATE_DIR),
)
app.config["JSON_AS_ASCII"] = False

# Ensure ambient music tracks are synthesized on startup
AUDIO_TRACKS = ensure_ambient_tracks(STATIC_DIR / "audio")


@app.after_request
def add_preview_friendly_headers(response: Response) -> Response:
    """Ensure compatibility with live preview proxies and cross-origin embedding."""
    response.headers.pop("X-Frame-Options", None)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def _extract_params(source: Dict[str, Any]) -> Dict[str, Any]:
    """Safely parse gold comparison parameters from JSON body or query string."""
    def _to_float(val: Any, default: float) -> float:
        if val is None or val == "":
            return default
        try:
            cleaned = str(val).replace(",", "").strip()
            return float(cleaned)
        except Exception:
            return default

    return {
        "vn_price_per_chi_vnd": _to_float(source.get("vn_price_per_chi_vnd"), DEFAULT_VN_CHI_VND),
        "in_price_per_gram_inr": _to_float(source.get("in_price_per_gram_inr"), DEFAULT_IN_GRAM_INR),
        "fx_inr_to_vnd": _to_float(source.get("fx_inr_to_vnd"), DEFAULT_FX_INR_TO_VND),
        "purity": str(source.get("purity") or "24K (999.9 Pure Gold)"),
        "vn_extra_pct": _to_float(source.get("vn_extra_pct"), 0.0),
        "in_extra_pct": _to_float(source.get("in_extra_pct"), 0.0),
        "custom_qty": _to_float(source.get("custom_qty"), 1.0),
        "custom_unit": str(source.get("custom_unit") or "pavan"),
        "theme_id": str(source.get("theme_id") or "imperial_gold"),
        "customer_note": str(source.get("customer_note") or ""),
    }


@app.route("/")
def index() -> str:
    fx_info = get_live_fx_rate(force_refresh=False)
    initial_report = calculate_gold_comparison(
        vn_price_per_chi_vnd=DEFAULT_VN_CHI_VND,
        in_price_per_gram_inr=DEFAULT_IN_GRAM_INR,
        fx_inr_to_vnd=fx_info["rate"],
    )
    return render_template(
        "index.html",
        themes=list(THEMES.values()),
        tracks=AUDIO_TRACKS,
        fx_info=fx_info,
        initial_report=initial_report,
    )


@app.route("/api/fx", methods=["GET"])
def api_fx() -> Response:
    force = request.args.get("refresh", "0") == "1"
    fx_info = get_live_fx_rate(force_refresh=force)
    return jsonify({"ok": True, **fx_info})


@app.route("/api/calculate", methods=["POST"])
def api_calculate() -> Response:
    payload = request.get_json(silent=True) or {}
    params = _extract_params(payload)
    report = calculate_gold_comparison(**params)
    return jsonify({"ok": True, "report": report})


@app.route("/api/export/pdf", methods=["GET", "POST"])
def api_export_pdf() -> Response:
    raw = (request.get_json(silent=True) or {}) if request.method == "POST" else request.args.to_dict()
    params = _extract_params(raw)
    report = calculate_gold_comparison(**params)
    pdf_bytes, filename = generate_pdf_report(report, save_to_disk=True)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/api/export/excel", methods=["GET", "POST"])
def api_export_excel() -> Response:
    raw = (request.get_json(silent=True) or {}) if request.method == "POST" else request.args.to_dict()
    params = _extract_params(raw)
    report = calculate_gold_comparison(**params)
    xlsx_bytes, filename = generate_excel_report(report, save_to_disk=True)
    return send_file(
        io.BytesIO(xlsx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/api/share/telegram", methods=["POST"])
def api_share_telegram() -> Response:
    payload = request.get_json(silent=True) or {}
    params = _extract_params(payload)
    report = calculate_gold_comparison(**params)
    bot_token = str(payload.get("bot_token") or "")
    chat_id = str(payload.get("chat_id") or "")
    attach_pdf = bool(payload.get("attach_pdf", True))
    res = send_via_telegram_bot(bot_token, chat_id, report, attach_pdf=attach_pdf)
    return jsonify(res)


@app.route("/print")
def print_view() -> str:
    params = _extract_params(request.args.to_dict())
    report = calculate_gold_comparison(**params)
    auto_print = request.args.get("autoprint", "1") == "1"
    return render_template("print_report.html", report=report, auto_print=auto_print)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    if os.environ.get("LEO_OPEN_BROWSER", "0") == "1":
        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    print(f"🦁 LEO Gold Rate Comparison Application (Created by Anto George Leo) running on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
