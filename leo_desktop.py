#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEO — Luxury Vietnam ⇄ India Gold Rate Comparison
=================================================
A premium desktop application (Python + Tkinter).

Created by Anto George Leo

Run:
    python3 leo_desktop.py
    (Windows:  py leo_desktop.py  or double-click Leo.bat)

Only pure-Python standard library is required to start the app.
PDF / Excel export need reportlab + openpyxl (the app tells you politely
if they are missing and keeps working).
"""

from __future__ import annotations

import array
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import wave
import webbrowser
from datetime import datetime

import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox

# --------------------------------------------------------------------------
#  BRAND
# --------------------------------------------------------------------------
APP_NAME = "LEO"
APP_TAGLINE = "Vietnam  ⇄  India   ·   Gold Rate Comparison"
APP_CREDIT = "Created by Anto George Leo"
APP_VERSION = "2.0"

# --------------------------------------------------------------------------
#  GOLD STANDARDS
# --------------------------------------------------------------------------
GRAMS_PER_CHI = 3.75
GRAMS_PER_GRAM = 1.00
GRAMS_PER_PAVAN = 8.00
GRAMS_PER_LUONG = 37.50

DEFAULT_VN_CHI_VND = 14_100_000.0
DEFAULT_IN_GRAM_INR = 13_849.00
DEFAULT_FX_INR_TO_VND = 273.07

# --------------------------------------------------------------------------
#  10 LUXURY THEMES
# --------------------------------------------------------------------------
THEMES = [
    {
        "id": "imperial_gold", "name": "Imperial Gold & Obsidian", "badge": "Signature 24K",
        "bg_primary": "#0A0C10", "bg_secondary": "#121620", "surface": "#171C28",
        "accent": "#D4AF37", "accent_light": "#F5D77F", "accent_secondary": "#B8860B",
        "text_primary": "#F8F5EE", "text_muted": "#A39E93", "swatch": "#D4AF37",
    },
    {
        "id": "emerald_vault", "name": "Royal Emerald Vault", "badge": "Heritage Green",
        "bg_primary": "#061510", "bg_secondary": "#0C241C", "surface": "#113026",
        "accent": "#10B981", "accent_light": "#6EE7B7", "accent_secondary": "#D4AF37",
        "text_primary": "#ECFDF5", "text_muted": "#94B8A8", "swatch": "#10B981",
    },
    {
        "id": "ruby_velvet", "name": "Maharaja Ruby Velvet", "badge": "Regal Crimson",
        "bg_primary": "#18070D", "bg_secondary": "#260D16", "surface": "#33121E",
        "accent": "#F43F5E", "accent_light": "#FDA4AF", "accent_secondary": "#EAB308",
        "text_primary": "#FFF1F2", "text_muted": "#C49BA3", "swatch": "#F43F5E",
    },
    {
        "id": "sapphire_crown", "name": "Midnight Sapphire Crown", "badge": "Celestial Blue",
        "bg_primary": "#071022", "bg_secondary": "#0E1B36", "surface": "#15264A",
        "accent": "#3B82F6", "accent_light": "#93C5FD", "accent_secondary": "#FBBF24",
        "text_primary": "#EFF6FF", "text_muted": "#94A8C7", "swatch": "#3B82F6",
    },
    {
        "id": "amethyst_sovereign", "name": "Amethyst Sovereign", "badge": "Royal Violet",
        "bg_primary": "#120920", "bg_secondary": "#1D1033", "surface": "#271745",
        "accent": "#A855F7", "accent_light": "#D8B4FE", "accent_secondary": "#F59E0B",
        "text_primary": "#FAF5FF", "text_muted": "#B3A0CC", "swatch": "#A855F7",
    },
    {
        "id": "champagne_pearl", "name": "Champagne Ivory Pearl", "badge": "Couture Light",
        "bg_primary": "#F9F6F0", "bg_secondary": "#F1ECE1", "surface": "#FFFFFF",
        "accent": "#9A6F18", "accent_light": "#C99A36", "accent_secondary": "#78530D",
        "text_primary": "#1C1917", "text_muted": "#6B6358", "swatch": "#E6CFA3",
    },
    {
        "id": "rose_gold_couture", "name": "Rose Gold Couture", "badge": "Blush Metallic",
        "bg_primary": "#180E13", "bg_secondary": "#24161D", "surface": "#301E27",
        "accent": "#E88D80", "accent_light": "#F7C4BC", "accent_secondary": "#F3C677",
        "text_primary": "#FFF5F5", "text_muted": "#C2A1A6", "swatch": "#E88D80",
    },
    {
        "id": "saigon_jade", "name": "Saigon Jade & Amber", "badge": "Oriental Teal",
        "bg_primary": "#06171A", "bg_secondary": "#0C252A", "surface": "#12333A",
        "accent": "#14B8A6", "accent_light": "#5EEAD4", "accent_secondary": "#F59E0B",
        "text_primary": "#F0FDFA", "text_muted": "#8EBAB5", "swatch": "#14B8A6",
    },
    {
        "id": "platinum_titanium", "name": "Platinum Horology", "badge": "Swiss Slate",
        "bg_primary": "#0C1117", "bg_secondary": "#151D26", "surface": "#1E2936",
        "accent": "#38BDF8", "accent_light": "#BAE6FD", "accent_secondary": "#94A3B8",
        "text_primary": "#F1F5F9", "text_muted": "#94A3B8", "swatch": "#38BDF8",
    },
    {
        "id": "saffron_palace", "name": "Saffron Sunset Palace", "badge": "Marigold Gold",
        "bg_primary": "#180E06", "bg_secondary": "#26170B", "surface": "#362110",
        "accent": "#F97316", "accent_light": "#FDBA74", "accent_secondary": "#FACC15",
        "text_primary": "#FFF7ED", "text_muted": "#C7A68B", "swatch": "#F97316",
    },
]


# --------------------------------------------------------------------------
#  COLOUR HELPERS
# --------------------------------------------------------------------------
def _rgb(color: str):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb) -> str:
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def mix(c1: str, c2: str, t: float) -> str:
    """Blend two hex colours (t=0 -> c1, t=1 -> c2)."""
    a, b = _rgb(c1), _rgb(c2)
    return _hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def luminance(color: str) -> float:
    r, g, b = (c / 255.0 for c in _rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def readable_on(bg: str) -> str:
    return "#0B0B0B" if luminance(bg) > 0.55 else "#FFFFFF"


def tint(theme: dict, base: str, amount: float) -> str:
    """Accent-tinted surface used for banners."""
    return mix(base, theme["accent"], amount)


# --------------------------------------------------------------------------
#  NUMBER FORMATTING
# --------------------------------------------------------------------------
def group_indian(n: float) -> str:
    """Indian digit grouping: 1,23,456.78"""
    neg = n < 0
    s = "{:.2f}".format(abs(float(n)))
    whole, frac = s.split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    return ("-" if neg else "") + whole + "." + frac


def fmt_inr(v: float, decimals: int = 2) -> str:
    sign = "-" if v < 0 else ""
    body = group_indian(abs(float(v)))
    if decimals == 0:
        body = body.split(".")[0]
    return f"{sign}₹{body}"


def fmt_vnd(v: float, decimals: int = 0) -> str:
    sign = "-" if v < 0 else ""
    body = "{:,.{d}f}".format(abs(float(v)), d=decimals)
    return f"{sign}₫{body}"


# --------------------------------------------------------------------------
#  CALCULATION ENGINE
# --------------------------------------------------------------------------
def calculate(vn_per_chi: float, in_per_gram: float, fx: float) -> dict:
    """
    vn_per_chi   : Vietnam 9999 gold price for 1 Chỉ (3.75 g) in VND
    in_per_gram  : India gold price for 1 gram in INR
    fx           : 1 INR = fx VND
    """
    fx = fx if fx > 0 else DEFAULT_FX_INR_TO_VND
    vn_per_gram = vn_per_chi / GRAMS_PER_CHI
    in_per_gram_vnd = in_per_gram * fx

    units = []
    for key, label, grams in (
        ("chi", "CHỈ", GRAMS_PER_CHI),
        ("gram", "GRAM", GRAMS_PER_GRAM),
        ("pavan", "PAVAN", GRAMS_PER_PAVAN),
    ):
        vn_vnd = vn_per_gram * grams
        vn_inr = vn_vnd / fx
        in_inr = in_per_gram * grams
        in_vnd = in_inr * fx
        diff_vnd = vn_vnd - in_vnd          # >0 -> India cheaper
        diff_inr = diff_vnd / fx
        pct = (diff_vnd / in_vnd * 100.0) if in_vnd else 0.0
        if abs(pct) < 0.01:
            cheaper = "equal"
        else:
            cheaper = "india" if diff_vnd > 0 else "vietnam"
        units.append({
            "key": key, "label": label, "grams": grams,
            "vn_vnd": vn_vnd, "vn_inr": vn_inr,
            "in_inr": in_inr, "in_vnd": in_vnd,
            "diff_vnd": diff_vnd, "diff_inr": diff_inr,
            "pct": pct, "cheaper": cheaper,
        })

    return {
        "vn_per_chi": vn_per_chi,
        "in_per_gram": in_per_gram,
        "fx": fx,
        "vn_per_gram_vnd": vn_per_gram,
        "vn_per_gram_inr": vn_per_gram / fx,
        "in_per_gram_vnd": in_per_gram_vnd,
        "units": units,
        "stamp": datetime.now().strftime("%d %b %Y · %H:%M"),
    }


def summarise(report: dict) -> dict:
    """Headline: which country is cheaper on 1 Pavan (the reference bar)."""
    pavan = next(u for u in report["units"] if u["key"] == "pavan")
    if pavan["cheaper"] == "equal":
        return {
            "head": "BOTH MARKETS ARE AT PAR",
            "sub": "Vietnam and India are quoting the same value in VND.",
            "cheaper": "equal", "pct": 0.0, "diff_vnd": 0.0, "diff_inr": 0.0,
        }
    win = "INDIA" if pavan["cheaper"] == "india" else "VIETNAM"
    lose = "Vietnam" if win == "INDIA" else "India"
    return {
        "head": f"{win} IS CHEAPER  ·  {abs(pavan['pct']):.2f}%",
        "sub": (f"Buying 1 Pavan (8 g) saves you "
                f"{fmt_vnd(abs(pavan['diff_vnd']))} (≈ {fmt_inr(abs(pavan['diff_inr']))}) "
                f"versus {lose}."),
        "cheaper": pavan["cheaper"],
        "pct": pavan["pct"],
        "diff_vnd": pavan["diff_vnd"],
        "diff_inr": pavan["diff_inr"],
    }


# --------------------------------------------------------------------------
#  SHARE / REPORT TEXT
# --------------------------------------------------------------------------
def build_share_text(report: dict) -> str:
    s = summarise(report)
    lines = [
        "🦁 LEO · Vietnam ⇄ India Gold Comparison",
        "────────────────────────────",
        f"Vietnam : {fmt_vnd(report['vn_per_chi'])} per Chỉ (3.75 g)",
        f"India   : {fmt_inr(report['in_per_gram'])} per Gram (1.00 g)",
        f"FX      : 1 INR = {report['fx']:.2f} VND",
        "────────────────────────────",
    ]
    for u in report["units"]:
        tag = {"india": "🇮🇳 India cheaper",
               "vietnam": "🇻🇳 Vietnam cheaper",
               "equal": "➖ At par"}[u["cheaper"]]
        lines.append(f"• {u['label']} ({u['grams']:.2f} g)")
        lines.append(f"    VN  {fmt_vnd(u['vn_vnd'])}  ≈ {fmt_inr(u['vn_inr'])}")
        lines.append(f"    IND {fmt_inr(u['in_inr'])}  ≈ {fmt_vnd(u['in_vnd'])}")
        lines.append(f"    → {tag} by {abs(u['pct']):.2f}%")
    lines += ["────────────────────────────", s["head"], APP_CREDIT,
              f"Generated {report['stamp']}"]
    return "\n".join(lines)


# --------------------------------------------------------------------------
#  BACKGROUND MUSIC  (generated with the standard library, no downloads)
# --------------------------------------------------------------------------
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
TRACK_FILE = os.path.join(AUDIO_DIR, "leo_lounge.wav")
SAMPLE_RATE = 22050
DURATION = 24.0


def _build_music(path: str = TRACK_FILE) -> str:
    """Synthesise a warm, slow lounge pad (24 s, seamless loop)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path) and os.path.getsize(path) > 100_000:
        return path

    sr = SAMPLE_RATE
    total = int(sr * DURATION)
    buf = array.array("h", bytes(2 * total))

    # Soft, warm chord progression (A minor 9 lounge feel)
    chords = [
        (220.00, 261.63, 329.63, 415.30),   # Am9
        (174.61, 220.00, 261.63, 329.63),   # Fmaj7
        (196.00, 246.94, 293.66, 369.99),   # G(add9)
        (164.81, 207.65, 246.94, 329.63),   # E7sus
    ]
    seg = DURATION / len(chords)
    two_pi = 2.0 * math.pi

    for i in range(total):
        t = i / sr
        idx = min(int(t / seg), len(chords) - 1)
        local = (t - idx * seg) / seg

        # gentle cross-fade between neighbouring chords
        fade = min(1.0, min(local, 1 - local) * 6.0)
        nxt = (idx + 1) % len(chords)
        nlocal = local

        val = 0.0
        for c_i, chord in enumerate((chords[idx], chords[nxt])):
            w = fade if c_i == 0 else (1.0 - fade)
            if w <= 0:
                continue
            for k, f in enumerate(chord):
                detune = 1.0 + 0.0016 * math.sin(two_pi * 0.11 * t + k)
                amp = 0.075 / (1 + 0.45 * k)
                val += w * amp * math.sin(two_pi * f * detune * t + k * 0.7)

        # shimmering bell every 3 seconds
        beat = t % 3.0
        if beat < 1.6:
            env = math.exp(-beat * 3.2)
            bell_f = 880.0 if int(t / 3.0) % 2 == 0 else 1046.5
            val += 0.055 * env * math.sin(two_pi * bell_f * t)

        # slow breathing tremolo + soft global fade so the loop is seamless
        val *= 0.55 + 0.45 * math.sin(two_pi * 0.06 * t)
        edge = min(1.0, t / 1.2, (DURATION - t) / 1.2)
        val *= max(0.0, edge) * 0.9

        buf[i] = int(max(-1.0, min(1.0, val)) * 30000)

    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(buf.tobytes())
    return path


class MusicPlayer:
    """Best-effort background music with looping, on Windows / macOS / Linux."""

    def __init__(self):
        self.path = None
        self.playing = False
        self._proc = None
        self._error = None
        self.system = platform.system()

    def _ensure_file(self):
        if self.path and os.path.exists(self.path):
            return self.path
        try:
            self.path = _build_music()
        except Exception as exc:                      # pragma: no cover
            self._error = f"Could not prepare music: {exc}"
            self.path = None
        return self.path

    # -- platform back-ends -------------------------------------------------
    def _linux_candidates(self):
        """Ordered list of (exe, args) that can play a WAV loop on Linux."""
        table = (
            ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet", "-loop", "0"]),
            ("mpv", ["--no-video", "--loop=inf", "--really-quiet"]),
            ("mpv", ["--no-video", "--loop=inf", "--really-quiet", "--ao=null"]),
            ("cvlc", ["--loop", "--quiet", "--intf", "dummy"]),
            ("paplay", []),
            ("aplay", ["-q"]),
            ("play", ["-q"]),
            ("gst-play-1.0", []),
        )
        out = []
        for cmd, args in table:
            exe = shutil.which(cmd)
            if exe:
                out.append([exe] + args + ["{file}"])
        return out

    def _linux_cmd(self):
        c = self._linux_candidates()
        return c[0] if c else None

    def start(self) -> bool:
        if self.playing:
            return True
        if not self._ensure_file():
            return False
        try:
            if self.system == "Windows":
                import winsound
                winsound.PlaySound(self.path,
                                   winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            elif self.system == "Darwin":
                self._proc = subprocess.Popen(["afplay", self.path],
                                              stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL)
            else:
                cands = self._linux_candidates()
                if not cands:
                    self._error = ("No audio player found. Install one with:\n"
                                   "    sudo apt install ffmpeg      (or mpv / pulseaudio-utils)")
                    return False
                for tmpl in cands:
                    cmd = [c.format(file=self.path) for c in tmpl]
                    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL)
                    time.sleep(0.45)
                    if proc.poll() is None:      # still running -> works
                        self._proc = proc
                        break
                    self._proc = None
                else:
                    self._error = ("Could not open an audio device. "
                                   "Music needs a sound card or PulseAudio.")
                    return False
            self.playing = True
            self._error = None
            return True
        except Exception as exc:                       # pragma: no cover
            self._error = f"Audio unavailable: {exc}"
            return False

    def stop(self):
        self.playing = False
        try:
            if self.system == "Windows":
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        self._proc = None

    def toggle(self) -> bool:
        if self.playing:
            self.stop()
            return False
        return self.start()

    def poll(self):
        """Restart one-shot players (paplay/aplay) so the loop never stops."""
        if self.playing and self._proc and self._proc.poll() is not None:
            self._proc = None
            self.stop()
            self.start()


# --------------------------------------------------------------------------
#  EXPORTERS
# --------------------------------------------------------------------------
def _exports_dir() -> str:
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
    os.makedirs(d, exist_ok=True)
    return d


def _dated(suffix: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return os.path.join(_exports_dir(), f"Leo_Gold_{stamp}.{suffix}")


def _register_pdf_fonts():
    """Use DejaVu (has ₹ and ₫) when available, else fall back safely."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
        ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf",
         "C:/Windows/Fonts/georgia.ttf"),
        ("/System/Library/Fonts/Supplemental/Arial.ttf",
         "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/System/Library/Fonts/Supplemental/Georgia.ttf"),
        ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf", "/Library/Fonts/Georgia.ttf"),
    ]
    for reg, bold, serif in candidates:
        if os.path.exists(reg) and os.path.exists(bold):
            try:
                pdfmetrics.registerFont(TTFont("LeoBody", reg))
                pdfmetrics.registerFont(TTFont("LeoBold", bold))
                if os.path.exists(serif):
                    pdfmetrics.registerFont(TTFont("LeoSerif", serif))
                else:
                    pdfmetrics.registerFont(TTFont("LeoSerif", reg))
                return True, ("LeoSerif", "LeoBold", "LeoBody")
            except Exception:
                continue
    return False, ("Times-Bold", "Helvetica-Bold", "Helvetica")


def export_pdf(report: dict, theme: dict, path: str | None = None) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas as pdfcanvas

    unicode_ok, (F_TITLE, F_BOLD, F_BODY) = _register_pdf_fonts()
    accent = colors.HexColor(theme["accent"])
    accent_soft = colors.HexColor(theme["accent_light"])
    dark = colors.HexColor("#12151C")
    muted = colors.HexColor("#6B7280")
    line = colors.HexColor("#D8D3C7")

    if not unicode_ok:
        # Helvetica cannot render ₹ / ₫ -> use ISO codes instead
        globals()["fmt_inr_orig"] = fmt_inr
        globals()["fmt_vnd_orig"] = fmt_vnd

    def money_inr(v):
        return fmt_inr(v) if unicode_ok else "INR " + "{:,.2f}".format(v)

    def money_vnd(v):
        return fmt_vnd(v) if unicode_ok else "VND " + "{:,.0f}".format(v)

    path = path or _dated("pdf")
    c = pdfcanvas.Canvas(path, pagesize=A4)
    W, H = A4

    # ---- header band
    c.setFillColor(dark)
    c.rect(0, H - 42 * mm, W, 42 * mm, stroke=0, fill=1)
    c.setFillColor(accent)
    c.rect(0, H - 43.5 * mm, W, 1.5 * mm, stroke=0, fill=1)

    c.setFillColor(accent)
    c.setFont(F_TITLE, 30)
    c.drawString(16 * mm, H - 20 * mm, "LEO")
    c.setFont(F_BODY, 10.5)
    c.setFillColor(colors.HexColor("#E9E4D8"))
    c.drawString(16 * mm, H - 27 * mm, "Vietnam  -  India   |   Gold Rate Comparison Report")
    c.setFillColor(accent_soft)
    c.setFont(F_BODY, 9)
    c.drawString(16 * mm, H - 33 * mm, APP_CREDIT)
    c.setFillColor(colors.HexColor("#B9B4A8"))
    c.drawRightString(W - 16 * mm, H - 27 * mm, f"Theme: {theme['name']}")
    c.drawRightString(W - 16 * mm, H - 33 * mm, report["stamp"])

    y = H - 54 * mm

    # ---- inputs
    c.setFillColor(dark)
    c.setFont(F_BOLD, 9)
    c.drawString(16 * mm, y, "MARKET INPUTS")
    c.setStrokeColor(accent)
    c.setLineWidth(0.8)
    c.line(16 * mm, y - 2 * mm, W - 16 * mm, y - 2 * mm)
    y -= 9 * mm

    rows = [
        ("Vietnam gold price (per Chi / 3.75 g)", money_vnd(report["vn_per_chi"])),
        ("India gold price (per Gram / 1.00 g)", money_inr(report["in_per_gram"])),
        ("Exchange rate", f"1 INR = {report['fx']:,.2f} VND"),
    ]
    for label, value in rows:
        c.setFont(F_BODY, 10)
        c.setFillColor(muted)
        c.drawString(18 * mm, y, label)
        c.setFont(F_BOLD, 11)
        c.setFillColor(dark)
        c.drawRightString(W - 18 * mm, y, value)
        y -= 7.6 * mm

    # ---- comparison table
    y -= 4 * mm
    c.setFillColor(dark)
    c.setFont(F_BOLD, 9)
    c.drawString(16 * mm, y, "SIDE-BY-SIDE COMPARISON")
    c.setStrokeColor(accent)
    c.line(16 * mm, y - 2 * mm, W - 16 * mm, y - 2 * mm)
    y -= 8 * mm

    col_x = [18 * mm, 62 * mm, 108 * mm, 152 * mm]
    heads = ["UNIT", "VIETNAM", "INDIA", "VERDICT"]
    c.setFont(F_BOLD, 9)
    c.setFillColor(muted)
    for x, h in zip(col_x, heads):
        c.drawString(x, y, h)
    y -= 5 * mm

    for u in report["units"]:
        c.setStrokeColor(line)
        c.setLineWidth(0.5)
        c.line(16 * mm, y + 2.5 * mm, W - 16 * mm, y + 2.5 * mm)
        c.setFont(F_BOLD, 10.5)
        c.setFillColor(dark)
        c.drawString(col_x[0], y - 2 * mm, u["label"])
        c.setFont(F_BODY, 8)
        c.setFillColor(muted)
        c.drawString(col_x[0], y - 6 * mm, f"{u['grams']:.2f} grams")

        c.setFont(F_BODY, 9.5)
        c.setFillColor(dark)
        c.drawString(col_x[1], y - 2 * mm, money_vnd(u["vn_vnd"]))
        c.setFont(F_BODY, 8)
        c.setFillColor(muted)
        c.drawString(col_x[1], y - 6 * mm, "= " + money_inr(u["vn_inr"]))

        c.setFont(F_BODY, 9.5)
        c.setFillColor(dark)
        c.drawString(col_x[2], y - 2 * mm, money_inr(u["in_inr"]))
        c.setFont(F_BODY, 8)
        c.setFillColor(muted)
        c.drawString(col_x[2], y - 6 * mm, "= " + money_vnd(u["in_vnd"]))

        verdict = {"india": "INDIA cheaper", "vietnam": "VIETNAM cheaper",
                   "equal": "At par"}[u["cheaper"]]
        c.setFont(F_BOLD, 9.5)
        c.setFillColor(accent if u["cheaper"] != "equal" else muted)
        c.drawString(col_x[3], y - 2 * mm, verdict)
        c.setFont(F_BODY, 8)
        c.setFillColor(muted)
        c.drawString(col_x[3], y - 6 * mm, f"by {abs(u['pct']):.2f}%")
        y -= 13 * mm

    # ---- headline box
    y -= 2 * mm
    s = summarise(report)
    box_h = 26 * mm
    c.setFillColor(colors.HexColor("#F7F4EC"))
    c.setStrokeColor(accent)
    c.setLineWidth(1.1)
    c.roundRect(16 * mm, y - box_h, W - 32 * mm, box_h, 3 * mm, stroke=1, fill=1)
    c.setFillColor(accent)
    c.setFont(F_BOLD, 15)
    c.drawString(22 * mm, y - 10 * mm, s["head"])
    c.setFillColor(dark)
    c.setFont(F_BODY, 9.5)
    c.drawString(22 * mm, y - 17 * mm, s["sub"])
    c.setFillColor(muted)
    c.setFont(F_BODY, 8)
    c.drawString(22 * mm, y - 22 * mm,
                 "Reference set: 1 Chi = 3.75 g  |  1 Gram = 1.00 g  |  1 Pavan = 8.00 g  |  1 Luong = 37.5 g")

    # ---- footer
    c.setStrokeColor(line)
    c.setLineWidth(0.5)
    c.line(16 * mm, 20 * mm, W - 16 * mm, 20 * mm)
    c.setFillColor(muted)
    c.setFont(F_BODY, 8)
    c.drawString(16 * mm, 15 * mm,
                 "Rates are user-supplied or sample benchmarks. Verify with your jeweller before trading.")
    c.drawRightString(W - 16 * mm, 15 * mm, f"LEO v{APP_VERSION}  ·  {APP_CREDIT}")

    c.showPage()
    c.save()
    return path


def export_excel(report: dict, path: str | None = None) -> str:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    path = path or _dated("xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "Comparison"

    gold = "D4AF37"
    dark = "12151C"
    thin = Side(style="thin", color="DDD8CC")

    ws["A1"] = "LEO  ·  Vietnam ⇄ India Gold Rate Comparison"
    ws["A1"].font = Font(size=16, bold=True, color=dark)
    ws["A2"] = APP_CREDIT
    ws["A2"].font = Font(size=10, italic=True, color="8A6D1F")
    ws["A3"] = f"Generated {report['stamp']}"
    ws["A3"].font = Font(size=9, color="777777")

    ws["A5"] = "Inputs"
    ws["A5"].font = Font(bold=True, size=12, color=dark)
    inputs = [
        ("Vietnam price per Chi (VND)", report["vn_per_chi"]),
        ("India price per Gram (INR)", report["in_per_gram"]),
        ("FX rate (1 INR = VND)", report["fx"]),
    ]
    r = 6
    for label, val in inputs:
        ws.cell(row=r, column=1, value=label).font = Font(bold=True, size=10)
        c = ws.cell(row=r, column=2, value=val)
        c.font = Font(size=10)
        c.number_format = '#,##0" ₫"' if "VND" in label else ('#,##0.00" ₹"' if "INR" in label else "0.0000")
        r += 1

    r += 1
    headers = ["Unit", "Grams", "Vietnam (VND)", "Vietnam (INR)",
               "India (INR)", "India (VND)", "Cheaper", "Difference %"]
    ws.cell(row=r, column=1, value="Comparison").font = Font(bold=True, size=12, color=dark)
    r += 1
    head_row = r
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=r, column=i, value=h)
        c.font = Font(bold=True, color="FFFFFF", size=10)
        c.fill = PatternFill("solid", fgColor=dark)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    r += 1
    for u in report["units"]:
        row = [
            u["label"], u["grams"], round(u["vn_vnd"]), round(u["vn_inr"], 2),
            round(u["in_inr"], 2), round(u["in_vnd"]), u["cheaper"].upper(),
            round(abs(u["pct"]), 2),
        ]
        for i, v in enumerate(row, start=1):
            c = ws.cell(row=r, column=i, value=v)
            c.border = Border(bottom=thin)
            if i in (3, 6):
                c.number_format = '#,##0" ₫"'
            elif i in (4, 5):
                c.number_format = '#,##0.00" ₹"'
            elif i == 8:
                c.number_format = '0.00"%"'
            if i == 7:
                c.font = Font(bold=True, color="0F7A46" if v == "INDIA" else "9A5010")
        r += 1

    r += 2
    ws.cell(row=r, column=1, value="Headline").font = Font(bold=True, size=12, color=dark)
    s = summarise(report)
    ws.cell(row=r + 1, column=1, value=s["head"]).font = Font(bold=True, size=11, color="8A6D1F")
    ws.cell(row=r + 2, column=1, value=s["sub"]).font = Font(size=10)

    widths = [16, 9, 20, 18, 16, 20, 12, 14]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=head_row + 1, column=1)

    # --- second sheet: live formulas so the user can tweak prices
    ws2 = wb.create_sheet("Calculator")
    ws2["A1"] = "LEO · Interactive Calculator (edit the green cells)"
    ws2["A1"].font = Font(size=14, bold=True, color=dark)
    grid = [
        ("Vietnam price per Chi (VND)", report["vn_per_chi"]),
        ("India price per Gram (INR)", report["in_per_gram"]),
        ("FX rate (1 INR = VND)", report["fx"]),
    ]
    rr = 3
    for label, val in grid:
        ws2.cell(row=rr, column=1, value=label).font = Font(bold=True, size=10)
        c = ws2.cell(row=rr, column=2, value=val)
        c.fill = PatternFill("solid", fgColor="EAF6EC")
        c.font = Font(bold=True, size=10)
        rr += 1

    rr += 1
    calc_headers = ["Unit", "Grams", "Vietnam (VND)", "India (VND)", "Cheaper", "Difference %"]
    for i, h in enumerate(calc_headers, start=1):
        c = ws2.cell(row=rr, column=i, value=h)
        c.font = Font(bold=True, color="FFFFFF", size=10)
        c.fill = PatternFill("solid", fgColor=dark)
        c.alignment = Alignment(horizontal="center")
    start = rr + 1
    for k, (label, grams) in enumerate(
            [("CHỈ", GRAMS_PER_CHI), ("GRAM", GRAMS_PER_GRAM), ("PAVAN", GRAMS_PER_PAVAN)]):
        row = start + k
        ws2.cell(row=row, column=1, value=label).font = Font(bold=True)
        ws2.cell(row=row, column=2, value=grams).number_format = "0.00"
        ws2.cell(row=row, column=3,
                 value=f"=$B$3/3.75*B{row}").number_format = '#,##0" ₫"'
        ws2.cell(row=row, column=4,
                 value=f"=$B$4*$B$5*B{row}").number_format = '#,##0" ₫"'
        ws2.cell(row=row, column=5,
                 value=f'=IF(C{row}>D{row},"INDIA","VIETNAM")').font = Font(bold=True)
        ws2.cell(row=row, column=6,
                 value=f"=ABS((C{row}-D{row})/D{row}*100)").number_format = '0.00"%"'
    for col, w in zip("ABCDEF", [16, 9, 20, 20, 12, 14]):
        ws2.column_dimensions[col].width = w

    ws2["A" + str(start + 5)] = "1 Chỉ = 3.75 g   ·   1 Gram = 1.00 g   ·   1 Pavan = 8.00 g   ·   1 Lượng = 37.5 g"
    ws2["A" + str(start + 5)].font = Font(size=9, italic=True, color="777777")
    ws2["A" + str(start + 6)] = APP_CREDIT
    ws2["A" + str(start + 6)].font = Font(size=9, color="8A6D1F")

    wb.save(path)
    return path


# --------------------------------------------------------------------------
#  UI PRIMITIVES
# --------------------------------------------------------------------------
class LeoButton(tk.Frame):
    """Flat, rounded-feel luxury button with hover states."""

    def __init__(self, master, text, command, kind="primary", app=None, width=None):
        super().__init__(master, bd=0, highlightthickness=0)
        self.app = app
        self.command = command
        self.kind = kind
        self._enabled = True
        self.label = tk.Label(self, text=text, bd=0, padx=18, pady=11,
                              cursor="hand2", anchor="center")
        self.label.pack(fill="both", expand=True)
        if width:
            self.label.configure(width=width)
        for w in (self, self.label):
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)
        if app:
            app.painters.append(self.restyle)

    def _click(self, _e=None):
        if self._enabled and self.command:
            self.command()

    def set_enabled(self, on: bool):
        self._enabled = on
        self.configure(cursor="hand2" if on else "arrow")
        self.restyle(self.app.theme if self.app else None)

    def _enter(self, _e=None):
        if not self._enabled or not self.app:
            return
        t = self.app.theme
        if self.kind == "primary":
            self.label.configure(bg=t["accent_light"], fg=readable_on(t["accent_light"]))
        elif self.kind == "ghost":
            self.label.configure(bg=mix(t["surface"], t["accent"], 0.16), fg=t["accent_light"])
        self.configure(highlightbackground=t["accent"])

    def _leave(self, _e=None):
        self.restyle(self.app.theme if self.app else None)

    def restyle(self, t):
        if not t:
            return
        f = self.app.font
        self.label.configure(font=f("button", 11, "bold"))
        if not self._enabled:
            self.label.configure(bg=mix(t["surface"], t["bg_primary"], 0.4),
                                 fg=t["text_muted"])
            self.configure(highlightbackground=mix(t["surface"], t["bg_primary"], 0.2))
            return
        if self.kind == "primary":
            self.label.configure(bg=t["accent"], fg=readable_on(t["accent"]))
            self.configure(highlightbackground=t["accent"])
        elif self.kind == "ghost":
            self.label.configure(bg=t["surface"], fg=t["accent_light"])
            self.configure(highlightbackground=mix(t["surface"], t["accent"], 0.45))
        else:  # quiet
            self.label.configure(bg="%s" % t["bg_secondary"], fg=t["text_muted"])
            self.configure(highlightbackground=mix(t["bg_secondary"], t["text_muted"], 0.25))
        self.configure(highlightthickness=1, bd=0)


class Card(tk.Frame):
    """Surface panel with a hairline border and a thin accent rule on top."""

    def __init__(self, master, app, accent_top=True):
        super().__init__(master, bd=0, highlightthickness=1)
        self.app = app
        self.accent_top = accent_top
        if app:
            app.painters.append(self.restyle)

    def restyle(self, t):
        self.configure(bg=t["surface"],
                       highlightbackground=mix(t["surface"], t["text_primary"], 0.14))


class UnitCard(tk.Frame):
    """One comparison card: Chi / Gram / Pavan."""

    def __init__(self, master, app, unit):
        super().__init__(master, bg=app.theme["surface"], bd=0, highlightthickness=1)
        self.app = app
        self.unit = unit
        self.f = app.font

        # header row
        head = tk.Frame(self, bd=0)
        head.pack(fill="x", padx=16, pady=(13, 0))
        self.title = tk.Label(head, text=f"{unit['label']}  ·  {unit['grams']:.2f} g",
                              anchor="w", bd=0)
        self.title.pack(side="left")
        self.badge = tk.Label(head, text="", bd=0, padx=10, pady=3, anchor="e")
        self.badge.pack(side="right")

        # Vietnam row
        self.vn_name, self.vn_main, self.vn_sub = self._row("🇻🇳  VIETNAM")
        # India row
        self.in_name, self.in_main, self.in_sub = self._row("🇮🇳  INDIA")

        # bar canvas
        self.bar = tk.Canvas(self, height=34, bd=0, highlightthickness=0)
        self.bar.pack(fill="x", padx=16, pady=(4, 0))
        self.bar.bind("<Configure>", lambda e: self._draw_bars())

        # difference line
        self.diff = tk.Label(self, text="", anchor="w", bd=0)
        self.diff.pack(fill="x", padx=16, pady=(2, 12))

        self.values = {"vn": 0.0, "in": 0.0}
        app.painters.append(self.restyle)

    def _row(self, label):
        row = tk.Frame(self, bd=0)
        row.pack(fill="x", padx=16, pady=(7, 0))
        name = tk.Label(row, text=label, anchor="w", width=13, bd=0)
        name.pack(side="left")
        main = tk.Label(row, text="—", anchor="e", bd=0)
        main.pack(side="right")
        sub = tk.Label(row, text="", anchor="e", bd=0)
        sub.pack(side="right", padx=(0, 12))
        return name, main, sub

    def set_values(self, unit: dict):
        self.unit = unit
        t = self.app.theme
        self.values = {"vn": unit["vn_vnd"], "in": unit["in_vnd"]}
        self.vn_main.configure(text=fmt_vnd(unit["vn_vnd"]))
        self.vn_sub.configure(text="≈ " + fmt_inr(unit["vn_inr"]))
        self.in_main.configure(text=fmt_inr(unit["in_inr"]))
        self.in_sub.configure(text="≈ " + fmt_vnd(unit["in_vnd"]))

        if unit["cheaper"] == "india":
            txt = f"India cheaper by {abs(unit['pct']):.2f}%   ·   save {fmt_vnd(abs(unit['diff_vnd']))}"
            self.badge.configure(text="🇮🇳  INDIA")
        elif unit["cheaper"] == "vietnam":
            txt = f"Vietnam cheaper by {abs(unit['pct']):.2f}%   ·   save {fmt_vnd(abs(unit['diff_vnd']))}"
            self.badge.configure(text="🇻🇳  VIETNAM")
        else:
            txt = "Both markets at par"
            self.badge.configure(text="AT PAR")
        self.diff.configure(text=txt)
        self._draw_bars()

    def _draw_bars(self):
        c = self.bar
        c.delete("all")
        t = self.app.theme
        w = max(c.winfo_width(), 60)
        h = 34
        c.configure(bg=t["surface"])
        mx = max(self.values["vn"], self.values["in"], 1)
        cheaper = self.unit.get("cheaper", "equal")
        for i, key in enumerate(("vn", "in")):
            won = (cheaper == "vietnam" and key == "vn") or (cheaper == "india" and key == "in")
            color = t["accent"] if won else mix(t["surface"], t["text_primary"], 0.30)
            y = 4 + i * 15
            bw = max(3, (w - 6) * self.values[key] / mx)
            c.create_rectangle(0, y, w, y + 9, fill=mix(t["surface"], t["text_primary"], 0.07),
                               outline="")
            c.create_rectangle(0, y, bw, y + 9, fill=color, outline="")

    def restyle(self, t):
        f = self.f
        self.configure(bg=t["surface"], highlightbackground=mix(t["surface"], t["text_primary"], 0.14))
        self.title.configure(bg=t["surface"], fg=t["text_primary"], font=f("serif", 15, "bold"))
        self.badge.configure(bg=mix(t["surface"], t["accent"], 0.20), fg=t["accent_light"],
                             font=f("sans", 9, "bold"))
        for lbl in (self.vn_name, self.in_name):
            lbl.configure(bg=t["surface"], fg=t["text_muted"], font=f("sans", 9, "bold"))
        for lbl in (self.vn_main, self.in_main):
            lbl.configure(bg=t["surface"], fg=t["text_primary"], font=f("mono", 14, "bold"))
        for lbl in (self.vn_sub, self.in_sub):
            lbl.configure(bg=t["surface"], fg=t["text_muted"], font=f("mono", 9))
        for w in self.winfo_children():
            try:
                w.configure(bg=t["surface"])
            except tk.TclError:
                pass
        self.diff.configure(bg=t["surface"],
                            fg=t["accent_light"] if self.unit["cheaper"] != "equal" else t["text_muted"],
                            font=f("sans", 10, "bold"))
        self._draw_bars()


# --------------------------------------------------------------------------
#  MAIN APPLICATION
# --------------------------------------------------------------------------
class LeoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.theme = THEMES[0]
        self.report = None
        self.painters = []
        self.surface_frames = []      # plain frames that should follow the card surface
        self.music = MusicPlayer()
        self._music_tick = None
        self._entry_var = {}

        root.title(f"{APP_NAME} · Vietnam ⇄ India Gold Comparison")
        root.geometry("1280x880")
        root.minsize(1120, 800)
        try:
            root.tk.call("tk", "scaling", 1.15)
        except Exception:
            pass

        self._pick_fonts()
        self._build()
        self.apply_theme(THEMES[0])
        self.load_benchmarks(silent=True)
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._bind_keys()

    # ---------------- fonts ----------------
    def _pick_fonts(self):
        fams = set(tkfont.families(self.root))

        def pick(cands, fallback):
            for c in cands:
                if c in fams:
                    return c
            return fallback

        base = {
            "serif": pick(["Playfair Display", "Georgia", "URW Bookman", "Nimbus Roman",
                           "DejaVu Serif", "Times New Roman"], "DejaVu Serif"),
            "sans": pick(["Segoe UI", "SF Pro Text", "Helvetica Neue", "Inter",
                          "Nimbus Sans", "Liberation Sans", "DejaVu Sans", "Arial"], "DejaVu Sans"),
            "mono": pick(["JetBrains Mono", "Cascadia Mono", "Consolas", "Menlo",
                          "DejaVu Sans Mono", "Courier New"], "DejaVu Sans Mono"),
        }

        def font(role, size, weight="normal"):
            fam = base.get(role, base["sans"])
            try:
                return tkfont.Font(family=fam, size=size, weight=weight)
            except Exception:
                return tkfont.Font(family="DejaVu Sans", size=size, weight=weight)

        self.font = font
        self.base_fonts = base

    # ---------------- layout ----------------
    def _build(self):
        root = self.root

        self.root_frame = tk.Frame(root, bd=0)
        self.root_frame.pack(fill="both", expand=True)

        # ================= HEADER =================
        self.header = tk.Frame(self.root_frame, bd=0, height=104)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.emblem = tk.Canvas(self.header, width=74, height=74, bd=0, highlightthickness=0)
        self.emblem.pack(side="left", padx=(26, 14), pady=15)
        self.painters.append(self._paint_emblem)

        brand = tk.Frame(self.header, bd=0)
        brand.pack(side="left", pady=20)
        self.brand = brand
        self.lbl_leo = tk.Label(brand, text=APP_NAME, anchor="w", bd=0)
        self.lbl_leo.pack(anchor="w")
        self.lbl_tag = tk.Label(brand, text=APP_TAGLINE, anchor="w", bd=0)
        self.lbl_tag.pack(anchor="w")
        self.lbl_credit = tk.Label(brand, text=APP_CREDIT, anchor="w", bd=0)
        self.lbl_credit.pack(anchor="w", pady=(4, 0))

        # right side of header: theme name + music button
        right = tk.Frame(self.header, bd=0)
        right.pack(side="right", padx=26, pady=22)
        self.hdr_right = right
        self.lbl_theme_name = tk.Label(right, text="", anchor="e", bd=0)
        self.lbl_theme_name.pack(anchor="e")
        self.btn_music = LeoButton(right, "♪  Background Music: Off", self.toggle_music,
                                   kind="ghost", app=self)
        self.btn_music.pack(anchor="e", pady=(8, 0))

        # ================= THEME BAR =================
        self.theme_bar = tk.Frame(self.root_frame, bd=0, height=56)
        self.theme_bar.pack(fill="x")
        self.theme_bar.pack_propagate(False)
        self.lbl_themes = tk.Label(self.theme_bar, text="THEME", anchor="w", bd=0)
        self.lbl_themes.pack(side="left", padx=(28, 14))
        self.swatches = []
        sw_box = tk.Frame(self.theme_bar, bd=0)
        sw_box.pack(side="left", pady=12)
        self.sw_box = sw_box
        for th in THEMES:
            cv = tk.Canvas(sw_box, width=26, height=26, bd=0, highlightthickness=2,
                           cursor="hand2")
            cv.pack(side="left", padx=4)
            cv.bind("<Button-1>", lambda e, t=th: self.apply_theme(t))
            self.swatches.append((cv, th))
        self.lbl_badge = tk.Label(self.theme_bar, text="", anchor="e", bd=0)
        self.lbl_badge.pack(side="right", padx=28)

        # ================= BODY =================
        self.body = tk.Frame(self.root_frame, bd=0)
        self.body.pack(fill="both", expand=True, padx=26, pady=(4, 0))

        # ---- left: inputs
        self.left = tk.Frame(self.body, bd=0, width=380)
        self.left.pack(side="left", fill="y", padx=(0, 18))
        self.left.pack_propagate(False)
        self._build_inputs()

        # ---- right: results
        self.right = tk.Frame(self.body, bd=0)
        self.right.pack(side="left", fill="both", expand=True)
        self._build_results()

        # ================= ACTIONS =================
        self.actions = tk.Frame(self.root_frame, bd=0, height=78)
        self.actions.pack(fill="x", padx=26, pady=(10, 0))
        self.actions.pack_propagate(False)
        self._build_actions()

        # ================= STATUS =================
        self.statusbar = tk.Frame(self.root_frame, bd=0, height=34)
        self.statusbar.pack(fill="x")
        self.statusbar.pack_propagate(False)
        self.lbl_status = tk.Label(self.statusbar, text="Ready.", anchor="w", bd=0)
        self.lbl_status.pack(side="left", padx=28)
        self.lbl_stamp = tk.Label(self.statusbar, text="", anchor="e", bd=0)
        self.lbl_stamp.pack(side="right", padx=28)

    # ---------------- inputs panel ----------------
    def _build_inputs(self):
        card = Card(self.left, self, )
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bd=0)
        inner.pack(fill="both", expand=True, padx=20, pady=18)
        self.inputs_inner = inner

        self.lbl_inputs_title = tk.Label(inner, text="MARKET INPUTS", anchor="w", bd=0)
        self.lbl_inputs_title.pack(anchor="w")
        self.lbl_inputs_rule = tk.Frame(inner, height=2, bd=0)
        self.lbl_inputs_rule.pack(fill="x", pady=(6, 14))

        self._field(inner, "vietnam", "VIETNAM  ·  per Chỉ (3.75 g)", "₫",
                    "e.g. 14,100,000")
        self._field(inner, "india", "INDIA  ·  per Gram (1.00 g)", "₹",
                    "e.g. 13,849")
        self._field(inner, "fx", "EXCHANGE RATE  ·  1 INR =", "VND",
                    "e.g. 273.07")

        # quick presets
        preset_box = tk.Frame(inner, bd=0)
        preset_box.pack(fill="x", pady=(12, 0))
        self.surface_frames.append(preset_box)
        self.lbl_preset = tk.Label(preset_box, text="QUICK SETS", anchor="w", bd=0)
        self.lbl_preset.pack(anchor="w", pady=(0, 8))
        row1 = tk.Frame(preset_box, bd=0)
        row1.pack(fill="x")
        self.surface_frames.append(row1)
        self.btn_24k = LeoButton(row1, "India 24K", lambda: self.preset_india("24K"),
                                 kind="quiet", app=self)
        self.btn_24k.pack(side="left")
        self.btn_22k = LeoButton(row1, "India 22K", lambda: self.preset_india("22K"),
                                 kind="quiet", app=self)
        self.btn_22k.pack(side="left", padx=(8, 0))

        row2 = tk.Frame(preset_box, bd=0)
        row2.pack(fill="x", pady=(8, 0))
        self.surface_frames.append(row2)
        self.btn_bench = LeoButton(row2, "Benchmarks", self.load_benchmarks,
                                   kind="quiet", app=self)
        self.btn_bench.pack(side="left")
        self.btn_reset = LeoButton(row2, "Reset", self.reset_inputs,
                                   kind="quiet", app=self)
        self.btn_reset.pack(side="left", padx=(8, 0))

        # primary compare
        self.btn_compare = LeoButton(inner, "COMPARE  GOLD  RATES", self.compare, app=self)
        self.btn_compare.pack(fill="x", pady=(16, 0))

        self.lbl_hint = tk.Label(inner, text="Enter to compare  ·  Ctrl+P to print  ·  Ctrl+S for PDF",
                                 anchor="w", justify="left", bd=0, wraplength=300)
        self.lbl_hint.pack(anchor="w", pady=(10, 0))

        # ---- unit standards footer inside the left card
        self.std_box = tk.Frame(inner, bd=0)
        self.std_box.pack(fill="x", side="bottom", pady=(14, 0))
        self.surface_frames.append(self.std_box)
        self.lbl_std_title = tk.Label(self.std_box, text="WEIGHT STANDARDS", anchor="w", bd=0)
        self.lbl_std_title.pack(anchor="w")
        self.std_rule = tk.Frame(self.std_box, height=1, bd=0)
        self.std_rule.pack(fill="x", pady=(6, 8))
        self.lbl_std = tk.Label(
            self.std_box, anchor="w", justify="left", bd=0, wraplength=300,
            text=("1 Chỉ  = 3.75 g       1 Pavan = 8.00 g\n"
                  "1 Gram = 1.00 g       1 Lượng = 37.50 g"))
        self.lbl_std.pack(anchor="w")

    def _field(self, parent, key, label, suffix, placeholder):
        wrap = tk.Frame(parent, bd=0)
        wrap.pack(fill="x", pady=(0, 14))
        self.surface_frames.append(wrap)

        lbl = tk.Label(wrap, text=label, anchor="w", bd=0)
        lbl.pack(anchor="w", pady=(0, 6))

        box = tk.Frame(wrap, bd=0, highlightthickness=1)
        box.pack(fill="x")

        var = tk.StringVar()
        ent = tk.Entry(box, textvariable=var, bd=0, relief="flat", highlightthickness=0,
                       justify="right", insertwidth=2)
        ent.pack(side="left", fill="x", expand=True, ipady=9, padx=(12, 6))
        ent.bind("<Return>", lambda e: self.compare())

        pre = tk.Label(box, text=suffix, bd=0, width=4, anchor="w")
        pre.pack(side="right", padx=(0, 10))

        self._entry_var[key] = var
        self.painters.append(lambda t, l=lbl, b=box, e=ent, p=pre, k=key: self._style_field(
            t, l, b, e, p))
        return var

    def _style_field(self, t, lbl, box, ent, pre):
        lbl.configure(bg=t["surface"], fg=t["text_muted"], font=self.font("sans", 9, "bold"))
        box.configure(bg=mix(t["surface"], t["bg_primary"], 0.45),
                      highlightbackground=mix(t["surface"], t["text_primary"], 0.16))
        ent.configure(bg=mix(t["surface"], t["bg_primary"], 0.45), fg=t["text_primary"],
                      font=self.font("mono", 14, "bold"), insertbackground=t["accent"],
                      highlightcolor=t["accent"],
                      selectbackground=mix(t["surface"], t["accent"], 0.35),
                      selectforeground=t["text_primary"])
        pre.configure(bg=mix(t["surface"], t["bg_primary"], 0.45), fg=t["accent_light"],
                      font=self.font("sans", 10, "bold"))

    # ---------------- results panel ----------------
    def _build_results(self):
        # headline banner
        self.banner = tk.Frame(self.right, bd=0, highlightthickness=1)
        self.banner.pack(fill="x")
        self.banner_inner = tk.Frame(self.banner, bd=0)
        self.banner_inner.pack(fill="x", padx=20, pady=14)
        self.lbl_head = tk.Label(self.banner_inner, text="—", anchor="w", bd=0)
        self.lbl_head.pack(anchor="w")
        self.lbl_sub = tk.Label(self.banner_inner, text="Enter your prices and press Compare.",
                                anchor="w", justify="left", bd=0)
        self.lbl_sub.pack(anchor="w", pady=(4, 0))

        # unit cards
        self.cards_box = tk.Frame(self.right, bd=0)
        self.cards_box.pack(fill="both", expand=True, pady=(16, 0))
        dummy = calculate(DEFAULT_VN_CHI_VND, DEFAULT_IN_GRAM_INR, DEFAULT_FX_INR_TO_VND)
        self.cards = {}
        for u in dummy["units"]:
            c = UnitCard(self.cards_box, self, u)
            c.pack(fill="x", pady=(0, 12))
            self.cards[u["key"]] = c

        self.painters.append(self._style_results)

    def _style_results(self, t):
        self.banner.configure(bg=mix(t["bg_secondary"], t["accent"], 0.13),
                              highlightbackground=mix(t["bg_secondary"], t["accent"], 0.45))
        self.banner_inner.configure(bg=mix(t["bg_secondary"], t["accent"], 0.13))
        self.lbl_head.configure(bg=mix(t["bg_secondary"], t["accent"], 0.13),
                                fg=t["accent_light"], font=self.font("serif", 20, "bold"))
        self.lbl_sub.configure(bg=mix(t["bg_secondary"], t["accent"], 0.13),
                               fg=t["text_primary"], font=self.font("sans", 10))
        self.cards_box.configure(bg=t["bg_primary"])

    # ---------------- action bar ----------------
    def _build_actions(self):
        bar = tk.Frame(self.actions, bd=0)
        bar.pack(fill="x")
        self.action_bar = bar

        self.btn_pdf = LeoButton(bar, "⎙  PDF Report", self.do_pdf, kind="ghost", app=self)
        self.btn_pdf.pack(side="left")
        self.btn_xls = LeoButton(bar, "▦  Excel", self.do_excel, kind="ghost", app=self)
        self.btn_xls.pack(side="left", padx=(10, 0))
        self.btn_wa = LeoButton(bar, "✆  WhatsApp", self.do_whatsapp, kind="ghost", app=self)
        self.btn_wa.pack(side="left", padx=(10, 0))
        self.btn_tg = LeoButton(bar, "✈  Telegram", self.do_telegram, kind="ghost", app=self)
        self.btn_tg.pack(side="left", padx=(10, 0))
        self.btn_print = LeoButton(bar, "🖨  Print", self.do_print, kind="ghost", app=self)
        self.btn_print.pack(side="left", padx=(10, 0))

        self.btn_copy = LeoButton(bar, "⧉  Copy Summary", self.copy_summary,
                                  kind="quiet", app=self)
        self.btn_copy.pack(side="right")

    # ---------------- theming ----------------
    def apply_theme(self, theme: dict):
        self.theme = theme
        t = theme

        self.root.configure(bg=t["bg_primary"])
        self.root_frame.configure(bg=t["bg_primary"])
        self.header.configure(bg=t["bg_secondary"])
        self.theme_bar.configure(bg=t["bg_primary"])
        self.body.configure(bg=t["bg_primary"])
        self.left.configure(bg=t["bg_primary"])
        self.right.configure(bg=t["bg_primary"])
        self.actions.configure(bg=t["bg_primary"])
        self.action_bar.configure(bg=t["bg_primary"])
        self.statusbar.configure(bg=t["bg_secondary"])

        self.brand.configure(bg=t["bg_secondary"])
        self.hdr_right.configure(bg=t["bg_secondary"])
        self.lbl_leo.configure(bg=t["bg_secondary"], fg=t["accent"],
                                font=self.font("serif", 30, "bold"))
        self.lbl_tag.configure(bg=t["bg_secondary"], fg=t["text_primary"],
                               font=self.font("sans", 11))
        self.lbl_credit.configure(bg=t["bg_secondary"], fg=t["text_muted"],
                                  font=self.font("sans", 9))
        self.lbl_theme_name.configure(bg=t["bg_secondary"], fg=t["text_muted"],
                                      font=self.font("sans", 9, "bold"),
                                      text=f"THEME  ·  {t['name'].upper()}")

        self.lbl_themes.configure(bg=t["bg_primary"], fg=t["text_muted"],
                                  font=self.font("sans", 9, "bold"))
        self.sw_box.configure(bg=t["bg_primary"])
        self.lbl_badge.configure(bg=t["bg_primary"], fg=t["accent_light"],
                                 font=self.font("sans", 9, "bold"), text=t["badge"].upper())

        for cv, th in self.swatches:
            active = th["id"] == t["id"]
            cv.configure(bg=t["bg_primary"],
                         highlightbackground=t["accent"] if active else mix(t["bg_primary"], t["text_primary"], 0.18))
            cv.delete("all")
            cv.create_oval(4, 4, 22, 22, fill=th["swatch"], outline="")
            if active:
                cv.create_oval(10, 10, 16, 16, fill=readable_on(th["swatch"]), outline="")

        self.lbl_inputs_title.configure(bg=t["surface"], fg=t["accent_light"],
                                        font=self.font("sans", 10, "bold"))
        self.lbl_inputs_rule.configure(bg=mix(t["surface"], t["accent"], 0.6))
        self.lbl_preset.configure(bg=t["surface"], fg=t["text_muted"],
                                  font=self.font("sans", 9, "bold"))
        self.inputs_inner.configure(bg=t["surface"])
        self.lbl_hint.configure(bg=t["surface"], fg=t["text_muted"],
                                font=self.font("sans", 8))
        for fr in self.surface_frames:
            try:
                fr.configure(bg=t["surface"])
            except tk.TclError:
                pass
        self.lbl_std_title.configure(bg=t["surface"], fg=t["text_muted"],
                                     font=self.font("sans", 8, "bold"))
        self.std_rule.configure(bg=mix(t["surface"], t["text_primary"], 0.16))
        self.lbl_std.configure(bg=t["surface"], fg=t["text_muted"],
                               font=self.font("mono", 9))

        self.lbl_status.configure(bg=t["bg_secondary"], fg=t["text_muted"],
                                  font=self.font("sans", 9))
        self.lbl_stamp.configure(bg=t["bg_secondary"], fg=t["text_muted"],
                                 font=self.font("sans", 9))

        self.btn_music.label.configure(text=("♪  Background Music: On" if self.music.playing
                                              else "♪  Background Music: Off"))
        for p in list(self.painters):
            try:
                p(t)
            except Exception:
                pass

        if self.report:
            self._render(self.report)

    def _paint_emblem(self, t):
        c = self.emblem
        c.configure(bg=t["bg_secondary"])
        c.delete("all")
        c.create_oval(3, 3, 71, 71, outline=t["accent"], width=1)
        c.create_oval(8, 8, 66, 66, outline=mix(t["bg_secondary"], t["accent"], 0.45), width=1)
        c.create_text(37, 34, text="L", fill=t["accent"], font=self.font("serif", 30, "bold"))
        c.create_line(24, 50, 50, 50, fill=mix(t["bg_secondary"], t["accent"], 0.55))
        c.create_text(37, 58, text="EST · LEO", fill=t["text_muted"],
                      font=self.font("sans", 6, "bold"))

    # ---------------- data plumbing ----------------
    @staticmethod
    def _num(text: str, default: float = 0.0) -> float:
        cleaned = (text or "").replace(",", "").replace(" ", "").replace("₹", "")
        cleaned = cleaned.replace("₫", "").replace("_", "").strip()
        if not cleaned:
            return default
        try:
            return float(cleaned)
        except ValueError:
            return default

    def _read_inputs(self):
        vn = self._num(self._entry_var["vietnam"].get())
        ind = self._num(self._entry_var["india"].get())
        fx = self._num(self._entry_var["fx"].get(), DEFAULT_FX_INR_TO_VND)
        if vn <= 0 or ind <= 0:
            raise ValueError("Please enter both gold prices (greater than zero).")
        if fx <= 0:
            fx = DEFAULT_FX_INR_TO_VND
            self._entry_var["fx"].set(f"{fx:.2f}")
        return vn, ind, fx

    def load_benchmarks(self, silent: bool = False):
        self._entry_var["vietnam"].set(f"{DEFAULT_VN_CHI_VND:,.0f}")
        self._entry_var["india"].set(f"{DEFAULT_IN_GRAM_INR:,.2f}")
        self._entry_var["fx"].set(f"{DEFAULT_FX_INR_TO_VND:.2f}")
        self.compare()
        if not silent:
            self.set_status("Loaded realistic November 2026 benchmarks.")

    def preset_india(self, purity: str = "24K"):
        """Re-price the India figure from the current 24K reference."""
        try:
            _vn, ind, _fx = self._read_inputs()
        except ValueError:
            ind = DEFAULT_IN_GRAM_INR
        ratio = 1.0 if purity == "24K" else 0.916
        target = ind * ratio if ind > 0 else DEFAULT_IN_GRAM_INR * ratio
        self._entry_var["india"].set(f"{target:,.2f}")
        self.compare()
        self.set_status(f"India price set to the {purity} reference · {fmt_inr(target)} per gram.")

    def reset_inputs(self):
        for v in self._entry_var.values():
            v.set("")
        self.report = None
        self.lbl_head.configure(text="AWAITING YOUR PRICES")
        self.lbl_sub.configure(text="Type the Vietnam (per Chỉ) and India (per Gram) prices, "
                                    "then press Compare.")
        self.lbl_stamp.configure(text="")
        self.set_status("Inputs cleared.")

    def compare(self):
        try:
            vn, ind, fx = self._read_inputs()
        except ValueError as exc:
            messagebox.showwarning(f"{APP_NAME} · Input needed", str(exc))
            self.set_status("Waiting for valid inputs…")
            return
        self.report = calculate(vn, ind, fx)
        self._render(self.report)
        self.set_status("Comparison updated · "
                        + summarise(self.report)["head"].title().replace("·", "—"))

    def _render(self, report: dict):
        s = summarise(report)
        self.lbl_head.configure(text=s["head"])
        self.lbl_sub.configure(text=s["sub"])
        for u in report["units"]:
            self.cards[u["key"]].set_values(u)
        self.lbl_stamp.configure(text=f"FX 1 INR = {report['fx']:,.2f} VND   ·   {report['stamp']}")

    def set_status(self, msg: str):
        self.lbl_status.configure(text=msg)

    def _ensure_report(self) -> bool:
        if not self.report:
            self.compare()
        if not self.report:
            messagebox.showinfo(f"{APP_NAME} · Nothing to export",
                                "Please compare the rates first.")
            return False
        return True

    # ---------------- music ----------------
    def toggle_music(self):
        ok = self.music.toggle()
        self.btn_music.label.configure(
            text="♪  Background Music: On" if self.music.playing else "♪  Background Music: Off")
        if self.music.playing:
            self.set_status("Background music on.")
            self._schedule_music_poll()
        else:
            self.set_status(self.music._error or "Background music off.")
            if self.music._error and not ok:
                messagebox.showwarning(f"{APP_NAME} · Audio", self.music._error)

    def _schedule_music_poll(self):
        if self._music_tick:
            self.root.after_cancel(self._music_tick)
        self._music_tick = self.root.after(1500, self._music_poll)

    def _music_poll(self):
        self.music.poll()
        if self.music.playing:
            self._music_tick = self.root.after(1500, self._music_poll)

    # ---------------- exports ----------------
    def _save_dialog(self, default_name: str, ext: str, types):
        return filedialog.asksaveasfilename(
            title=f"Save {APP_NAME} report",
            initialdir=_exports_dir(),
            initialfile=default_name,
            defaultextension=ext,
            filetypes=types,
        )

    def do_pdf(self):
        if not self._ensure_report():
            return
        try:
            path = export_pdf(self.report, self.theme)
        except ImportError:
            messagebox.showerror(f"{APP_NAME} · PDF library missing",
                                 "PDF export needs the 'reportlab' package.\n\n"
                                 "Install it with:\n    pip install reportlab")
            return
        except Exception as exc:
            messagebox.showerror(f"{APP_NAME} · PDF failed", str(exc))
            return
        self.set_status(f"PDF saved → {path}")
        self._offer_open(path, "PDF")

    def do_excel(self):
        if not self._ensure_report():
            return
        try:
            path = export_excel(self.report)
        except ImportError:
            messagebox.showerror(f"{APP_NAME} · Excel library missing",
                                 "Excel export needs the 'openpyxl' package.\n\n"
                                 "Install it with:\n    pip install openpyxl")
            return
        except Exception as exc:
            messagebox.showerror(f"{APP_NAME} · Excel failed", str(exc))
            return
        self.set_status(f"Excel saved → {path}")
        self._offer_open(path, "Excel workbook")

    def _offer_open(self, path: str, label: str):
        if messagebox.askyesno(f"{APP_NAME} · Done", f"{label} saved:\n{path}\n\nOpen it now?"):
            self.open_path(path)

    def open_path(self, path: str):
        try:
            if platform.system() == "Windows":
                os.startfile(path)          # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as exc:
            messagebox.showinfo(f"{APP_NAME}", f"Saved to:\n{path}\n\n({exc})")

    def copy_summary(self):
        if not self._ensure_report():
            return
        text = build_share_text(self.report)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.set_status("Summary copied to clipboard.")
        messagebox.showinfo(f"{APP_NAME} · Copied", "Comparison summary copied to the clipboard.")

    def do_whatsapp(self):
        if not self._ensure_report():
            return
        text = build_share_text(self.report)
        url = "https://wa.me/?text=" + urllib.parse.quote(text)
        try:
            webbrowser.open(url)
            self.set_status("WhatsApp opened with your comparison.")
        except Exception as exc:
            messagebox.showerror(f"{APP_NAME} · WhatsApp", str(exc))

    def do_telegram(self):
        if not self._ensure_report():
            return
        text = build_share_text(self.report)
        token = os.environ.get("LEO_TELEGRAM_BOT_TOKEN")
        chat = os.environ.get("LEO_TELEGRAM_CHAT_ID")
        if token and chat:
            try:
                import requests
                r = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat, "text": text}, timeout=12)
                if r.status_code == 200:
                    self.set_status("Sent to Telegram.")
                    messagebox.showinfo(f"{APP_NAME} · Telegram", "Report sent to your Telegram chat.")
                    return
                raise RuntimeError(r.text[:160])
            except Exception as exc:
                messagebox.showwarning(
                    f"{APP_NAME} · Telegram",
                    f"Bot delivery failed ({exc}).\n\nOpening Telegram share instead.")
        url = "https://t.me/share/url?url=" + urllib.parse.quote("LEO Gold Comparison") \
              + "&text=" + urllib.parse.quote(text)
        try:
            webbrowser.open(url)
            self.set_status("Telegram share opened.")
        except Exception as exc:
            messagebox.showerror(f"{APP_NAME} · Telegram", str(exc))

    def do_print(self):
        if not self._ensure_report():
            return
        try:
            path = export_pdf(self.report, self.theme)
        except ImportError:
            messagebox.showerror(f"{APP_NAME} · PDF library missing",
                                 "Printing needs the 'reportlab' package.\n\n"
                                 "Install it with:\n    pip install reportlab")
            return
        except Exception as exc:
            messagebox.showerror(f"{APP_NAME} · Print", str(exc))
            return
        self.set_status(f"Print-ready PDF created → {path}")
        try:
            if platform.system() == "Windows":
                os.startfile(path, "print")       # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                lp = shutil.which("lp")
                if lp:
                    subprocess.Popen([lp, path])
                else:
                    subprocess.Popen(["xdg-open", path],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            messagebox.showinfo(f"{APP_NAME} · Print",
                                f"Print-ready PDF saved to:\n{path}\n\n"
                                "Open it and press Ctrl+P to print.")

    # ---------------- misc ----------------
    def _bind_keys(self):
        self.root.bind("<Control-p>", lambda e: self.do_print())
        self.root.bind("<Control-s>", lambda e: self.do_pdf())
        self.root.bind("<Return>", lambda e: self.compare())
        self.root.bind("<F5>", lambda e: self.compare())

    def _on_close(self):
        self.music.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        root.iconname(APP_NAME)
    except Exception:
        pass
    LeoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
