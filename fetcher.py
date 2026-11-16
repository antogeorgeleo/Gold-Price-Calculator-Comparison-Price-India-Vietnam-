"""Real-time gold price & FX rate fetcher for Kerala (India) and Hanoi (Vietnam)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

GRAMS_PER_PAVAN = 8.0
GRAMS_PER_CHI = 3.75
GRAMS_PER_LUONG = 37.5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}


@dataclass
class KeralaKaratRate:
    karat: str
    purity: str
    per_gram_inr: float
    per_pavan_inr: float
    per_10g_inr: float
    change_gram_inr: float = 0.0
    change_pavan_inr: float = 0.0


@dataclass
class HanoiGoldRate:
    code: str
    name_en: str
    name_vi: str
    karat: str
    buy_per_chi_vnd: float
    sell_per_chi_vnd: float
    buy_per_luong_vnd: float
    sell_per_luong_vnd: float
    buy_per_gram_vnd: float
    sell_per_gram_vnd: float
    buy_per_pavan_vnd: float
    sell_per_pavan_vnd: float
    buy_per_gram_inr: float = 0.0
    sell_per_gram_inr: float = 0.0
    buy_per_pavan_inr: float = 0.0
    sell_per_pavan_inr: float = 0.0


@dataclass
class GoldMarketSnapshot:
    fetched_at: str
    fx_vnd_to_inr: float
    fx_inr_to_vnd: float
    fx_source: str
    kerala_updated: str
    kerala_source: str
    kerala_rates: list[KeralaKaratRate] = field(default_factory=list)
    hanoi_updated: str = ""
    hanoi_source: str = ""
    hanoi_rates: list[HanoiGoldRate] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def get_kerala(self, karat: str) -> KeralaKaratRate | None:
        for r in self.kerala_rates:
            if r.karat == karat:
                return r
        return None

    def get_hanoi(self, code: str) -> HanoiGoldRate | None:
        for r in self.hanoi_rates:
            if r.code == code:
                return r
        return None


def fetch_fx_rate(timeout: int = 12) -> tuple[float, str]:
    """Fetch live VND -> INR exchange rate."""
    try:
        r = requests.get("https://open.er-api.com/v6/latest/VND", headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        if data.get("result") == "success" and "INR" in data.get("rates", {}):
            return float(data["rates"]["INR"]), "open.er-api.com"
    except Exception:
        pass

    try:
        r = requests.get(
            "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/vnd.json",
            headers=HEADERS,
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        rate = float(data["vnd"]["inr"])
        return rate, "fawazahmed0/currency-api"
    except Exception as exc:
        raise RuntimeError(f"FX fetch failed: {exc}") from exc


def fetch_kerala_rates(timeout: int = 15) -> tuple[list[KeralaKaratRate], str, str]:
    """Fetch Kerala 24K, 22K, 18K rates in INR per gram and per pavan (8g)."""
    # Primary: keralagoldrates.com (official Kerala daily association rates)
    try:
        resp = requests.get("https://keralagoldrates.com/", headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        html = resp.text

        # Method 1: embedded JSON history
        match = re.search(r'const\s+homeGoldRatesRaw\s*=\s*"((?:\\.|[^"\\])*)"', html)
        if match:
            raw_json_str = json.loads(f'"{match.group(1)}"')
            payload = json.loads(raw_json_str)
            history = payload.get("history", [])
            if history:
                today = history[0]
                prev = history[1] if len(history) > 1 else {}

                def _make_rate(karat: str, purity: str, key: str) -> KeralaKaratRate | None:
                    val = today.get(key)
                    if not val:
                        return None
                    gram = float(val)
                    prev_gram = float(prev.get(key) or gram)
                    chg_g = gram - prev_gram
                    return KeralaKaratRate(
                        karat=karat,
                        purity=purity,
                        per_gram_inr=gram,
                        per_pavan_inr=gram * GRAMS_PER_PAVAN,
                        per_10g_inr=gram * 10.0,
                        change_gram_inr=chg_g,
                        change_pavan_inr=chg_g * GRAMS_PER_PAVAN,
                    )

                rates = [
                    r
                    for r in [
                        _make_rate("24K", "999 (24K)", "rate_24k"),
                        _make_rate("22K", "916 (22K)", "rate_22k"),
                        _make_rate("18K", "750 (18K)", "rate_18k"),
                    ]
                    if r is not None
                ]
                if rates:
                    updated = today.get("datetime_original") or today.get("date") or "Today"
                    return rates, str(updated), "keralagoldrates.com"

        # Method 2: regex over page text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        m22 = re.search(r"22\s*Karat\s*Gold.*?₹\s*([\d,]+)\s*/\s*gram", text, re.IGNORECASE)
        m24 = re.search(r"24\s*Karat\s*Gold.*?₹\s*([\d,]+)\s*/\s*gram", text, re.IGNORECASE)
        if m22 and m24:
            g24 = float(m24.group(1).replace(",", ""))
            g22 = float(m22.group(1).replace(",", ""))
            g18 = round(g24 * 0.75, 2)
            rates = [
                KeralaKaratRate("24K", "999 (24K)", g24, g24 * GRAMS_PER_PAVAN, g24 * 10),
                KeralaKaratRate("22K", "916 (22K)", g22, g22 * GRAMS_PER_PAVAN, g22 * 10),
                KeralaKaratRate("18K", "750 (18K)", g18, g18 * GRAMS_PER_PAVAN, g18 * 10),
            ]
            return rates, datetime.now().strftime("%Y-%m-%d %H:%M"), "keralagoldrates.com"
    except Exception:
        pass

    # Secondary fallback: trendiview.com/gold-price/kerala
    resp = requests.get("https://trendiview.com/gold-price/kerala", headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    m24 = re.search(r"24k\s*·\s*per\s*gram\s*₹\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
    m22 = re.search(r"22k\s*·\s*per\s*gram\s*₹\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
    if not (m24 and m22):
        raise RuntimeError("Could not parse Kerala gold prices from primary or fallback sources.")
    g24 = float(m24.group(1).replace(",", ""))
    g22 = float(m22.group(1).replace(",", ""))
    g18 = round(g24 * 0.75, 2)
    rates = [
        KeralaKaratRate("24K", "999 (24K)", g24, g24 * GRAMS_PER_PAVAN, g24 * 10),
        KeralaKaratRate("22K", "916 (22K)", g22, g22 * GRAMS_PER_PAVAN, g22 * 10),
        KeralaKaratRate("18K", "750 (18K)", g18, g18 * GRAMS_PER_PAVAN, g18 * 10),
    ]
    return rates, datetime.now().strftime("%Y-%m-%d %H:%M"), "trendiview.com (Spot Est.)"


def _build_hanoi_item(
    code: str,
    name_en: str,
    name_vi: str,
    karat: str,
    buy_chi_vnd: float,
    sell_chi_vnd: float,
    vnd_to_inr: float,
) -> HanoiGoldRate:
    buy_g = buy_chi_vnd / GRAMS_PER_CHI
    sell_g = sell_chi_vnd / GRAMS_PER_CHI
    buy_p = buy_g * GRAMS_PER_PAVAN
    sell_p = sell_g * GRAMS_PER_PAVAN
    return HanoiGoldRate(
        code=code,
        name_en=name_en,
        name_vi=name_vi,
        karat=karat,
        buy_per_chi_vnd=buy_chi_vnd,
        sell_per_chi_vnd=sell_chi_vnd,
        buy_per_luong_vnd=buy_chi_vnd * 10.0,
        sell_per_luong_vnd=sell_chi_vnd * 10.0,
        buy_per_gram_vnd=buy_g,
        sell_per_gram_vnd=sell_g,
        buy_per_pavan_vnd=buy_p,
        sell_per_pavan_vnd=sell_p,
        buy_per_gram_inr=buy_g * vnd_to_inr,
        sell_per_gram_inr=sell_g * vnd_to_inr,
        buy_per_pavan_inr=buy_p * vnd_to_inr,
        sell_per_pavan_inr=sell_p * vnd_to_inr,
    )


def fetch_hanoi_rates(vnd_to_inr: float, timeout: int = 15) -> tuple[list[HanoiGoldRate], str, str]:
    """Fetch Hanoi, Vietnam gold rates (PNJ Hanoi zone=11 primary, CafeF SJC fallback)."""
    # Primary: PNJ Official API (zone=11 -> Hanoi)
    try:
        url = "https://edge-api.pnj.io/ecom-frontend/v1/get-gold-price?zone=11"
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
        items = {row.get("masp"): row for row in payload.get("data", [])}

        wanted = [
            ("SJC", "SJC Gold Bar (Hanoi)", "Vàng miếng SJC 999.9", "24K (999.9)"),
            ("N24K", "PNJ 24K Plain Ring", "Nhẫn Trơn PNJ 999.9", "24K (999.9)"),
            ("24K", "24K Jewelry Gold", "Vàng nữ trang 999.9", "24K (999.9)"),
            ("22K", "22K Gold (916)", "Vàng 916 (22K)", "22K (916)"),
            ("75", "18K Gold (750)", "Vàng 750 (18K)", "18K (750)"),
        ]

        results: list[HanoiGoldRate] = []
        for code, name_en, name_vi, karat in wanted:
            row = items.get(code)
            if not row:
                continue
            buy_raw = row.get("giamua")
            sell_raw = row.get("giaban")
            if not buy_raw or not sell_raw:
                continue
            # PNJ API quotes in 1,000 VND per chỉ (3.75g)
            buy_chi_vnd = float(buy_raw) * 1000.0
            sell_chi_vnd = float(sell_raw) * 1000.0
            results.append(
                _build_hanoi_item(code, name_en, name_vi, karat, buy_chi_vnd, sell_chi_vnd, vnd_to_inr)
            )

        if results:
            updated = payload.get("updateDate") or datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            return results, str(updated), "PNJ Hanoi API (pnj.com.vn)"
    except Exception:
        pass

    # Fallback: CafeF SJC JSON
    resp = requests.get(
        "https://cafef.vn/du-lieu/Ajax/ajaxgoldpricehistory.ashx?index=1",
        headers=HEADERS,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json().get("Data", {})
    histories = data.get("goldPriceWorldHistories", [])
    if not histories:
        raise RuntimeError("Could not parse Hanoi gold prices from primary or fallback sources.")
    latest = histories[0]
    # CafeF quotes in million VND per lượng (10 chỉ) -> * 100,000 gives VND per chỉ
    buy_chi = float(latest["buyPrice"]) * 100_000.0
    sell_chi = float(latest["sellPrice"]) * 100_000.0
    results = [
        _build_hanoi_item(
            "SJC", "SJC Gold Bar (Vietnam)", "Vàng miếng SJC", "24K (999.9)", buy_chi, sell_chi, vnd_to_inr
        )
    ]
    updated = latest.get("createdAt", datetime.now().isoformat())
    return results, str(updated), "CafeF SJC API"


def fetch_all_market_data() -> GoldMarketSnapshot:
    """Fetch FX rate, Kerala gold rates, and Hanoi gold rates in one snapshot."""
    errors: list[str] = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        vnd_to_inr, fx_source = fetch_fx_rate()
    except Exception as exc:
        vnd_to_inr, fx_source = 0.00366, f"Fallback ({exc})"
        errors.append(str(exc))

    inr_to_vnd = (1.0 / vnd_to_inr) if vnd_to_inr > 0 else 0.0

    kerala_rates: list[KeralaKaratRate] = []
    kerala_updated = "N/A"
    kerala_source = "N/A"
    try:
        kerala_rates, kerala_updated, kerala_source = fetch_kerala_rates()
    except Exception as exc:
        errors.append(f"Kerala fetch error: {exc}")

    hanoi_rates: list[HanoiGoldRate] = []
    hanoi_updated = "N/A"
    hanoi_source = "N/A"
    try:
        hanoi_rates, hanoi_updated, hanoi_source = fetch_hanoi_rates(vnd_to_inr)
    except Exception as exc:
        errors.append(f"Hanoi fetch error: {exc}")

    return GoldMarketSnapshot(
        fetched_at=now_str,
        fx_vnd_to_inr=vnd_to_inr,
        fx_inr_to_vnd=inr_to_vnd,
        fx_source=fx_source,
        kerala_updated=kerala_updated,
        kerala_source=kerala_source,
        kerala_rates=kerala_rates,
        hanoi_updated=hanoi_updated,
        hanoi_source=hanoi_source,
        hanoi_rates=hanoi_rates,
        errors=errors,
    )
