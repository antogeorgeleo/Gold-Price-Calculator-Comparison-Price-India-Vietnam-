"""
LEO — Executive Export & Sharing Service (PDF, Excel, Telegram)
Created by Anto George Leo

Generates theme-aware luxury PDF comparison reports (ReportLab) and
formula-driven Excel workbooks (OpenPyXL) comparing Vietnam & India gold rates
across Chi (3.75g), Gram (1.00g), and Pavan (8.00g).
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

import openpyxl
import requests
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

EXPORT_DIR = Path(__file__).resolve().parent / "exports"


def _register_unicode_fonts() -> Tuple[str, str, bool]:
    """Register Unicode TTF fonts for ₹, ₫, and Vietnamese diacritics; fallback cleanly."""
    candidates = [
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
        (
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
        ),
        (
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ),
        (
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ),
    ]
    if "LeoSans" in pdfmetrics.getRegisteredFontNames():
        return "LeoSans", "LeoSans-Bold", True

    for reg_path, bold_path in candidates:
        if os.path.exists(reg_path) and os.path.exists(bold_path):
            try:
                pdfmetrics.registerFont(TTFont("LeoSans", reg_path))
                pdfmetrics.registerFont(TTFont("LeoSans-Bold", bold_path))
                return "LeoSans", "LeoSans-Bold", True
            except Exception:
                continue

    return "Helvetica", "Helvetica-Bold", False


def _safe_text(text: str, unicode_ok: bool) -> str:
    if unicode_ok:
        return text
    replacements = {
        "₹": "INR ",
        "₫": "VND",
        "Chỉ": "Chi",
        "Lượng": "Luong",
        "Cây": "Cay",
        "•": "-",
        "🇻🇳": "[VN]",
        "🇮🇳": "[IN]",
    }
    out = text
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out.encode("latin-1", "replace").decode("latin-1")


def _hex_to_rl_color(hex_str: str, fallback: str = "#D4AF37") -> colors.Color:
    try:
        return colors.HexColor(hex_str)
    except Exception:
        return colors.HexColor(fallback)


def _strip_hash(hex_str: str, fallback: str = "D4AF37") -> str:
    h = (hex_str or "").strip().lstrip("#")
    return h.upper() if len(h) == 6 else fallback


def generate_pdf_report(report: Dict[str, Any], save_to_disk: bool = True) -> Tuple[bytes, str]:
    """Create an executive luxury PDF comparison sheet and return (pdf_bytes, filename)."""
    font_reg, font_bold, unicode_ok = _register_unicode_fonts()
    S = lambda txt: _safe_text(str(txt), unicode_ok)

    theme = report.get("theme", {})
    accent_hex = theme.get("accent", "#D4AF37")
    accent_color = _hex_to_rl_color(accent_hex)
    dark_header_bg = colors.HexColor("#10141E")
    soft_tint_bg = colors.HexColor("#F8F6F1")
    border_gray = colors.HexColor("#DDD6C7")
    ink_dark = colors.HexColor("#171923")
    muted_gray = colors.HexColor("#5A6270")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=13 * mm,
        bottomMargin=13 * mm,
        title="LEO Gold Rate Comparison Report — Created by Anto George Leo",
        author="Anto George Leo",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "LeoTitle",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=19,
        leading=23,
        textColor=colors.HexColor("#FFFFFF"),
    )
    sub_style = ParagraphStyle(
        "LeoSub",
        parent=styles["Normal"],
        fontName=font_reg,
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#E2E8F0"),
    )
    section_heading = ParagraphStyle(
        "LeoSection",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=11,
        leading=14,
        textColor=ink_dark,
        spaceBefore=6,
        spaceAfter=4,
    )
    cell_style = ParagraphStyle(
        "LeoCell",
        parent=styles["Normal"],
        fontName=font_reg,
        fontSize=8.6,
        leading=11.5,
        textColor=ink_dark,
    )
    cell_bold = ParagraphStyle(
        "LeoCellBold",
        parent=cell_style,
        fontName=font_bold,
    )
    footer_style = ParagraphStyle(
        "LeoFooter",
        parent=styles["Normal"],
        fontName=font_reg,
        fontSize=8,
        leading=11,
        textColor=muted_gray,
        alignment=1,
    )

    story = []
    usable_width = A4[0] - 28 * mm

    # 1. Luxury Crest Header Table
    header_left = Paragraph(
        S(
            f"<b>LEO</b>  |  GOLD RATE INTELLIGENCE<br/>"
            f"<font size='9'>Vietnam &amp; India Bullion Comparison  •  {report['purity']}</font>"
        ),
        title_style,
    )
    header_right = Paragraph(
        S(
            f"<b>Created by Anto George Leo</b><br/>"
            f"Generated: {report['generated_at']}<br/>"
            f"Theme: {theme.get('name', 'Imperial Gold')}"
        ),
        sub_style,
    )
    header_tbl = Table([[header_left, header_right]], colWidths=[usable_width * 0.62, usable_width * 0.38])
    header_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), dark_header_bg),
                ("LINEBELOW", (0, 0), (-1, 0), 2.5, accent_color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
            ]
        )
    )
    story.append(header_tbl)
    story.append(Spacer(1, 5 * mm))

    # 2. Input Rates Summary Strip
    inp = report["inputs"]
    story.append(Paragraph(S("1. User Input Rates & Currency Parameters"), section_heading))

    vn_tax_note = f" (+{inp['vn_extra_pct']:g}% adj.)" if inp["vn_extra_pct"] > 0 else ""
    in_tax_note = f" (+{inp['in_extra_pct']:g}% adj.)" if inp["in_extra_pct"] > 0 else ""

    input_data = [
        [
            Paragraph(S("<b>Vietnam Input (Per 1 Chỉ = 3.75g)</b>"), cell_style),
            Paragraph(S("<b>India Input (Per 1 Gram = 1.00g)</b>"), cell_style),
            Paragraph(S("<b>Exchange Rate Applied</b>"), cell_style),
        ],
        [
            Paragraph(
                S(
                    f"<b>{inp['formatted']['vn_effective_chi_vnd']}</b>{vn_tax_note}<br/>"
                    f"<font size='7.5' color='#5A6270'>1 Lượng (10 Chỉ): {inp['formatted']['vn_luong_vnd']}</font>"
                ),
                cell_style,
            ),
            Paragraph(
                S(
                    f"<b>{inp['formatted']['in_effective_gram_inr']}</b>{in_tax_note}<br/>"
                    f"<font size='7.5' color='#5A6270'>1 Pavan (8g): {inp['formatted']['in_pavan_inr']}</font>"
                ),
                cell_style,
            ),
            Paragraph(
                S(
                    f"<b>{inp['formatted']['fx_display']}</b><br/>"
                    f"<font size='7.5' color='#5A6270'>{inp['formatted']['fx_inverse_display']}</font>"
                ),
                cell_style,
            ),
        ],
    ]
    input_tbl = Table(input_data, colWidths=[usable_width / 3.0] * 3)
    input_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), soft_tint_bg),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, border_gray),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, border_gray),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(input_tbl)
    story.append(Spacer(1, 5 * mm))

    # 3. Main Comparison Matrix (Chi, Gram, Pavan + Luong + Custom if customized)
    story.append(
        Paragraph(S("2. Side-by-Side Comparison in Chỉ, Gram & Pavan"), section_heading)
    )

    header_row = [
        Paragraph(S("<b>Weight Unit</b>"), ParagraphStyle("th", parent=cell_bold, textColor=colors.white)),
        Paragraph(S("<b>Vietnam Gold Price</b>"), ParagraphStyle("th", parent=cell_bold, textColor=colors.white)),
        Paragraph(S("<b>India Gold Price</b>"), ParagraphStyle("th", parent=cell_bold, textColor=colors.white)),
        Paragraph(S("<b>Price Difference</b>"), ParagraphStyle("th", parent=cell_bold, textColor=colors.white)),
        Paragraph(S("<b>Market Verdict</b>"), ParagraphStyle("th", parent=cell_bold, textColor=colors.white)),
    ]
    comp_rows = [header_row]

    display_units = list(report["units"]) + [report["by_key"]["luong"]]
    custom_row = report["by_key"]["custom"]
    if not (abs(custom_row["grams"] - 8.0) < 0.001 or abs(custom_row["grams"] - 3.75) < 0.001 or abs(custom_row["grams"] - 1.0) < 0.001):
        display_units.append(custom_row)

    for u in display_units:
        f = u["formatted"]
        verdict_color = (
            "#0F766E"
            if u["cheaper_country"] == "Vietnam"
            else ("#1D4ED8" if u["cheaper_country"] == "India" else "#4B5563")
        )
        comp_rows.append(
            [
                Paragraph(
                    S(f"<b>{u['label']}</b><br/><font size='7.3' color='#5A6270'>{u['subtitle']}</font>"),
                    cell_style,
                ),
                Paragraph(
                    S(f"<b>{f['vn_vnd']}</b><br/><font size='7.8' color='#475569'>≈ {f['vn_inr']}</font>"),
                    cell_style,
                ),
                Paragraph(
                    S(f"<b>{f['in_inr']}</b><br/><font size='7.8' color='#475569'>≈ {f['in_vnd']}</font>"),
                    cell_style,
                ),
                Paragraph(
                    S(f"<b>{f['abs_diff_inr']}</b><br/><font size='7.8' color='#475569'>{f['abs_diff_vnd']}</font>"),
                    cell_style,
                ),
                Paragraph(
                    S(f"<font color='{verdict_color}'><b>{u['verdict_badge']}</b></font>"),
                    cell_style,
                ),
            ]
        )

    col_widths = [
        usable_width * 0.23,
        usable_width * 0.21,
        usable_width * 0.21,
        usable_width * 0.18,
        usable_width * 0.17,
    ]
    comp_tbl = Table(comp_rows, colWidths=col_widths)
    tbl_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), dark_header_bg),
        ("LINEBELOW", (0, 0), (-1, 0), 1.8, accent_color),
        ("BOX", (0, 0), (-1, -1), 0.8, border_gray),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, border_gray),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for idx in range(1, len(comp_rows)):
        bg = colors.white if idx % 2 == 1 else soft_tint_bg
        tbl_styles.append(("BACKGROUND", (0, idx), (-1, idx), bg))
    comp_tbl.setStyle(TableStyle(tbl_styles))
    story.append(comp_tbl)
    story.append(Spacer(1, 5 * mm))

    # 4. Visual Bar Chart Drawing (Per 1 Pavan = 8g in INR)
    pavan = report["by_key"]["pavan"]
    max_val = max(pavan["vn_inr"], pavan["in_inr"], 1.0)
    bar_max_w = usable_width - 175
    vn_bar_w = max(12.0, (pavan["vn_inr"] / max_val) * bar_max_w)
    in_bar_w = max(12.0, (pavan["in_inr"] / max_val) * bar_max_w)

    drawing = Drawing(usable_width, 64)
    drawing.add(Rect(0, 0, usable_width, 64, fillColor=soft_tint_bg, strokeColor=border_gray, strokeWidth=0.7))
    drawing.add(
        String(
            10,
            49,
            S("Visual Benchmark — Cost per 1 Pavan (8.00 Grams / 2.133 Chỉ) in INR"),
            fontName=font_bold,
            fontSize=8.8,
            fillColor=ink_dark,
        )
    )
    # Vietnam Bar
    drawing.add(String(10, 30, S("Vietnam Rate:"), fontName=font_bold, fontSize=8.2, fillColor=ink_dark))
    drawing.add(Rect(85, 27, vn_bar_w, 11, fillColor=colors.HexColor("#DC2626"), strokeColor=None))
    drawing.add(
        String(
            90 + vn_bar_w,
            29,
            S(pavan["formatted"]["vn_inr"]),
            fontName=font_bold,
            fontSize=8.0,
            fillColor=ink_dark,
        )
    )
    # India Bar
    drawing.add(String(10, 11, S("India Rate:"), fontName=font_bold, fontSize=8.2, fillColor=ink_dark))
    drawing.add(Rect(85, 8, in_bar_w, 11, fillColor=accent_color, strokeColor=None))
    drawing.add(
        String(
            90 + in_bar_w,
            10,
            S(pavan["formatted"]["in_inr"]),
            fontName=font_bold,
            fontSize=8.0,
            fillColor=ink_dark,
        )
    )
    story.append(drawing)
    story.append(Spacer(1, 5 * mm))

    # 5. Verdict & Unit Reference Box
    summ = report["summary"]
    note_html = (
        f"<br/><b>Client / Reference Note:</b> {report['customer_note']}"
        if report.get("customer_note")
        else ""
    )
    verdict_box = Table(
        [
            [
                Paragraph(
                    S(
                        f"<b>EXECUTIVE VERDICT: {summ['headline'].replace('🇻🇳', '').replace('🇮🇳', '')}</b><br/>"
                        f"{summ['recommendation']}{note_html}<br/><br/>"
                        f"<font size='7.8' color='#5A6270'><b>Standard Bullion Conversions:</b>  "
                        f"1 Chỉ = 3.75 Grams = 0.46875 Pavan   •   "
                        f"1 Pavan = 8.00 Grams = 2.13333 Chỉ   •   "
                        f"1 Lượng = 10 Chỉ = 37.50 Grams</font>"
                    ),
                    cell_style,
                )
            ]
        ],
        colWidths=[usable_width],
    )
    verdict_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 1.2, accent_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("RIGHTPADDING", (0, 0), (-1, -1), 11),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(verdict_box)
    story.append(Spacer(1, 6 * mm))

    # 6. Signature Footer
    story.append(
        Paragraph(
            S("LEO Gold Rate Comparison Application  •  Created by Anto George Leo"),
            footer_style,
        )
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Leo_Gold_Comparison_{ts}.pdf"
    if save_to_disk:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        (EXPORT_DIR / "Leo_Gold_Comparison_Latest.pdf").write_bytes(pdf_bytes)

    return pdf_bytes, filename


def generate_excel_report(report: Dict[str, Any], save_to_disk: bool = True) -> Tuple[bytes, str]:
    """Create a multi-sheet, formula-powered Excel (.xlsx) comparison workbook."""
    wb = openpyxl.Workbook()
    wb.properties.title = "LEO Gold Rate Comparison — Vietnam & India"
    wb.properties.creator = "Anto George Leo"

    theme = report.get("theme", {})
    accent_hex = _strip_hash(theme.get("accent", "#D4AF37"), "D4AF37")
    dark_hex = "111622"
    soft_bg_hex = "FAF8F3"
    alt_row_hex = "F3EFE6"

    title_fill = PatternFill("solid", fgColor=dark_hex)
    accent_fill = PatternFill("solid", fgColor=accent_hex)
    sub_fill = PatternFill("solid", fgColor="1E2638")
    input_fill = PatternFill("solid", fgColor=soft_bg_hex)
    alt_fill = PatternFill("solid", fgColor=alt_row_hex)

    thin_side = Side(style="thin", color="D4CFC4")
    med_accent = Side(style="medium", color=accent_hex)
    cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    font_title = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="E2E8F0")
    font_sec = Font(name="Calibri", size=11, bold=True, color="111622")
    font_th = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_reg = Font(name="Calibri", size=10, color="1A202C")
    font_bold = Font(name="Calibri", size=10, bold=True, color="1A202C")
    font_input = Font(name="Calibri", size=10, bold=True, color="0F4C81")

    # ================= SHEET 1: Gold Comparison =================
    ws = wb.active
    ws.title = "Gold Comparison (Chi-g-Pavan)"
    ws.views.sheetView[0].showGridLines = True

    ws.merge_cells("A1:I1")
    ws["A1"] = "LEO — VIETNAM & INDIA GOLD RATE COMPARISON SUITE"
    ws["A1"].font = font_title
    ws["A1"].fill = title_fill
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 30

    ws.merge_cells("A2:I2")
    ws["A2"] = (
        f"Created by Anto George Leo  |  Generated: {report['generated_at']}  |  "
        f"Purity: {report['purity']}  |  Theme: {theme.get('name', 'Imperial Gold')}"
    )
    ws["A2"].font = font_subtitle
    ws["A2"].fill = sub_fill
    ws["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws["A2"].border = Border(bottom=med_accent)
    ws.row_dimensions[2].height = 20

    # Input Parameters Block (Rows 4 to 9)
    ws["A4"] = "1. INPUT PARAMETERS (EDITABLE — FORMULAS RECALCULATE AUTOMATICALLY)"
    ws["A4"].font = font_sec

    inp = report["inputs"]
    params = [
        ("Vietnam Gold Price (per 1 Chỉ = 3.75g) [VND]", inp["vn_price_per_chi_vnd"], '#,##0 "₫"'),
        ("India Gold Price (per 1 Gram = 1.00g) [INR]", inp["in_price_per_gram_inr"], '"₹"#,##0.00'),
        ("Exchange Rate (1 INR in VND)", inp["fx_inr_to_vnd"], '#,##0.00 "₫"'),
        ("Vietnam Tax / Making Adjustment (%)", inp["vn_extra_pct"] / 100.0, "0.00%"),
        ("India GST / Making Adjustment (%)", inp["in_extra_pct"] / 100.0, "0.00%"),
    ]
    for offset, (label, val, num_fmt) in enumerate(params, start=5):
        ws.merge_cells(start_row=offset, start_column=1, end_row=offset, end_column=2)
        ws.cell(row=offset, column=1, value=label).font = font_reg
        ws.cell(row=offset, column=1).fill = input_fill
        ws.cell(row=offset, column=1).border = cell_border
        ws.cell(row=offset, column=2).border = cell_border

        val_cell = ws.cell(row=offset, column=3, value=val)
        val_cell.font = font_input
        val_cell.number_format = num_fmt
        val_cell.fill = PatternFill("solid", fgColor="FFFDF7")
        val_cell.border = cell_border
        val_cell.alignment = Alignment(horizontal="right", vertical="center")
        ws.row_dimensions[offset].height = 20

    # Comparison Matrix Header (Row 11-12)
    ws["A11"] = "2. COMPLETE COMPARISON IN CHỈ, GRAM & PAVAN"
    ws["A11"].font = font_sec

    headers = [
        "Weight Unit",
        "Weight (Grams)",
        "Vietnam Price (VND ₫)",
        "Vietnam Price (INR ₹)",
        "India Price (INR ₹)",
        "India Price (VND ₫)",
        "Difference (INR ₹)",
        "Difference (VND ₫)",
        "Spread % & Verdict",
    ]
    header_row_idx = 12
    ws.row_dimensions[header_row_idx].height = 25
    for col_idx, h_text in enumerate(headers, start=1):
        c = ws.cell(row=header_row_idx, column=col_idx, value=h_text)
        c.font = font_th
        c.fill = title_fill
        c.alignment = Alignment(horizontal="center" if col_idx > 1 else "left", vertical="center", wrap_text=True)
        c.border = Border(bottom=med_accent, left=thin_side, right=thin_side, top=thin_side)

    custom_row_data = report["by_key"]["custom"]
    unit_rows_spec = [
        ("1 Chỉ (Vietnam Standard)", 3.75),
        ("1 Gram (Metric Standard)", 1.00),
        ("1 Pavan / Sovereign (India Standard)", 8.00),
        ("1 Lượng / Cây (10 Chỉ)", 37.50),
        (f"Custom: {custom_row_data['label']}", custom_row_data["grams"]),
    ]

    for idx, (u_name, grams_val) in enumerate(unit_rows_spec, start=13):
        ws.row_dimensions[idx].height = 22
        row_fill = PatternFill("solid", fgColor="FFFFFF") if idx % 2 == 1 else alt_fill

        c_unit = ws.cell(row=idx, column=1, value=u_name)
        c_unit.font = font_bold

        c_grams = ws.cell(row=idx, column=2, value=grams_val)
        c_grams.font = font_reg
        c_grams.number_format = "0.00"

        # Formulas referencing $C$5 (VN Chi VND), $C$6 (IN Gram INR), $C$7 (FX), $C$8 (VN %), $C$9 (IN %)
        c_vn_vnd = ws.cell(row=idx, column=3, value=f"=($C$5*(1+$C$8)/3.75)*B{idx}")
        c_vn_vnd.number_format = '#,##0 "₫"'
        c_vn_vnd.font = font_bold

        c_vn_inr = ws.cell(row=idx, column=4, value=f"=C{idx}/$C$7")
        c_vn_inr.number_format = '"₹"#,##0.00'
        c_vn_inr.font = font_reg

        c_in_inr = ws.cell(row=idx, column=5, value=f"=($C$6*(1+$C$9))*B{idx}")
        c_in_inr.number_format = '"₹"#,##0.00'
        c_in_inr.font = font_bold

        c_in_vnd = ws.cell(row=idx, column=6, value=f"=E{idx}*$C$7")
        c_in_vnd.number_format = '#,##0 "₫"'
        c_in_vnd.font = font_reg

        c_diff_inr = ws.cell(row=idx, column=7, value=f"=ABS(D{idx}-E{idx})")
        c_diff_inr.number_format = '"₹"#,##0.00'
        c_diff_inr.font = font_bold

        c_diff_vnd = ws.cell(row=idx, column=8, value=f"=ABS(C{idx}-F{idx})")
        c_diff_vnd.number_format = '#,##0 "₫"'
        c_diff_vnd.font = font_reg

        c_verdict = ws.cell(
            row=idx,
            column=9,
            value=(
                f'=IF(ABS(D{idx}-E{idx})<0.01,"Equal Parity",'
                f'IF(D{idx}<E{idx},"Vietnam Cheaper ("&TEXT(G{idx}/D{idx},"0.00%")&")",'
                f'"India Cheaper ("&TEXT(G{idx}/E{idx},"0.00%")&")"))'
            ),
        )
        c_verdict.font = font_bold
        c_verdict.alignment = Alignment(horizontal="center", vertical="center")

        for col_i in range(1, 10):
            cell_obj = ws.cell(row=idx, column=col_i)
            cell_obj.fill = row_fill
            cell_obj.border = cell_border
            if col_i in (2, 3, 4, 5, 6, 7, 8):
                cell_obj.alignment = Alignment(horizontal="right", vertical="center")

    # Summary / Signature Footer
    footer_row = 19
    ws.merge_cells(start_row=footer_row, start_column=1, end_row=footer_row, end_column=9)
    ws.cell(
        row=footer_row,
        column=1,
        value=f"Executive Summary: {report['summary']['headline']} — {report['summary']['recommendation']}",
    ).font = font_bold
    ws.cell(row=footer_row, column=1).fill = input_fill
    ws.cell(row=footer_row, column=1).border = cell_border
    ws.row_dimensions[footer_row].height = 24

    sig_row = 21
    ws.merge_cells(start_row=sig_row, start_column=1, end_row=sig_row, end_column=9)
    ws.cell(
        row=sig_row,
        column=1,
        value="Application: LEO Gold Rate Comparison Suite  •  Created by Anto George Leo",
    ).font = Font(name="Calibri", size=9.5, italic=True, color="5A6270")

    col_widths = [32, 15, 22, 20, 20, 22, 20, 22, 28]
    for col_i, width in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(col_i)].width = width

    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    # ================= SHEET 2: Unit Conversion Reference =================
    ws2 = wb.create_sheet(title="Unit Conversion Guide")
    ws2.merge_cells("A1:E1")
    ws2["A1"] = "LEO — GOLD WEIGHT CONVERSION REFERENCE (CHỈ • GRAM • PAVAN • LƯỢNG)"
    ws2["A1"].font = font_title
    ws2["A1"].fill = title_fill
    ws2.row_dimensions[1].height = 28

    ref_headers = ["Unit Name", "In Grams (g)", "In Chỉ (VN)", "In Pavan (IN)", "In Lượng (VN)"]
    for ci, rh in enumerate(ref_headers, start=1):
        cell = ws2.cell(row=3, column=ci, value=rh)
        cell.font = font_th
        cell.fill = accent_fill if accent_hex != "FFFFFF" else title_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = cell_border
    ws2.row_dimensions[3].height = 22

    ref_rows = [
        ("1 Chỉ (Vietnam Mace)", 3.75, 1.0, 3.75 / 8.0, 0.1),
        ("1 Gram (Metric)", 1.0, 1.0 / 3.75, 1.0 / 8.0, 1.0 / 37.5),
        ("1 Pavan / Sovereign (India)", 8.0, 8.0 / 3.75, 1.0, 8.0 / 37.5),
        ("1 Lượng / Cây (Vietnam Tael)", 37.5, 10.0, 37.5 / 8.0, 1.0),
    ]
    for r_idx, r_vals in enumerate(ref_rows, start=4):
        ws2.row_dimensions[r_idx].height = 20
        for c_idx, v in enumerate(r_vals, start=1):
            c = ws2.cell(row=r_idx, column=c_idx, value=v)
            c.font = font_bold if c_idx == 1 else font_reg
            c.border = cell_border
            if c_idx > 1:
                c.number_format = "0.0000"
                c.alignment = Alignment(horizontal="right", vertical="center")

    ws2["A10"] = "LEO Gold Intelligence Suite • Created by Anto George Leo"
    ws2["A10"].font = Font(name="Calibri", size=9.5, italic=True, color="5A6270")
    for ci, w in enumerate([30, 16, 16, 16, 16], start=1):
        ws2.column_dimensions[get_column_letter(ci)].width = w

    out_buf = io.BytesIO()
    wb.save(out_buf)
    xlsx_bytes = out_buf.getvalue()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Leo_Gold_Comparison_{ts}.xlsx"
    if save_to_disk:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        (EXPORT_DIR / "Leo_Gold_Comparison_Latest.xlsx").write_bytes(xlsx_bytes)

    return xlsx_bytes, filename


def send_via_telegram_bot(
    bot_token: str,
    chat_id: str,
    report: Dict[str, Any],
    attach_pdf: bool = True,
) -> Dict[str, Any]:
    """Send the formatted comparison text (and optional PDF report) via Telegram Bot API."""
    token = (bot_token or "").strip()
    cid = (chat_id or "").strip()
    if not token or not cid:
        return {"ok": False, "error": "Please enter both Telegram Bot Token and Chat ID."}

    text_msg = report["share_messages"]["telegram"]
    base_url = f"https://api.telegram.org/bot{token}"

    try:
        msg_resp = requests.post(
            f"{base_url}/sendMessage",
            json={"chat_id": cid, "text": text_msg},
            timeout=10,
        )
        msg_data = msg_resp.json()
        if not msg_data.get("ok"):
            return {
                "ok": False,
                "error": msg_data.get("description", "Telegram API rejected the request."),
            }

        if attach_pdf:
            pdf_bytes, pdf_name = generate_pdf_report(report, save_to_disk=False)
            requests.post(
                f"{base_url}/sendDocument",
                data={"chat_id": cid, "caption": "LEO Gold Comparison PDF — Created by Anto George Leo"},
                files={"document": (pdf_name, pdf_bytes, "application/pdf")},
                timeout=15,
            )

        return {"ok": True, "message": "Comparison report & PDF sent successfully via Telegram Bot!"}
    except Exception as exc:
        return {"ok": False, "error": f"Connection error: {exc}"}
