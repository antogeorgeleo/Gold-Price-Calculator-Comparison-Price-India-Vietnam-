"""Professional A4 PDF report generator for Kerala & Hanoi Gold Prices."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from fetcher import GoldMarketSnapshot

APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))


def _register_fonts() -> tuple[str, str]:
    """Register Unicode TTF fonts supporting ₹, ₫, and Vietnamese diacritics."""
    candidates = [
        (RESOURCE_DIR / "fonts" / "DejaVuSans.ttf", RESOURCE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        (APP_DIR / "fonts" / "DejaVuSans.ttf", APP_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
        (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
        (Path("C:/Windows/Fonts/segoeui.ttf"), Path("C:/Windows/Fonts/segoeuib.ttf")),
        (
            Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ),
    ]
    for reg_path, bold_path in candidates:
        if reg_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("AppFont", str(reg_path)))
                if bold_path.exists():
                    pdfmetrics.registerFont(TTFont("AppFont-Bold", str(bold_path)))
                    registerFontFamily(
                        "AppFont",
                        normal="AppFont",
                        bold="AppFont-Bold",
                        italic="AppFont",
                        boldItalic="AppFont-Bold",
                    )
                    return "AppFont", "AppFont-Bold"
                registerFontFamily(
                    "AppFont",
                    normal="AppFont",
                    bold="AppFont",
                    italic="AppFont",
                    boldItalic="AppFont",
                )
                return "AppFont", "AppFont"
            except Exception:
                continue
    return "Helvetica", "Helvetica-Bold"


def generate_gold_pdf(snapshot: GoldMarketSnapshot, output_path: str | Path | None = None) -> Path:
    """Generate a styled PDF report and return its Path."""
    font_reg, font_bold = _register_fonts()
    use_unicode_symbols = font_reg != "Helvetica"

    def inr(val: float, decimals: int = 0) -> str:
        sym = "₹" if use_unicode_symbols else "INR "
        return f"{sym}{val:,.{decimals}f}"

    def vnd(val: float) -> str:
        sym = "₫" if use_unicode_symbols else "VND"
        return f"{val:,.0f} {sym}"

    if output_path is None:
        reports_dir = APP_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        fname = f"Gold_Price_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        out_path = reports_dir / fname
    else:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Kerala & Hanoi Live Gold Price Report",
    )

    styles = getSampleStyleSheet()
    navy = colors.HexColor("#0F172A")
    slate = colors.HexColor("#334155")
    gold_dark = colors.HexColor("#9A6F04")
    gold_bg = colors.HexColor("#FEF8E7")
    gold_border = colors.HexColor("#E5C158")
    row_alt = colors.HexColor("#F8FAFC")
    green_txt = colors.HexColor("#15803D")
    red_txt = colors.HexColor("#B91C1C")

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=17,
        leading=22,
        textColor=colors.white,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        fontName=font_reg,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#E2E8F0"),
    )
    section_style = ParagraphStyle(
        "SectionCustom",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=11.5,
        leading=15,
        textColor=navy,
        spaceBefore=6,
        spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "MetaCustom",
        parent=styles["Normal"],
        fontName=font_reg,
        fontSize=8.5,
        leading=12,
        textColor=slate,
    )
    cell_style = ParagraphStyle(
        "CellCustom",
        parent=styles["Normal"],
        fontName=font_reg,
        fontSize=8.5,
        leading=11,
        textColor=navy,
    )
    cell_bold = ParagraphStyle(
        "CellBoldCustom",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=8.5,
        leading=11,
        textColor=navy,
    )

    elements = []

    # Header Banner
    banner_data = [
        [
            Paragraph("KERALA & HANOI LIVE GOLD PRICE REPORT", title_style),
        ],
        [
            Paragraph(
                f"Generated: {snapshot.fetched_at}   |   "
                f"Live FX: 1 INR = {snapshot.fx_inr_to_vnd:,.2f} VND  (1 VND = {inr(snapshot.fx_vnd_to_inr, 6)})   |   "
                f"Units: Gram & Pavan (8g)",
                subtitle_style,
            )
        ],
    ]
    banner = Table(banner_data, colWidths=[182 * mm])
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), navy),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (0, 0), 10),
                ("BOTTOMPADDING", (0, 1), (0, 1), 10),
                ("LINEBELOW", (0, 1), (0, 1), 2.5, gold_border),
            ]
        )
    )
    elements.append(banner)
    elements.append(Spacer(1, 7))

    # Highlight Summary Cards
    k22 = snapshot.get_kerala("22K")
    k24 = snapshot.get_kerala("24K")
    h_sjc = snapshot.get_hanoi("SJC")
    h22 = snapshot.get_hanoi("22K")

    card_cells = [
        [
            Paragraph(
                f"<b>Kerala 22K (916)</b><br/>"
                f"1g: {inr(k22.per_gram_inr) if k22 else 'N/A'}<br/>"
                f"<b>1 Pavan (8g): {inr(k22.per_pavan_inr) if k22 else 'N/A'}</b>",
                cell_style,
            ),
            Paragraph(
                f"<b>Kerala 24K (999)</b><br/>"
                f"1g: {inr(k24.per_gram_inr) if k24 else 'N/A'}<br/>"
                f"<b>1 Pavan (8g): {inr(k24.per_pavan_inr) if k24 else 'N/A'}</b>",
                cell_style,
            ),
            Paragraph(
                f"<b>Hanoi SJC 24K (Sell)</b><br/>"
                f"1g: {vnd(h_sjc.sell_per_gram_vnd) if h_sjc else 'N/A'} ({inr(h_sjc.sell_per_gram_inr) if h_sjc else ''})<br/>"
                f"<b>1 Pavan: {vnd(h_sjc.sell_per_pavan_vnd) if h_sjc else 'N/A'} ({inr(h_sjc.sell_per_pavan_inr) if h_sjc else ''})</b>",
                cell_style,
            ),
            Paragraph(
                f"<b>Hanoi 22K 916 (Sell)</b><br/>"
                f"1g: {vnd(h22.sell_per_gram_vnd) if h22 else 'N/A'} ({inr(h22.sell_per_gram_inr) if h22 else ''})<br/>"
                f"<b>1 Pavan: {vnd(h22.sell_per_pavan_vnd) if h22 else 'N/A'} ({inr(h22.sell_per_pavan_inr) if h22 else ''})</b>",
                cell_style,
            ),
        ]
    ]
    cards = Table(card_cells, colWidths=[44 * mm, 44 * mm, 47 * mm, 47 * mm])
    cards.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), gold_bg),
                ("BOX", (0, 0), (0, 0), 0.8, gold_border),
                ("BOX", (1, 0), (1, 0), 0.8, gold_border),
                ("BOX", (2, 0), (2, 0), 0.8, gold_border),
                ("BOX", (3, 0), (3, 0), 0.8, gold_border),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elements.append(cards)
    elements.append(Spacer(1, 8))

    # Section 1: Kerala Gold Rates
    elements.append(Paragraph("1. Kerala, India Gold Rates (INR)", section_style))
    elements.append(
        Paragraph(f"Source: {snapshot.kerala_source}  |  Market Timestamp: {snapshot.kerala_updated}", meta_style)
    )
    elements.append(Spacer(1, 3))

    k_rows = [["Purity / Karat", "1 Gram (INR)", "1 Pavan / 8g (INR)", "10 Grams (INR)", "Daily Change (1g / Pavan)"]]
    for r in snapshot.kerala_rates:
        if r.change_gram_inr > 0:
            chg_str = f"+{inr(r.change_gram_inr)} / +{inr(r.change_pavan_inr)}"
        elif r.change_gram_inr < 0:
            chg_str = f"-{inr(abs(r.change_gram_inr))} / -{inr(abs(r.change_pavan_inr))}"
        else:
            chg_str = "No change"
        k_rows.append(
            [
                Paragraph(f"<b>{r.purity}</b>", cell_bold),
                inr(r.per_gram_inr),
                Paragraph(f"<b>{inr(r.per_pavan_inr)}</b>", cell_bold),
                inr(r.per_10g_inr),
                chg_str,
            ]
        )

    k_table = Table(k_rows, colWidths=[32 * mm, 34 * mm, 40 * mm, 34 * mm, 42 * mm])
    k_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), font_bold),
                ("FONTNAME", (0, 1), (-1, -1), font_reg),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BACKGROUND", (0, 0), (-1, 0), navy),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, row_alt]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(k_table)
    elements.append(Spacer(1, 9))

    # Section 2: Hanoi, Vietnam Gold Rates
    elements.append(Paragraph("2. Hanoi, Vietnam Gold Rates (VND & Converted INR)", section_style))
    elements.append(
        Paragraph(
            f"Source: {snapshot.hanoi_source}  |  Market Timestamp: {snapshot.hanoi_updated}  |  "
            "Local units: 1 Chỉ = 3.75g, 1 Lượng = 37.5g",
            meta_style,
        )
    )
    elements.append(Spacer(1, 3))

    h_rows = [
        [
            "Gold Type (Hanoi)",
            "Side",
            "1 Gram (VND)",
            "1 Pavan 8g (VND)",
            "1 Gram (INR)",
            "1 Pavan 8g (INR)",
            "1 Chỉ 3.75g (VND)",
        ]
    ]
    for r in snapshot.hanoi_rates:
        h_rows.append(
            [
                Paragraph(f"<b>{r.name_en}</b><br/><font size='7' color='#64748B'>{r.name_vi}</font>", cell_style),
                "Sell\nBuy",
                f"{vnd(r.sell_per_gram_vnd)}\n{vnd(r.buy_per_gram_vnd)}",
                Paragraph(
                    f"<b>{vnd(r.sell_per_pavan_vnd)}</b><br/>{vnd(r.buy_per_pavan_vnd)}",
                    cell_style,
                ),
                f"{inr(r.sell_per_gram_inr)}\n{inr(r.buy_per_gram_inr)}",
                Paragraph(
                    f"<b>{inr(r.sell_per_pavan_inr)}</b><br/>{inr(r.buy_per_pavan_inr)}",
                    cell_style,
                ),
                f"{vnd(r.sell_per_chi_vnd)}\n{vnd(r.buy_per_chi_vnd)}",
            ]
        )

    h_table = Table(h_rows, colWidths=[38 * mm, 12 * mm, 26 * mm, 30 * mm, 24 * mm, 26 * mm, 26 * mm])
    h_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), font_bold),
                ("FONTNAME", (0, 1), (-1, -1), font_reg),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), navy),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, row_alt]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(h_table)
    elements.append(Spacer(1, 9))

    # Section 3: Comparison Table (Kerala vs Hanoi in INR)
    elements.append(Paragraph("3. Kerala vs Hanoi Price Comparison (INR Equivalent)", section_style))
    comp_rows = [
        ["Comparison Pair", "Kerala (1g / 1 Pavan)", "Hanoi Sell (1g / 1 Pavan)", "Difference (1g / 1 Pavan)", "Cheaper Market"]
    ]

    pairs = []
    if k24 and h_sjc:
        pairs.append(("24K: Kerala vs Hanoi SJC", k24.per_gram_inr, k24.per_pavan_inr, h_sjc.sell_per_gram_inr, h_sjc.sell_per_pavan_inr))
    h_n24 = snapshot.get_hanoi("N24K")
    if k24 and h_n24:
        pairs.append(("24K: Kerala vs Hanoi PNJ Ring", k24.per_gram_inr, k24.per_pavan_inr, h_n24.sell_per_gram_inr, h_n24.sell_per_pavan_inr))
    if k22 and h22:
        pairs.append(("22K (916): Kerala vs Hanoi", k22.per_gram_inr, k22.per_pavan_inr, h22.sell_per_gram_inr, h22.sell_per_pavan_inr))

    for label, kg, kp, hg, hp in pairs:
        diff_g = kg - hg
        diff_p = kp - hp
        pct = (abs(diff_g) / kg * 100.0) if kg else 0.0
        cheaper = f"Hanoi (-{pct:.2f}%)" if diff_g > 0 else f"Kerala (-{pct:.2f}%)"
        color_tag = "#15803D" if diff_g > 0 else "#1D4ED8"
        comp_rows.append(
            [
                Paragraph(f"<b>{label}</b>", cell_style),
                f"{inr(kg)} / {inr(kp)}",
                f"{inr(hg)} / {inr(hp)}",
                f"{inr(abs(diff_g))} / {inr(abs(diff_p))}",
                Paragraph(f"<font color='{color_tag}'><b>{cheaper}</b></font>", cell_style),
            ]
        )

    c_table = Table(comp_rows, colWidths=[45 * mm, 38 * mm, 38 * mm, 35 * mm, 26 * mm])
    c_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), font_bold),
                ("FONTNAME", (0, 1), (-1, -1), font_reg),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), gold_dark),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, row_alt]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ALIGN", (1, 0), (3, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(c_table)
    elements.append(Spacer(1, 10))

    # Footer Notes
    elements.append(
        Paragraph(
            f"Notes: 1 Pavan (Sovereign) = 8.00 grams | 1 Chỉ = 3.75 grams | 1 Lượng (Cây) = 37.50 grams. "
            f"FX Source: {snapshot.fx_source}. Rates exclude local jewellery making charges, GST (India), or shop premiums.",
            meta_style,
        )
    )

    doc.build(elements)
    return out_path
