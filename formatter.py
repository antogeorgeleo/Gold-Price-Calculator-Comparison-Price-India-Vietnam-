"""Format live gold price snapshots for WhatsApp and Telegram messages."""

from __future__ import annotations

from fetcher import GoldMarketSnapshot


def _fmt_inr(val: float) -> str:
    return f"₹{val:,.2f}" if val % 1 else f"₹{val:,.0f}"


def _fmt_vnd(val: float) -> str:
    return f"{val:,.0f} ₫"


def _fmt_change(val: float) -> str:
    if val > 0:
        return f"+₹{val:,.0f}"
    if val < 0:
        return f"-₹{abs(val):,.0f}"
    return "₹0"


def format_messenger_report(snapshot: GoldMarketSnapshot) -> str:
    """Create a rich, readable report suitable for both WhatsApp and Telegram."""
    lines: list[str] = [
        "*LIVE GOLD PRICE REPORT*",
        f"Updated: {snapshot.fetched_at}",
        f"FX Rate: 1 INR = {snapshot.fx_inr_to_vnd:,.2f} VND (1 VND = ₹{snapshot.fx_vnd_to_inr:.6f})",
        "",
        "*KERALA, INDIA (INR)*",
    ]

    if snapshot.kerala_rates:
        for r in snapshot.kerala_rates:
            if r.karat in ("24K", "22K", "18K"):
                chg = f" ({_fmt_change(r.change_gram_inr)}/g, {_fmt_change(r.change_pavan_inr)}/pavan)" if r.change_gram_inr else ""
                lines.append(
                    f"• *{r.purity}*: {_fmt_inr(r.per_gram_inr)} /g | *{_fmt_inr(r.per_pavan_inr)} /pavan (8g)*{chg}"
                )
        lines.append(f"_Source: {snapshot.kerala_source} ({snapshot.kerala_updated})_")
    else:
        lines.append("• Kerala data unavailable")

    lines.append("")
    lines.append("*HANOI, VIETNAM (VND & INR)*")
    if snapshot.hanoi_rates:
        for r in snapshot.hanoi_rates:
            if r.code in ("SJC", "N24K", "22K"):
                lines.append(f"• *{r.name_en}* ({r.karat}):")
                lines.append(
                    f"   Sell: {_fmt_vnd(r.sell_per_gram_vnd)}/g ({_fmt_inr(r.sell_per_gram_inr)}/g) | "
                    f"*{_fmt_vnd(r.sell_per_pavan_vnd)}/pavan ({_fmt_inr(r.sell_per_pavan_inr)}/pavan)*"
                )
                lines.append(
                    f"   Buy : {_fmt_vnd(r.buy_per_gram_vnd)}/g ({_fmt_inr(r.buy_per_gram_inr)}/g) | "
                    f"{_fmt_vnd(r.buy_per_pavan_vnd)}/pavan ({_fmt_inr(r.buy_per_pavan_inr)}/pavan)"
                )
        lines.append(f"_Source: {snapshot.hanoi_source} ({snapshot.hanoi_updated})_")
    else:
        lines.append("• Hanoi data unavailable")

    # Quick Kerala vs Hanoi Comparison
    k24 = snapshot.get_kerala("24K")
    k22 = snapshot.get_kerala("22K")
    h_sjc = snapshot.get_hanoi("SJC") or snapshot.get_hanoi("N24K")
    h22 = snapshot.get_hanoi("22K")

    if (k24 and h_sjc) or (k22 and h22):
        lines.append("")
        lines.append("*KERALA vs HANOI COMPARISON (Sell Rate in INR)*")
        if k24 and h_sjc:
            diff_g = k24.per_gram_inr - h_sjc.sell_per_gram_inr
            diff_p = k24.per_pavan_inr - h_sjc.sell_per_pavan_inr
            cheaper = "Hanoi" if diff_g > 0 else "Kerala"
            lines.append(
                f"• 24K (Kerala vs Hanoi SJC): {cheaper} cheaper by {_fmt_inr(abs(diff_g))}/g "
                f"({_fmt_inr(abs(diff_p))}/pavan)"
            )
        if k22 and h22:
            diff_g = k22.per_gram_inr - h22.sell_per_gram_inr
            diff_p = k22.per_pavan_inr - h22.sell_per_pavan_inr
            cheaper = "Hanoi" if diff_g > 0 else "Kerala"
            lines.append(
                f"• 22K (Kerala vs Hanoi 916): {cheaper} cheaper by {_fmt_inr(abs(diff_g))}/g "
                f"({_fmt_inr(abs(diff_p))}/pavan)"
            )

    lines.append("")
    lines.append("_Note: 1 Pavan = 8 grams | 1 Chỉ = 3.75 grams | 1 Lượng = 37.5 grams_")
    return "\n".join(lines)
