"""
LEO — Luxury Vietnam & India Gold Rate Comparison Engine
Created by Anto George Leo

Core weight conversions, currency formatting (INR Lakh/Crore & VND),
live FX rate retrieval, and structured comparison matrices across
Chi (3.75g), Gram (1.00g), and Pavan (8.00g).
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests

# Exact Gold Weight Standards
GRAMS_PER_CHI: float = 3.75       # 1 Vietnamese Chỉ = 3.75 grams (1/10 Lượng)
GRAMS_PER_GRAM: float = 1.00      # 1 Metric Gram = 1.00 gram
GRAMS_PER_PAVAN: float = 8.00     # 1 Indian Pavan (Sovereign) = 8.00 grams
GRAMS_PER_LUONG: float = 37.50    # 1 Vietnamese Lượng (Cây / Tael) = 10 Chỉ = 37.50 grams

DEFAULT_VN_CHI_VND: float = 14_100_000.0   # ~14.10M VND per Chỉ (9999 / SJC benchmark)
DEFAULT_IN_GRAM_INR: float = 13_849.00     # ~₹13,849 per Gram (24K India benchmark)
DEFAULT_FX_INR_TO_VND: float = 273.07      # 1 INR = ~273.07 VND

# 10 Curated Luxury Color Themes
THEMES: Dict[str, Dict[str, str]] = {
    "imperial_gold": {
        "id": "imperial_gold",
        "name": "Imperial Gold & Obsidian",
        "badge": "Signature 24K",
        "mode": "dark",
        "bg_primary": "#0A0C10",
        "bg_secondary": "#121620",
        "surface": "#171C28",
        "accent": "#D4AF37",
        "accent_light": "#F5D77F",
        "accent_secondary": "#B8860B",
        "text_primary": "#F8F5EE",
        "text_muted": "#A39E93",
        "swatch": "#D4AF37",
    },
    "emerald_vault": {
        "id": "emerald_vault",
        "name": "Royal Emerald Vault",
        "badge": "Heritage Green",
        "mode": "dark",
        "bg_primary": "#061510",
        "bg_secondary": "#0C241C",
        "surface": "#113026",
        "accent": "#10B981",
        "accent_light": "#6EE7B7",
        "accent_secondary": "#D4AF37",
        "text_primary": "#ECFDF5",
        "text_muted": "#94B8A8",
        "swatch": "#10B981",
    },
    "ruby_velvet": {
        "id": "ruby_velvet",
        "name": "Maharaja Ruby Velvet",
        "badge": "Regal Crimson",
        "mode": "dark",
        "bg_primary": "#18070D",
        "bg_secondary": "#260D16",
        "surface": "#33121E",
        "accent": "#F43F5E",
        "accent_light": "#FDA4AF",
        "accent_secondary": "#EAB308",
        "text_primary": "#FFF1F2",
        "text_muted": "#C49BA3",
        "swatch": "#F43F5E",
    },
    "sapphire_crown": {
        "id": "sapphire_crown",
        "name": "Midnight Sapphire Crown",
        "badge": "Celestial Blue",
        "mode": "dark",
        "bg_primary": "#071022",
        "bg_secondary": "#0E1B36",
        "surface": "#15264A",
        "accent": "#3B82F6",
        "accent_light": "#93C5FD",
        "accent_secondary": "#FBBF24",
        "text_primary": "#EFF6FF",
        "text_muted": "#94A8C7",
        "swatch": "#3B82F6",
    },
    "amethyst_sovereign": {
        "id": "amethyst_sovereign",
        "name": "Amethyst Sovereign",
        "badge": "Royal Violet",
        "mode": "dark",
        "bg_primary": "#120920",
        "bg_secondary": "#1D1033",
        "surface": "#271745",
        "accent": "#A855F7",
        "accent_light": "#D8B4FE",
        "accent_secondary": "#F59E0B",
        "text_primary": "#FAF5FF",
        "text_muted": "#B3A0CC",
        "swatch": "#A855F7",
    },
    "champagne_pearl": {
        "id": "champagne_pearl",
        "name": "Champagne Ivory Pearl",
        "badge": "Couture Light",
        "mode": "light",
        "bg_primary": "#F9F6F0",
        "bg_secondary": "#F1ECE1",
        "surface": "#FFFFFF",
        "accent": "#9A6F18",
        "accent_light": "#C99A36",
        "accent_secondary": "#78530D",
        "text_primary": "#1C1917",
        "text_muted": "#6B6358",
        "swatch": "#E6CFA3",
    },
    "rose_gold_couture": {
        "id": "rose_gold_couture",
        "name": "Rose Gold Couture",
        "badge": "Blush Metallic",
        "mode": "dark",
        "bg_primary": "#180E13",
        "bg_secondary": "#24161D",
        "surface": "#301E27",
        "accent": "#E88D80",
        "accent_light": "#F7C4BC",
        "accent_secondary": "#F3C677",
        "text_primary": "#FFF5F5",
        "text_muted": "#C2A1A6",
        "swatch": "#E88D80",
    },
    "saigon_jade": {
        "id": "saigon_jade",
        "name": "Saigon Jade & Amber",
        "badge": "Oriental Teal",
        "mode": "dark",
        "bg_primary": "#06171A",
        "bg_secondary": "#0C252A",
        "surface": "#12333A",
        "accent": "#14B8A6",
        "accent_light": "#5EEAD4",
        "accent_secondary": "#F59E0B",
        "text_primary": "#F0FDFA",
        "text_muted": "#8EBAB5",
        "swatch": "#14B8A6",
    },
    "platinum_titanium": {
        "id": "platinum_titanium",
        "name": "Platinum Horology",
        "badge": "Swiss Slate",
        "mode": "dark",
        "bg_primary": "#0C1117",
        "bg_secondary": "#151D26",
        "surface": "#1E2936",
        "accent": "#38BDF8",
        "accent_light": "#BAE6FD",
        "accent_secondary": "#94A3B8",
        "text_primary": "#F1F5F9",
        "text_muted": "#94A3B8",
        "swatch": "#38BDF8",
    },
    "saffron_palace": {
        "id": "saffron_palace",
        "name": "Saffron Sunset Palace",
        "badge": "Marigold Gold",
        "mode": "dark",
        "bg_primary": "#180E06",
        "bg_secondary": "#26170B",
        "surface": "#362110",
        "accent": "#F97316",
        "accent_light": "#FDBA74",
        "accent_secondary": "#FACC15",
        "text_primary": "#FFF7ED",
        "text_muted": "#C7A68B",
        "swatch": "#F97316",
    },
}

_FX_CACHE: Dict[str, Any] = {
    "rate": DEFAULT_FX_INR_TO_VND,
    "source": "Market Benchmark (1 INR = 273.07 VND)",
    "updated_at": None,
    "timestamp": 0.0,
}


def format_indian_number(value: float, decimals: int = 2) -> str:
    """Format number using the Indian Lakh/Crore comma system (e.g., 1,10,792.00)."""
    neg = value < 0
    val = abs(float(value))
    formatted = f"{val:.{decimals}f}"
    if "." in formatted:
        int_part, dec_part = formatted.split(".")
    else:
        int_part, dec_part = formatted, ""

    if len(int_part) > 3:
        last_three = int_part[-3:]
        rest = int_part[:-3]
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        groups.reverse()
        int_formatted = ",".join(groups) + "," + last_three
    else:
        int_formatted = int_part

    result = f"{int_formatted}.{dec_part}" if decimals > 0 else int_formatted
    return f"-{result}" if neg else result


def format_inr(value: float, decimals: int = 2, symbol: str = "₹") -> str:
    neg = value < 0
    core = format_indian_number(abs(value), decimals=decimals)
    return f"-{symbol}{core}" if neg else f"{symbol}{core}"


def format_vnd(value: float, symbol: str = "₫") -> str:
    neg = value < 0
    rounded = int(round(abs(float(value))))
    core = f"{rounded:,}"
    return f"-{core} {symbol}" if neg else f"{core} {symbol}"


def get_live_fx_rate(force_refresh: bool = False) -> Dict[str, Any]:
    """Fetch live INR -> VND exchange rate with 30-min cache and graceful fallback."""
    now = time.time()
    if not force_refresh and _FX_CACHE["updated_at"] and (now - _FX_CACHE["timestamp"] < 1800):
        return dict(_FX_CACHE)

    endpoints = [
        "https://open.er-api.com/v6/latest/INR",
        "https://api.exchangerate-api.com/v4/latest/INR",
    ]
    for url in endpoints:
        try:
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                rates = data.get("rates", {})
                vnd_rate = rates.get("VND")
                if vnd_rate and float(vnd_rate) > 10:
                    _FX_CACHE["rate"] = round(float(vnd_rate), 2)
                    _FX_CACHE["source"] = "Live Global Forex Feed"
                    _FX_CACHE["updated_at"] = datetime.now().strftime("%d %b %Y, %H:%M")
                    _FX_CACHE["timestamp"] = now
                    return dict(_FX_CACHE)
        except Exception:
            continue

    if not _FX_CACHE["updated_at"]:
        _FX_CACHE["updated_at"] = datetime.now().strftime("%d %b %Y, %H:%M")
    return dict(_FX_CACHE)


def _build_unit_row(
    key: str,
    label: str,
    subtitle: str,
    grams: float,
    vn_gram_vnd: float,
    in_gram_inr: float,
    fx_inr_to_vnd: float,
) -> Dict[str, Any]:
    vn_vnd = vn_gram_vnd * grams
    vn_inr = vn_vnd / fx_inr_to_vnd

    in_inr = in_gram_inr * grams
    in_vnd = in_inr * fx_inr_to_vnd

    # diff = Vietnam - India (negative => Vietnam is cheaper; positive => India is cheaper)
    diff_inr = vn_inr - in_inr
    diff_vnd = vn_vnd - in_vnd
    abs_diff_inr = abs(diff_inr)
    abs_diff_vnd = abs(diff_vnd)

    min_inr = min(vn_inr, in_inr)
    pct_spread = (abs_diff_inr / min_inr * 100.0) if min_inr > 0 else 0.0

    if abs(pct_spread) < 0.01:
        cheaper_country = "Parity"
        verdict_badge = "Equal Price Parity"
    elif diff_inr < 0:
        cheaper_country = "Vietnam"
        verdict_badge = f"Vietnam Cheaper by {pct_spread:.2f}%"
    else:
        cheaper_country = "India"
        verdict_badge = f"India Cheaper by {pct_spread:.2f}%"

    return {
        "key": key,
        "label": label,
        "subtitle": subtitle,
        "grams": round(grams, 5),
        "chi_equiv": round(grams / GRAMS_PER_CHI, 5),
        "pavan_equiv": round(grams / GRAMS_PER_PAVAN, 5),
        "vn_vnd": round(vn_vnd, 2),
        "vn_inr": round(vn_inr, 2),
        "in_inr": round(in_inr, 2),
        "in_vnd": round(in_vnd, 2),
        "diff_inr": round(diff_inr, 2),
        "diff_vnd": round(diff_vnd, 2),
        "abs_diff_inr": round(abs_diff_inr, 2),
        "abs_diff_vnd": round(abs_diff_vnd, 2),
        "pct_spread": round(pct_spread, 2),
        "cheaper_country": cheaper_country,
        "verdict_badge": verdict_badge,
        "formatted": {
            "vn_vnd": format_vnd(vn_vnd),
            "vn_inr": format_inr(vn_inr),
            "in_inr": format_inr(in_inr),
            "in_vnd": format_vnd(in_vnd),
            "abs_diff_inr": format_inr(abs_diff_inr),
            "abs_diff_vnd": format_vnd(abs_diff_vnd),
            "signed_diff_inr": ("+" if diff_inr > 0 else "") + format_inr(diff_inr),
            "signed_diff_vnd": ("+" if diff_vnd > 0 else "") + format_vnd(diff_vnd),
        },
    }


def calculate_gold_comparison(
    vn_price_per_chi_vnd: float = DEFAULT_VN_CHI_VND,
    in_price_per_gram_inr: float = DEFAULT_IN_GRAM_INR,
    fx_inr_to_vnd: float = DEFAULT_FX_INR_TO_VND,
    purity: str = "24K (999.9 Pure Gold)",
    vn_extra_pct: float = 0.0,
    in_extra_pct: float = 0.0,
    custom_qty: float = 1.0,
    custom_unit: str = "pavan",
    theme_id: str = "imperial_gold",
    customer_note: str = "",
) -> Dict[str, Any]:
    """Compute full Vietnam vs India gold comparison in Chi, Gram, and Pavan."""
    vn_chi_base = max(0.0, float(vn_price_per_chi_vnd))
    in_gram_base = max(0.0, float(in_price_per_gram_inr))
    fx = max(0.0001, float(fx_inr_to_vnd))
    vn_tax = max(0.0, float(vn_extra_pct))
    in_tax = max(0.0, float(in_extra_pct))
    qty = max(0.01, float(custom_qty))

    vn_chi_effective_vnd = vn_chi_base * (1.0 + vn_tax / 100.0)
    vn_gram_vnd = vn_chi_effective_vnd / GRAMS_PER_CHI

    in_gram_effective_inr = in_gram_base * (1.0 + in_tax / 100.0)

    # Primary three required comparison units: Chi, Gram, Pavan
    units = [
        _build_unit_row(
            key="chi",
            label="1 Chỉ (Vietnam Unit)",
            subtitle="3.75 Grams • 0.4688 Pavan",
            grams=GRAMS_PER_CHI,
            vn_gram_vnd=vn_gram_vnd,
            in_gram_inr=in_gram_effective_inr,
            fx_inr_to_vnd=fx,
        ),
        _build_unit_row(
            key="gram",
            label="1 Gram (Standard Unit)",
            subtitle="1.00 Gram • 0.2667 Chỉ • 0.125 Pavan",
            grams=GRAMS_PER_GRAM,
            vn_gram_vnd=vn_gram_vnd,
            in_gram_inr=in_gram_effective_inr,
            fx_inr_to_vnd=fx,
        ),
        _build_unit_row(
            key="pavan",
            label="1 Pavan (Indian Sovereign)",
            subtitle="8.00 Grams • 2.1333 Chỉ",
            grams=GRAMS_PER_PAVAN,
            vn_gram_vnd=vn_gram_vnd,
            in_gram_inr=in_gram_effective_inr,
            fx_inr_to_vnd=fx,
        ),
    ]

    # Additional reference row: 1 Lượng (10 Chỉ = 37.5g)
    luong_row = _build_unit_row(
        key="luong",
        label="1 Lượng / Cây (10 Chỉ)",
        subtitle="37.50 Grams • 4.6875 Pavan",
        grams=GRAMS_PER_LUONG,
        vn_gram_vnd=vn_gram_vnd,
        in_gram_inr=in_gram_effective_inr,
        fx_inr_to_vnd=fx,
    )

    unit_gram_map = {
        "chi": GRAMS_PER_CHI,
        "gram": GRAMS_PER_GRAM,
        "pavan": GRAMS_PER_PAVAN,
        "luong": GRAMS_PER_LUONG,
    }
    unit_name_map = {
        "chi": "Chỉ",
        "gram": "Gram(s)",
        "pavan": "Pavan(s)",
        "luong": "Lượng",
    }
    c_unit = custom_unit.lower() if custom_unit.lower() in unit_gram_map else "pavan"
    custom_grams = qty * unit_gram_map[c_unit]
    custom_row = _build_unit_row(
        key="custom",
        label=f"{qty:g} {unit_name_map[c_unit]}",
        subtitle=f"{custom_grams:.2f} Grams • {custom_grams / GRAMS_PER_CHI:.2f} Chỉ • {custom_grams / GRAMS_PER_PAVAN:.2f} Pavan",
        grams=custom_grams,
        vn_gram_vnd=vn_gram_vnd,
        in_gram_inr=in_gram_effective_inr,
        fx_inr_to_vnd=fx,
    )

    gram_row = units[1]
    chi_row = units[0]
    pavan_row = units[2]

    if gram_row["cheaper_country"] == "Vietnam":
        headline = f"Gold is {gram_row['pct_spread']:.2f}% Cheaper in Vietnam 🇻🇳 than India 🇮🇳"
        recommendation = (
            f"Buying in Vietnam saves {pavan_row['formatted']['abs_diff_inr']} "
            f"({pavan_row['formatted']['abs_diff_vnd']}) per 1 Pavan (8g) and "
            f"{chi_row['formatted']['abs_diff_inr']} ({chi_row['formatted']['abs_diff_vnd']}) per 1 Chỉ (3.75g)."
        )
    elif gram_row["cheaper_country"] == "India":
        headline = f"Gold is {gram_row['pct_spread']:.2f}% Cheaper in India 🇮🇳 than Vietnam 🇻🇳"
        recommendation = (
            f"Buying in India saves {pavan_row['formatted']['abs_diff_inr']} "
            f"({pavan_row['formatted']['abs_diff_vnd']}) per 1 Pavan (8g) and "
            f"{chi_row['formatted']['abs_diff_inr']} ({chi_row['formatted']['abs_diff_vnd']}) per 1 Chỉ (3.75g)."
        )
    else:
        headline = "Vietnam 🇻🇳 and India 🇮🇳 Gold Prices are at Exact Market Parity"
        recommendation = "Both markets offer identical effective gold rates across Chỉ, Gram, and Pavan."

    timestamp_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    theme = THEMES.get(theme_id, THEMES["imperial_gold"])

    result: Dict[str, Any] = {
        "app_name": "LEO",
        "creator": "Anto George Leo",
        "generated_at": timestamp_str,
        "purity": purity,
        "customer_note": customer_note.strip(),
        "theme": theme,
        "inputs": {
            "vn_price_per_chi_vnd": vn_chi_base,
            "in_price_per_gram_inr": in_gram_base,
            "fx_inr_to_vnd": fx,
            "fx_vnd_to_inr": round(1.0 / fx, 6),
            "vn_extra_pct": vn_tax,
            "in_extra_pct": in_tax,
            "vn_effective_chi_vnd": vn_chi_effective_vnd,
            "in_effective_gram_inr": in_gram_effective_inr,
            "custom_qty": qty,
            "custom_unit": c_unit,
            "formatted": {
                "vn_input_chi_vnd": format_vnd(vn_chi_base),
                "vn_effective_chi_vnd": format_vnd(vn_chi_effective_vnd),
                "vn_luong_vnd": format_vnd(vn_chi_effective_vnd * 10),
                "in_input_gram_inr": format_inr(in_gram_base),
                "in_effective_gram_inr": format_inr(in_gram_effective_inr),
                "in_pavan_inr": format_inr(in_gram_effective_inr * 8.0),
                "fx_display": f"₹1 INR = {fx:,.2f} ₫ VND",
                "fx_inverse_display": f"10,000 ₫ VND = ₹{10000.0 / fx:,.2f} INR",
            },
        },
        "units": units,
        "by_key": {
            "chi": chi_row,
            "gram": gram_row,
            "pavan": pavan_row,
            "luong": luong_row,
            "custom": custom_row,
        },
        "summary": {
            "cheaper_country": gram_row["cheaper_country"],
            "pct_spread": gram_row["pct_spread"],
            "headline": headline,
            "recommendation": recommendation,
        },
    }

    result["share_messages"] = {
        "whatsapp": build_whatsapp_message(result),
        "telegram": build_telegram_message(result),
    }
    return result


def build_whatsapp_message(report: Dict[str, Any]) -> str:
    """Format a crisp WhatsApp-ready comparison message with bold/italic markers."""
    inp = report["inputs"]
    chi = report["by_key"]["chi"]
    gram = report["by_key"]["gram"]
    pavan = report["by_key"]["pavan"]
    summ = report["summary"]

    tax_line = ""
    if inp["vn_extra_pct"] > 0 or inp["in_extra_pct"] > 0:
        tax_line = f"\n• Adjustments: VN +{inp['vn_extra_pct']:g}% | IN +{inp['in_extra_pct']:g}%"

    note_line = f"\n📝 *Note:* {report['customer_note']}" if report.get("customer_note") else ""

    lines = [
        "🦁 *LEO — GOLD RATE COMPARISON*",
        "_Vietnam 🇻🇳 vs India 🇮🇳 Executive Report_",
        f"📅 {report['generated_at']} | ✨ {report['purity']}",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "📥 *USER INPUT RATES*",
        f"🇻🇳 Vietnam (1 Chỉ / 3.75g): *{inp['formatted']['vn_effective_chi_vnd']}*",
        f"🇮🇳 India (1 Gram / 1.00g): *{inp['formatted']['in_effective_gram_inr']}*",
        f"💱 FX Rate: *{inp['formatted']['fx_display']}*{tax_line}",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "⚖️ *COMPARISON BY WEIGHT UNIT*",
        "",
        "1️⃣ *PER 1 CHỈ (3.75 Grams)*",
        f"   🇻🇳 Vietnam: *{chi['formatted']['vn_vnd']}* ({chi['formatted']['vn_inr']})",
        f"   🇮🇳 India: *{chi['formatted']['in_inr']}* ({chi['formatted']['in_vnd']})",
        f"   📊 Diff: *{chi['formatted']['abs_diff_inr']}* ({chi['formatted']['abs_diff_vnd']}) → _{chi['verdict_badge']}_",
        "",
        "2️⃣ *PER 1 GRAM (1.00 Gram)*",
        f"   🇻🇳 Vietnam: *{gram['formatted']['vn_vnd']}* ({gram['formatted']['vn_inr']})",
        f"   🇮🇳 India: *{gram['formatted']['in_inr']}* ({gram['formatted']['in_vnd']})",
        f"   📊 Diff: *{gram['formatted']['abs_diff_inr']}* ({gram['formatted']['abs_diff_vnd']}) → _{gram['verdict_badge']}_",
        "",
        "3️⃣ *PER 1 PAVAN / SOVEREIGN (8.00 Grams)*",
        f"   🇻🇳 Vietnam: *{pavan['formatted']['vn_vnd']}* ({pavan['formatted']['vn_inr']})",
        f"   🇮🇳 India: *{pavan['formatted']['in_inr']}* ({pavan['formatted']['in_vnd']})",
        f"   📊 Diff: *{pavan['formatted']['abs_diff_inr']}* ({pavan['formatted']['abs_diff_vnd']}) → _{pavan['verdict_badge']}_",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🏆 *VERDICT:* {summ['headline']}",
        f"💡 {summ['recommendation']}{note_line}",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "👑 _Application: *LEO* | Created by *Anto George Leo*_",
    ]
    return "\n".join(lines)


def build_telegram_message(report: Dict[str, Any]) -> str:
    """Format a clean Telegram-ready comparison report."""
    inp = report["inputs"]
    chi = report["by_key"]["chi"]
    gram = report["by_key"]["gram"]
    pavan = report["by_key"]["pavan"]
    summ = report["summary"]

    note_line = f"\n📝 Note: {report['customer_note']}" if report.get("customer_note") else ""

    lines = [
        "🦁 LEO — VIETNAM 🇻🇳 & INDIA 🇮🇳 GOLD COMPARISON",
        f"🕒 {report['generated_at']}  •  💎 {report['purity']}",
        "══════════════════════════",
        f"🇻🇳 Vietnam Input (1 Chỉ = 3.75g): {inp['formatted']['vn_effective_chi_vnd']}",
        f"🇮🇳 India Input (1 Gram = 1.00g): {inp['formatted']['in_effective_gram_inr']}",
        f"💱 Exchange Rate: {inp['formatted']['fx_display']}",
        "══════════════════════════",
        "",
        "🔸 1 CHỈ (3.75g | 0.4688 Pavan)",
        f"  • Vietnam : {chi['formatted']['vn_vnd']}  [{chi['formatted']['vn_inr']}]",
        f"  • India   : {chi['formatted']['in_inr']}  [{chi['formatted']['in_vnd']}]",
        f"  • Spread  : {chi['formatted']['abs_diff_inr']} ({chi['formatted']['abs_diff_vnd']}) — {chi['verdict_badge']}",
        "",
        "🔸 1 GRAM (1.00g | 0.2667 Chỉ | 0.125 Pavan)",
        f"  • Vietnam : {gram['formatted']['vn_vnd']}  [{gram['formatted']['vn_inr']}]",
        f"  • India   : {gram['formatted']['in_inr']}  [{gram['formatted']['in_vnd']}]",
        f"  • Spread  : {gram['formatted']['abs_diff_inr']} ({gram['formatted']['abs_diff_vnd']}) — {gram['verdict_badge']}",
        "",
        "🔸 1 PAVAN / SOVEREIGN (8.00g | 2.1333 Chỉ)",
        f"  • Vietnam : {pavan['formatted']['vn_vnd']}  [{pavan['formatted']['vn_inr']}]",
        f"  • India   : {pavan['formatted']['in_inr']}  [{pavan['formatted']['in_vnd']}]",
        f"  • Spread  : {pavan['formatted']['abs_diff_inr']} ({pavan['formatted']['abs_diff_vnd']}) — {pavan['verdict_badge']}",
        "",
        "══════════════════════════",
        f"🏆 {summ['headline']}",
        f"💡 {summ['recommendation']}{note_line}",
        "",
        "✨ Powered by LEO • Created by Anto George Leo",
    ]
    return "\n".join(lines)
