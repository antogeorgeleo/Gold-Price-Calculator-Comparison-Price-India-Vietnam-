"""Desktop GUI Application: Real-Time Kerala & Hanoi Gold Price Tracker."""

from __future__ import annotations

import os
import platform
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from config import load_config, save_config
from fetcher import GRAMS_PER_CHI, GRAMS_PER_PAVAN, GoldMarketSnapshot, fetch_all_market_data
from formatter import format_messenger_report
from notifiers import (
    detect_telegram_chat_id,
    open_whatsapp_qr_login,
    send_telegram_report,
    send_whatsapp_report,
    test_telegram_bot,
)
from pdf_generator import generate_gold_pdf


class GoldTrackerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Kerala & Hanoi Live Gold Tracker (Gram & Pavan)")
        self.root.geometry("1160x780")
        self.root.minsize(980, 680)
        self.root.configure(bg="#F1F5F9")

        self.config = load_config()
        self.snapshot: GoldMarketSnapshot | None = None
        self.last_pdf_path: Path | None = None
        self._is_busy = False
        self._after_id: str | None = None

        self._setup_styles()
        self._build_ui()
        self._load_settings_into_vars()

        # Initial fetch shortly after window appears
        self.root.after(200, self.refresh_data)

    def _setup_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TNotebook", background="#F1F5F9", borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 7),
            background="#E2E8F0",
            foreground="#1E293B",
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#0F172A")],
            foreground=[("selected", "#FBBF24")],
        )

        style.configure(
            "Gold.Treeview",
            font=("Segoe UI", 10),
            rowheight=28,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#0F172A",
        )
        style.configure(
            "Gold.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#0F172A",
            foreground="#FFFFFF",
            padding=(6, 6),
        )
        style.map("Gold.Treeview.Heading", background=[("active", "#1E293B")])

    def _build_ui(self) -> None:
        # ---- Top Banner ----
        header = tk.Frame(self.root, bg="#0F172A", height=66)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg="#0F172A")
        title_frame.pack(side="left", padx=16, pady=8)

        tk.Label(
            title_frame,
            text="KERALA & HANOI LIVE GOLD TRACKER",
            font=("Segoe UI", 15, "bold"),
            fg="#FBBF24",
            bg="#0F172A",
        ).pack(anchor="w")

        self.lbl_subtitle = tk.Label(
            title_frame,
            text="Real-time INR & VND prices in Gram & Pavan (8g)  |  Loading live markets...",
            font=("Segoe UI", 9),
            fg="#CBD5E1",
            bg="#0F172A",
        )
        self.lbl_subtitle.pack(anchor="w")

        controls = tk.Frame(header, bg="#0F172A")
        controls.pack(side="right", padx=16)

        self.var_auto_refresh = tk.BooleanVar(value=bool(self.config.get("auto_refresh_enabled", True)))
        tk.Checkbutton(
            controls,
            text="Auto-Refresh",
            variable=self.var_auto_refresh,
            command=self._toggle_auto_refresh,
            bg="#0F172A",
            fg="#E2E8F0",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#FBBF24",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 10))

        self.btn_refresh = tk.Button(
            controls,
            text="Refresh Live Prices",
            command=self.refresh_data,
            bg="#D97706",
            fg="#FFFFFF",
            activebackground="#B45309",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
        )
        self.btn_refresh.pack(side="left")

        # ---- 4 Summary KPI Cards ----
        cards_row = tk.Frame(self.root, bg="#F1F5F9")
        cards_row.pack(fill="x", padx=14, pady=(12, 8))
        for i in range(4):
            cards_row.columnconfigure(i, weight=1, uniform="kpi")

        self.card_k22 = self._make_kpi_card(cards_row, 0, "KERALA 22K (916)", "#92400E", "#FEF3C7")
        self.card_k24 = self._make_kpi_card(cards_row, 1, "KERALA 24K (999)", "#1E3A8A", "#DBEAFE")
        self.card_hsjc = self._make_kpi_card(cards_row, 2, "HANOI SJC 24K (SELL)", "#065F46", "#D1FAE5")
        self.card_h22 = self._make_kpi_card(cards_row, 3, "HANOI 22K 916 (SELL)", "#5B21B6", "#EDE9FE")

        # ---- Main Notebook Tabs ----
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(2, 8))

        self.tab_rates = tk.Frame(self.notebook, bg="#F8FAFC")
        self.tab_calc = tk.Frame(self.notebook, bg="#F8FAFC")
        self.tab_export = tk.Frame(self.notebook, bg="#F8FAFC")
        self.tab_settings = tk.Frame(self.notebook, bg="#F8FAFC")

        self.notebook.add(self.tab_rates, text="  Live Rates (Gram & Pavan)  ")
        self.notebook.add(self.tab_calc, text="  Gram / Pavan Calculator  ")
        self.notebook.add(self.tab_export, text="  PDF, Telegram & WhatsApp  ")
        self.notebook.add(self.tab_settings, text="  Settings  ")

        self._build_rates_tab()
        self._build_calc_tab()
        self._build_export_tab()
        self._build_settings_tab()

        # ---- Bottom Action + Status Bar ----
        bottom = tk.Frame(self.root, bg="#0F172A", height=36)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)

        self.lbl_status = tk.Label(
            bottom,
            text="Ready.",
            font=("Segoe UI", 9),
            fg="#E2E8F0",
            bg="#0F172A",
            anchor="w",
        )
        self.lbl_status.pack(side="left", padx=14, fill="x", expand=True)

        tk.Button(
            bottom,
            text="Quick PDF",
            command=self.action_generate_pdf,
            bg="#334155",
            fg="#F8FAFC",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=10,
            cursor="hand2",
        ).pack(side="right", padx=4, pady=5)

        tk.Button(
            bottom,
            text="Send Telegram",
            command=self.action_send_telegram,
            bg="#0284C7",
            fg="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=10,
            cursor="hand2",
        ).pack(side="right", padx=4, pady=5)

        tk.Button(
            bottom,
            text="Send WhatsApp",
            command=self.action_send_whatsapp,
            bg="#16A34A",
            fg="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=10,
            cursor="hand2",
        ).pack(side="right", padx=4, pady=5)

    def _make_kpi_card(
        self, parent: tk.Frame, col: int, title: str, accent: str, badge_bg: str
    ) -> dict[str, tk.Label]:
        card = tk.Frame(parent, bg="#FFFFFF", highlightbackground="#CBD5E1", highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew", padx=5)

        top_bar = tk.Frame(card, bg=badge_bg, height=26)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        tk.Label(top_bar, text=title, font=("Segoe UI", 8, "bold"), fg=accent, bg=badge_bg).pack(
            side="left", padx=10, pady=3
        )

        body = tk.Frame(card, bg="#FFFFFF")
        body.pack(fill="both", expand=True, padx=10, pady=8)

        lbl_pavan = tk.Label(body, text="Pavan: --", font=("Segoe UI", 13, "bold"), fg="#0F172A", bg="#FFFFFF", anchor="w")
        lbl_pavan.pack(fill="x")

        lbl_gram = tk.Label(body, text="Gram: --", font=("Segoe UI", 10), fg="#334155", bg="#FFFFFF", anchor="w")
        lbl_gram.pack(fill="x", pady=(2, 0))

        lbl_sub = tk.Label(body, text="--", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF", anchor="w")
        lbl_sub.pack(fill="x", pady=(3, 0))

        return {"pavan": lbl_pavan, "gram": lbl_gram, "sub": lbl_sub}

    def _build_rates_tab(self) -> None:
        # Kerala Section
        k_header = tk.Frame(self.tab_rates, bg="#F8FAFC")
        k_header.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(
            k_header,
            text="Kerala, India Gold Rates (INR)",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#F8FAFC",
        ).pack(side="left")
        self.lbl_kerala_meta = tk.Label(
            k_header, text="", font=("Segoe UI", 9), fg="#475569", bg="#F8FAFC"
        )
        self.lbl_kerala_meta.pack(side="right")

        k_cols = ("purity", "gram", "pavan", "ten_g", "chg")
        self.tree_kerala = ttk.Treeview(
            self.tab_rates, columns=k_cols, show="headings", height=3, style="Gold.Treeview"
        )
        for cid, heading, w, anch in [
            ("purity", "Purity / Karat", 160, "w"),
            ("gram", "1 Gram (INR)", 170, "e"),
            ("pavan", "1 Pavan / 8g (INR)", 200, "e"),
            ("ten_g", "10 Grams (INR)", 170, "e"),
            ("chg", "Daily Change (1g / Pavan)", 240, "e"),
        ]:
            self.tree_kerala.heading(cid, text=heading)
            self.tree_kerala.column(cid, width=w, anchor=anch)
        self.tree_kerala.pack(fill="x", padx=12, pady=(0, 10))

        # Hanoi Section
        h_header = tk.Frame(self.tab_rates, bg="#F8FAFC")
        h_header.pack(fill="x", padx=12, pady=(4, 4))
        tk.Label(
            h_header,
            text="Hanoi, Vietnam Gold Rates (VND & INR Equivalent)",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#F8FAFC",
        ).pack(side="left")
        self.lbl_hanoi_meta = tk.Label(
            h_header, text="", font=("Segoe UI", 9), fg="#475569", bg="#F8FAFC"
        )
        self.lbl_hanoi_meta.pack(side="right")

        h_cols = ("name", "karat", "sell_g_vnd", "sell_p_vnd", "sell_g_inr", "sell_p_inr", "buy_p_vnd", "chi_vnd")
        self.tree_hanoi = ttk.Treeview(
            self.tab_rates, columns=h_cols, show="headings", height=6, style="Gold.Treeview"
        )
        for cid, heading, w, anch in [
            ("name", "Gold Type (Hanoi)", 175, "w"),
            ("karat", "Purity", 95, "center"),
            ("sell_g_vnd", "Sell 1g (VND)", 125, "e"),
            ("sell_p_vnd", "Sell 1 Pavan (VND)", 145, "e"),
            ("sell_g_inr", "Sell 1g (INR)", 110, "e"),
            ("sell_p_inr", "Sell 1 Pavan (INR)", 135, "e"),
            ("buy_p_vnd", "Buy 1 Pavan (VND)", 145, "e"),
            ("chi_vnd", "Sell 1 Chỉ 3.75g (VND)", 145, "e"),
        ]:
            self.tree_hanoi.heading(cid, text=heading)
            self.tree_hanoi.column(cid, width=w, anchor=anch)
        self.tree_hanoi.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Comparison Bar
        comp_box = tk.Frame(self.tab_rates, bg="#FEF8E7", highlightbackground="#E5C158", highlightthickness=1)
        comp_box.pack(fill="x", padx=12, pady=(0, 10))
        self.lbl_comparison = tk.Label(
            comp_box,
            text="Kerala vs Hanoi comparison will appear after fetching live prices...",
            font=("Segoe UI", 9, "bold"),
            fg="#78350F",
            bg="#FEF8E7",
            justify="left",
            anchor="w",
            padx=12,
            pady=8,
        )
        self.lbl_comparison.pack(fill="x")

    def _build_calc_tab(self) -> None:
        container = tk.Frame(self.tab_calc, bg="#FFFFFF", highlightbackground="#CBD5E1", highlightthickness=1)
        container.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(
            container,
            text="Gold Weight & Cost Calculator (Gram, Pavan & Chỉ)",
            font=("Segoe UI", 13, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        ).pack(anchor="w", padx=20, pady=(16, 4))

        tk.Label(
            container,
            text="1 Pavan (Kerala Sovereign) = 8.00 grams   |   1 Chỉ (Vietnam) = 3.75 grams   |   1 Lượng = 37.50 grams",
            font=("Segoe UI", 9),
            fg="#64748B",
            bg="#FFFFFF",
        ).pack(anchor="w", padx=20, pady=(0, 14))

        form = tk.Frame(container, bg="#F8FAFC", highlightbackground="#E2E8F0", highlightthickness=1)
        form.pack(fill="x", padx=20, pady=6)

        tk.Label(form, text="Weight:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC").grid(
            row=0, column=0, padx=12, pady=12, sticky="w"
        )
        self.var_calc_weight = tk.StringVar(value="1")
        ent_w = tk.Entry(form, textvariable=self.var_calc_weight, font=("Segoe UI", 11), width=12)
        ent_w.grid(row=0, column=1, padx=6, pady=12)
        ent_w.bind("<KeyRelease>", lambda _e: self._update_calculator())

        tk.Label(form, text="Unit:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC").grid(
            row=0, column=2, padx=12, pady=12, sticky="w"
        )
        self.var_calc_unit = tk.StringVar(value="Pavan (8g)")
        cb_unit = ttk.Combobox(
            form,
            textvariable=self.var_calc_unit,
            values=["Pavan (8g)", "Gram (1g)", "Chỉ (3.75g)", "Lượng (37.5g)"],
            state="readonly",
            width=16,
        )
        cb_unit.grid(row=0, column=3, padx=6, pady=12)
        cb_unit.bind("<<ComboboxSelected>>", lambda _e: self._update_calculator())

        tk.Label(form, text="Purity:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC").grid(
            row=0, column=4, padx=12, pady=12, sticky="w"
        )
        self.var_calc_purity = tk.StringVar(value="22K (916)")
        cb_pur = ttk.Combobox(
            form,
            textvariable=self.var_calc_purity,
            values=["22K (916)", "24K (999 / SJC)"],
            state="readonly",
            width=18,
        )
        cb_pur.grid(row=0, column=5, padx=6, pady=12)
        cb_pur.bind("<<ComboboxSelected>>", lambda _e: self._update_calculator())

        tk.Button(
            form,
            text="Calculate",
            command=self._update_calculator,
            bg="#0F172A",
            fg="#FBBF24",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=14,
            pady=4,
        ).grid(row=0, column=6, padx=14, pady=12)

        self.lbl_calc_result = tk.Label(
            container,
            text="Fetch live rates to calculate Kerala vs Hanoi gold cost...",
            font=("Consolas", 11),
            fg="#0F172A",
            bg="#FFFFFF",
            justify="left",
            anchor="nw",
        )
        self.lbl_calc_result.pack(fill="both", expand=True, padx=24, pady=18)

    def _build_export_tab(self) -> None:
        toolbar = tk.Frame(self.tab_export, bg="#F8FAFC")
        toolbar.pack(fill="x", padx=12, pady=(10, 6))

        buttons = [
            ("Generate PDF Report", self.action_generate_pdf, "#0F172A", "#FBBF24"),
            ("Open Latest PDF", self.action_open_latest_pdf, "#334155", "#FFFFFF"),
            ("Open Reports Folder", self.action_open_reports_dir, "#475569", "#FFFFFF"),
            ("Copy Message", self.action_copy_message, "#64748B", "#FFFFFF"),
            ("Send to Telegram (Text + PDF)", self.action_send_telegram, "#0284C7", "#FFFFFF"),
            ("Send to WhatsApp", self.action_send_whatsapp, "#16A34A", "#FFFFFF"),
        ]
        for label, cmd, bg, fg in buttons:
            tk.Button(
                toolbar,
                text=label,
                command=cmd,
                bg=bg,
                fg=fg,
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                padx=11,
                pady=6,
                cursor="hand2",
            ).pack(side="left", padx=(0, 6))

        tk.Label(
            self.tab_export,
            text="Message Preview (Telegram & WhatsApp — Editable before sending):",
            font=("Segoe UI", 9, "bold"),
            fg="#334155",
            bg="#F8FAFC",
        ).pack(anchor="w", padx=12, pady=(4, 2))

        self.txt_preview = scrolledtext.ScrolledText(
            self.tab_export,
            font=("Consolas", 10),
            bg="#FFFFFF",
            fg="#0F172A",
            wrap="word",
            padx=12,
            pady=10,
        )
        self.txt_preview.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def _build_settings_tab(self) -> None:
        canvas_frame = tk.Frame(self.tab_settings, bg="#F8FAFC")
        canvas_frame.pack(fill="both", expand=True, padx=18, pady=12)

        # ---- Telegram Settings ----
        tg_box = tk.LabelFrame(
            canvas_frame,
            text="  Telegram Bot Settings  ",
            font=("Segoe UI", 10, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
            padx=14,
            pady=10,
        )
        tg_box.pack(fill="x", pady=(0, 10))

        tk.Label(tg_box, text="Bot Token (from @BotFather):", bg="#FFFFFF", font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.var_tg_token = tk.StringVar()
        tk.Entry(tg_box, textvariable=self.var_tg_token, width=54, show="*").grid(
            row=0, column=1, padx=8, pady=4, sticky="w"
        )
        tk.Button(tg_box, text="Test Bot", command=self.action_test_tg, bg="#0284C7", fg="white", relief="flat", padx=10).grid(
            row=0, column=2, padx=4
        )

        tk.Label(tg_box, text="Chat ID (send /start to bot first):", bg="#FFFFFF", font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.var_tg_chat_id = tk.StringVar()
        tk.Entry(tg_box, textvariable=self.var_tg_chat_id, width=32).grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
        )
        tk.Button(
            tg_box,
            text="Detect My Chat ID",
            command=self.action_detect_tg_chat,
            bg="#0F172A",
            fg="#FBBF24",
            relief="flat",
            padx=10,
        ).grid(row=1, column=2, padx=4)

        self.var_tg_send_pdf = tk.BooleanVar(value=True)
        tk.Checkbutton(
            tg_box,
            text="Automatically attach generated PDF report when sending to Telegram",
            variable=self.var_tg_send_pdf,
            bg="#FFFFFF",
            font=("Segoe UI", 9),
        ).grid(row=2, column=1, columnspan=2, sticky="w", pady=4)

        # ---- WhatsApp Personal Settings ----
        wa_box = tk.LabelFrame(
            canvas_frame,
            text="  Personal WhatsApp Web Settings  ",
            font=("Segoe UI", 10, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
            padx=14,
            pady=10,
        )
        wa_box.pack(fill="x", pady=(0, 10))

        tk.Label(wa_box, text="WhatsApp Phone (with country code):", bg="#FFFFFF", font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.var_wa_phone = tk.StringVar()
        tk.Entry(wa_box, textvariable=self.var_wa_phone, width=28).grid(
            row=0, column=1, padx=8, pady=4, sticky="w"
        )
        tk.Label(wa_box, text="Example: +919876543210 or +84912345678", fg="#64748B", bg="#FFFFFF", font=("Segoe UI", 8)).grid(
            row=0, column=2, sticky="w"
        )

        tk.Label(wa_box, text="Delivery Mode:", bg="#FFFFFF", font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="nw", pady=4
        )
        self.var_wa_mode = tk.StringVar(value="browser_url")
        modes_frame = tk.Frame(wa_box, bg="#FFFFFF")
        modes_frame.grid(row=1, column=1, columnspan=2, sticky="w", pady=4)

        tk.Radiobutton(
            modes_frame,
            text="Browser WhatsApp Web (Pre-fills message in default browser — zero setup)",
            variable=self.var_wa_mode,
            value="browser_url",
            bg="#FFFFFF",
        ).pack(anchor="w")
        tk.Radiobutton(
            modes_frame,
            text="PyWhatKit Auto-Send (Auto-sends text message via WhatsApp Web)",
            variable=self.var_wa_mode,
            value="pywhatkit",
            bg="#FFFFFF",
        ).pack(anchor="w")
        tk.Radiobutton(
            modes_frame,
            text="Playwright Auto-Send + PDF Attachment (Sends BOTH text & PDF file via WhatsApp Web)",
            variable=self.var_wa_mode,
            value="playwright_pdf",
            bg="#FFFFFF",
        ).pack(anchor="w")

        tk.Button(
            wa_box,
            text="Link WhatsApp QR (For Playwright PDF Mode)",
            command=self.action_wa_qr_login,
            bg="#16A34A",
            fg="#FFFFFF",
            relief="flat",
            padx=12,
            pady=4,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=2, column=1, sticky="w", padx=8, pady=6)

        tk.Button(
            wa_box,
            text="Install PyWhatKit + Playwright",
            command=self.action_install_wa_extras,
            bg="#334155",
            fg="#FFFFFF",
            relief="flat",
            padx=10,
            pady=4,
            font=("Segoe UI", 9),
        ).grid(row=2, column=2, sticky="w", padx=4, pady=6)

        # ---- General Settings ----
        gen_box = tk.LabelFrame(
            canvas_frame,
            text="  General & PDF Output Settings  ",
            font=("Segoe UI", 10, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
            padx=14,
            pady=10,
        )
        gen_box.pack(fill="x", pady=(0, 10))

        tk.Label(gen_box, text="Auto-Refresh Interval (seconds):", bg="#FFFFFF", font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.var_refresh_sec = tk.StringVar(value="300")
        tk.Entry(gen_box, textvariable=self.var_refresh_sec, width=12).grid(
            row=0, column=1, padx=8, pady=4, sticky="w"
        )

        tk.Label(gen_box, text="PDF Reports Folder:", bg="#FFFFFF", font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.var_reports_dir = tk.StringVar()
        tk.Entry(gen_box, textvariable=self.var_reports_dir, width=52).grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
        )
        tk.Button(
            gen_box,
            text="Browse...",
            command=self._browse_reports_dir,
            bg="#E2E8F0",
            relief="flat",
            padx=10,
        ).grid(row=1, column=2, padx=4)

        tk.Button(
            canvas_frame,
            text="Save Settings",
            command=self.action_save_settings,
            bg="#0F172A",
            fg="#FBBF24",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
        ).pack(anchor="w", pady=6)

    def _load_settings_into_vars(self) -> None:
        self.var_tg_token.set(self.config.get("telegram_bot_token", ""))
        self.var_tg_chat_id.set(self.config.get("telegram_chat_id", ""))
        self.var_tg_send_pdf.set(bool(self.config.get("telegram_send_pdf", True)))
        self.var_wa_phone.set(self.config.get("whatsapp_phone", ""))
        self.var_wa_mode.set(self.config.get("whatsapp_mode", "browser_url"))
        self.var_refresh_sec.set(str(self.config.get("refresh_interval_seconds", 300)))
        self.var_reports_dir.set(str(self.config.get("reports_dir", "")))
        self.var_auto_refresh.set(bool(self.config.get("auto_refresh_enabled", True)))

    def _browse_reports_dir(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.var_reports_dir.get() or str(Path.home()))
        if chosen:
            self.var_reports_dir.set(chosen)

    def _set_status(self, msg: str) -> None:
        self.lbl_status.config(text=msg)

    def _toggle_auto_refresh(self) -> None:
        self.config["auto_refresh_enabled"] = self.var_auto_refresh.get()
        save_config(self.config)
        self._schedule_next_refresh()

    def _schedule_next_refresh(self) -> None:
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        if self.var_auto_refresh.get():
            try:
                sec = max(30, int(self.config.get("refresh_interval_seconds", 300)))
            except ValueError:
                sec = 300
            self._after_id = self.root.after(sec * 1000, self.refresh_data)

    # ---- Background Live Fetch ----
    def refresh_data(self) -> None:
        if self._is_busy:
            return
        self._is_busy = True
        self.btn_refresh.config(state="disabled", text="Fetching...")
        self._set_status("Fetching live Kerala & Hanoi gold prices and FX rates...")

        def worker() -> None:
            try:
                snap = fetch_all_market_data()
                self.root.after(0, lambda: self._on_data_fetched(snap))
            except Exception as exc:
                self.root.after(0, lambda: self._on_fetch_error(str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_fetch_error(self, err: str) -> None:
        self._is_busy = False
        self.btn_refresh.config(state="normal", text="Refresh Live Prices")
        self._set_status(f"Error fetching data: {err}")
        self._schedule_next_refresh()

    def _on_data_fetched(self, snap: GoldMarketSnapshot) -> None:
        self.snapshot = snap
        self._is_busy = False
        self.btn_refresh.config(state="normal", text="Refresh Live Prices")

        self.lbl_subtitle.config(
            text=f"Updated: {snap.fetched_at}   |   Live FX: 1 INR = {snap.fx_inr_to_vnd:,.2f} VND (1 VND = ₹{snap.fx_vnd_to_inr:.6f})"
        )

        # Update KPI Cards
        k22 = snap.get_kerala("22K")
        k24 = snap.get_kerala("24K")
        hsjc = snap.get_hanoi("SJC")
        h22 = snap.get_hanoi("22K")

        if k22:
            chg = f"Today: {'+' if k22.change_pavan_inr > 0 else ''}₹{k22.change_pavan_inr:,.0f}/pavan" if k22.change_pavan_inr else f"Updated {snap.kerala_updated}"
            self.card_k22["pavan"].config(text=f"₹{k22.per_pavan_inr:,.0f} / pavan")
            self.card_k22["gram"].config(text=f"₹{k22.per_gram_inr:,.0f} / gram")
            self.card_k22["sub"].config(text=chg)

        if k24:
            chg = f"Today: {'+' if k24.change_pavan_inr > 0 else ''}₹{k24.change_pavan_inr:,.0f}/pavan" if k24.change_pavan_inr else f"Updated {snap.kerala_updated}"
            self.card_k24["pavan"].config(text=f"₹{k24.per_pavan_inr:,.0f} / pavan")
            self.card_k24["gram"].config(text=f"₹{k24.per_gram_inr:,.0f} / gram")
            self.card_k24["sub"].config(text=chg)

        if hsjc:
            self.card_hsjc["pavan"].config(text=f"{hsjc.sell_per_pavan_vnd:,.0f} ₫ / pavan")
            self.card_hsjc["gram"].config(text=f"{hsjc.sell_per_gram_vnd:,.0f} ₫ / gram")
            self.card_hsjc["sub"].config(
                text=f"≈ ₹{hsjc.sell_per_pavan_inr:,.0f}/pavan (₹{hsjc.sell_per_gram_inr:,.0f}/g)"
            )

        if h22:
            self.card_h22["pavan"].config(text=f"{h22.sell_per_pavan_vnd:,.0f} ₫ / pavan")
            self.card_h22["gram"].config(text=f"{h22.sell_per_gram_vnd:,.0f} ₫ / gram")
            self.card_h22["sub"].config(
                text=f"≈ ₹{h22.sell_per_pavan_inr:,.0f}/pavan (₹{h22.sell_per_gram_inr:,.0f}/g)"
            )

        # Populate Kerala Treeview
        for item in self.tree_kerala.get_children():
            self.tree_kerala.delete(item)
        for r in snap.kerala_rates:
            if r.change_gram_inr > 0:
                chg_str = f"+₹{r.change_gram_inr:,.0f} / +₹{r.change_pavan_inr:,.0f}"
            elif r.change_gram_inr < 0:
                chg_str = f"-₹{abs(r.change_gram_inr):,.0f} / -₹{abs(r.change_pavan_inr):,.0f}"
            else:
                chg_str = "No change"
            self.tree_kerala.insert(
                "",
                "end",
                values=(
                    r.purity,
                    f"₹{r.per_gram_inr:,.2f}" if r.per_gram_inr % 1 else f"₹{r.per_gram_inr:,.0f}",
                    f"₹{r.per_pavan_inr:,.0f}",
                    f"₹{r.per_10g_inr:,.0f}",
                    chg_str,
                ),
            )
        self.lbl_kerala_meta.config(text=f"Source: {snap.kerala_source}  |  {snap.kerala_updated}")

        # Populate Hanoi Treeview
        for item in self.tree_hanoi.get_children():
            self.tree_hanoi.delete(item)
        for r in snap.hanoi_rates:
            self.tree_hanoi.insert(
                "",
                "end",
                values=(
                    r.name_en,
                    r.karat,
                    f"{r.sell_per_gram_vnd:,.0f} ₫",
                    f"{r.sell_per_pavan_vnd:,.0f} ₫",
                    f"₹{r.sell_per_gram_inr:,.2f}",
                    f"₹{r.sell_per_pavan_inr:,.0f}",
                    f"{r.buy_per_pavan_vnd:,.0f} ₫",
                    f"{r.sell_per_chi_vnd:,.0f} ₫",
                ),
            )
        self.lbl_hanoi_meta.config(text=f"Source: {snap.hanoi_source}  |  {snap.hanoi_updated}")

        # Comparison Text
        comp_lines = []
        if k24 and hsjc:
            dg = k24.per_gram_inr - hsjc.sell_per_gram_inr
            dp = k24.per_pavan_inr - hsjc.sell_per_pavan_inr
            who = "Hanoi SJC is cheaper" if dg > 0 else "Kerala 24K is cheaper"
            comp_lines.append(
                f"24K Comparison: Kerala ₹{k24.per_pavan_inr:,.0f}/pavan vs Hanoi SJC ₹{hsjc.sell_per_pavan_inr:,.0f}/pavan  ->  {who} by ₹{abs(dg):,.0f}/g (₹{abs(dp):,.0f}/pavan)"
            )
        if k22 and h22:
            dg = k22.per_gram_inr - h22.sell_per_gram_inr
            dp = k22.per_pavan_inr - h22.sell_per_pavan_inr
            who = "Hanoi 22K is cheaper" if dg > 0 else "Kerala 22K is cheaper"
            comp_lines.append(
                f"22K Comparison: Kerala ₹{k22.per_pavan_inr:,.0f}/pavan vs Hanoi 916 ₹{h22.sell_per_pavan_inr:,.0f}/pavan  ->  {who} by ₹{abs(dg):,.0f}/g (₹{abs(dp):,.0f}/pavan)"
            )
        self.lbl_comparison.config(text="\n".join(comp_lines) if comp_lines else "Comparison unavailable.")

        # Update Preview & Calculator
        self.txt_preview.delete("1.0", tk.END)
        self.txt_preview.insert("1.0", format_messenger_report(snap))
        self._update_calculator()

        if snap.errors:
            self._set_status(f"Updated at {snap.fetched_at} with warnings: {'; '.join(snap.errors)}")
        else:
            self._set_status(f"Live prices updated at {snap.fetched_at} (Kerala + Hanoi + FX).")

        self._schedule_next_refresh()

    def _update_calculator(self) -> None:
        if not self.snapshot:
            return
        try:
            qty = float(self.var_calc_weight.get().strip() or "0")
        except ValueError:
            self.lbl_calc_result.config(text="Enter a valid numeric weight.")
            return

        unit = self.var_calc_unit.get()
        if "Pavan" in unit:
            grams = qty * GRAMS_PER_PAVAN
        elif "Chỉ" in unit:
            grams = qty * GRAMS_PER_CHI
        elif "Lượng" in unit:
            grams = qty * 37.5
        else:
            grams = qty

        pavans = grams / GRAMS_PER_PAVAN
        chis = grams / GRAMS_PER_CHI

        purity = self.var_calc_purity.get()
        if "22K" in purity:
            k_rate = self.snapshot.get_kerala("22K")
            h_rate = self.snapshot.get_hanoi("22K")
            label = "22K (916)"
        else:
            k_rate = self.snapshot.get_kerala("24K")
            h_rate = self.snapshot.get_hanoi("SJC") or self.snapshot.get_hanoi("N24K")
            label = "24K (999 / SJC)"

        lines = [
            f"Weight Entered : {qty:g} {unit}",
            f"Exact Grams    : {grams:,.3f} g",
            f"Exact Pavans   : {pavans:,.4f} pavan (8g each)",
            f"Exact Chỉ (VN) : {chis:,.4f} chỉ (3.75g each)",
            "-" * 62,
        ]
        if k_rate:
            k_total = k_rate.per_gram_inr * grams
            lines.append(f"Kerala {label:<16}: ₹{k_total:,.2f}  (@ ₹{k_rate.per_gram_inr:,.0f}/g)")
        if h_rate:
            h_vnd = h_rate.sell_per_gram_vnd * grams
            h_inr = h_rate.sell_per_gram_inr * grams
            lines.append(f"Hanoi {label:<17}: {h_vnd:,.0f} ₫  (≈ ₹{h_inr:,.2f} @ {h_rate.sell_per_gram_vnd:,.0f} ₫/g)")
        if k_rate and h_rate:
            diff = (k_rate.per_gram_inr * grams) - (h_rate.sell_per_gram_inr * grams)
            cheaper = "Hanoi" if diff > 0 else "Kerala"
            lines.append("-" * 62)
            lines.append(f"Price Difference        : {cheaper} is cheaper by ₹{abs(diff):,.2f}")

        self.lbl_calc_result.config(text="\n".join(lines))

    # ---- Actions ----
    def _ensure_pdf(self) -> Path:
        if not self.snapshot:
            raise RuntimeError("Live prices have not loaded yet. Please click Refresh first.")
        reports_dir = Path(self.config.get("reports_dir") or "reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        fname = f"Gold_Price_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = generate_gold_pdf(self.snapshot, reports_dir / fname)
        self.last_pdf_path = pdf_path
        return pdf_path

    def _open_path(self, path: Path) -> None:
        sys_name = platform.system()
        if sys_name == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys_name == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def action_generate_pdf(self) -> None:
        try:
            pdf_path = self._ensure_pdf()
            self._set_status(f"PDF generated: {pdf_path}")
            if messagebox.askyesno("PDF Created", f"Saved PDF report:\n{pdf_path}\n\nOpen it now?"):
                self._open_path(pdf_path)
        except Exception as exc:
            messagebox.showerror("PDF Error", str(exc))

    def action_open_latest_pdf(self) -> None:
        if self.last_pdf_path and self.last_pdf_path.exists():
            self._open_path(self.last_pdf_path)
        else:
            self.action_generate_pdf()

    def action_open_reports_dir(self) -> None:
        rdir = Path(self.config.get("reports_dir") or "reports")
        rdir.mkdir(parents=True, exist_ok=True)
        self._open_path(rdir)

    def action_copy_message(self) -> None:
        msg = self.txt_preview.get("1.0", tk.END).strip()
        if not msg:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(msg)
        self._set_status("Formatted Gram & Pavan message copied to clipboard!")

    def action_save_settings(self) -> None:
        try:
            sec = max(30, int(self.var_refresh_sec.get().strip() or "300"))
        except ValueError:
            messagebox.showerror("Invalid Interval", "Auto-refresh interval must be a number (seconds).")
            return

        self.config["telegram_bot_token"] = self.var_tg_token.get().strip()
        self.config["telegram_chat_id"] = self.var_tg_chat_id.get().strip()
        self.config["telegram_send_pdf"] = bool(self.var_tg_send_pdf.get())
        self.config["whatsapp_phone"] = self.var_wa_phone.get().strip()
        self.config["whatsapp_mode"] = self.var_wa_mode.get()
        self.config["refresh_interval_seconds"] = sec
        self.config["reports_dir"] = self.var_reports_dir.get().strip() or str(Path("reports").resolve())
        self.config["auto_refresh_enabled"] = bool(self.var_auto_refresh.get())

        save_config(self.config)
        self._schedule_next_refresh()
        self._set_status("Settings saved.")
        messagebox.showinfo("Saved", "Settings saved successfully!")

    def action_test_tg(self) -> None:
        token = self.var_tg_token.get().strip()
        try:
            bot_info = test_telegram_bot(token)
            messagebox.showinfo("Telegram Connected", f"Connected to bot: {bot_info}")
        except Exception as exc:
            messagebox.showerror("Telegram Error", str(exc))

    def action_detect_tg_chat(self) -> None:
        token = self.var_tg_token.get().strip()
        try:
            chats = detect_telegram_chat_id(token)
            if not chats:
                messagebox.showwarning(
                    "No Chats Found",
                    "No recent messages found.\n\n1. Open Telegram and find your bot.\n2. Press Start or send 'hi'.\n3. Click 'Detect My Chat ID' again.",
                )
                return
            latest = chats[-1]
            self.var_tg_chat_id.set(latest["id"])
            summary = "\n".join(f"{c['title']} ({c['type']}): {c['id']}" for c in chats)
            messagebox.showinfo("Chat ID Detected", f"Selected latest Chat ID: {latest['id']}\n\nFound:\n{summary}")
        except Exception as exc:
            messagebox.showerror("Telegram Error", str(exc))

    def action_send_telegram(self) -> None:
        if not self.snapshot:
            messagebox.showwarning("No Data", "Wait for live prices to load first.")
            return
        token = self.var_tg_token.get().strip() or self.config.get("telegram_bot_token", "")
        chat_id = self.var_tg_chat_id.get().strip() or self.config.get("telegram_chat_id", "")
        send_pdf = bool(self.var_tg_send_pdf.get())
        msg = self.txt_preview.get("1.0", tk.END).strip() or format_messenger_report(self.snapshot)

        self._set_status("Sending report to Telegram...")

        def worker() -> None:
            try:
                pdf_path = self._ensure_pdf() if send_pdf else None
                res = send_telegram_report(token, chat_id, msg, pdf_path=pdf_path)
                self.root.after(0, lambda: self._on_notify_done(res, is_error=False))
            except Exception as exc:
                self.root.after(0, lambda: self._on_notify_done(str(exc), is_error=True))

        threading.Thread(target=worker, daemon=True).start()

    def action_install_wa_extras(self) -> None:
        import sys
        if getattr(sys, "frozen", False):
            messagebox.showinfo(
                "Standalone Mode",
                "This executable is already packaged. Use 'Browser WhatsApp Web' mode or run from Python source for Playwright.",
            )
            return

        req_opt = Path(__file__).resolve().parent / "requirements-optional.txt"
        self._set_status("Installing PyWhatKit & Playwright + Chromium (this may take 1-2 minutes)...")

        def worker() -> None:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_opt)])
                subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
                self.root.after(
                    0,
                    lambda: self._on_notify_done(
                        "PyWhatKit & Playwright Chromium installed! You can now use 'Link WhatsApp QR'.",
                        is_error=False,
                    ),
                )
            except Exception as exc:
                self.root.after(0, lambda: self._on_notify_done(f"Install failed: {exc}", is_error=True))

        threading.Thread(target=worker, daemon=True).start()

    def action_wa_qr_login(self) -> None:
        self._set_status("Opening WhatsApp Web for QR scan...")

        def worker() -> None:
            try:
                res = open_whatsapp_qr_login()
                self.root.after(0, lambda: self._on_notify_done(res, is_error=False))
            except Exception as exc:
                self.root.after(0, lambda: self._on_notify_done(str(exc), is_error=True))

        threading.Thread(target=worker, daemon=True).start()

    def action_send_whatsapp(self) -> None:
        if not self.snapshot:
            messagebox.showwarning("No Data", "Wait for live prices to load first.")
            return
        phone = self.var_wa_phone.get().strip() or self.config.get("whatsapp_phone", "")
        mode = self.var_wa_mode.get() or self.config.get("whatsapp_mode", "browser_url")
        msg = self.txt_preview.get("1.0", tk.END).strip() or format_messenger_report(self.snapshot)

        self._set_status(f"Sending via WhatsApp ({mode})...")

        def worker() -> None:
            try:
                pdf_path = self._ensure_pdf()
                res = send_whatsapp_report(phone, msg, mode=mode, pdf_path=pdf_path)
                self.root.after(0, lambda: self._on_notify_done(res, is_error=False))
            except Exception as exc:
                self.root.after(0, lambda: self._on_notify_done(str(exc), is_error=True))

        threading.Thread(target=worker, daemon=True).start()

    def _on_notify_done(self, msg: str, is_error: bool) -> None:
        self._set_status(msg)
        if is_error:
            messagebox.showerror("Delivery Error", msg)
        else:
            messagebox.showinfo("Success", msg)


def main() -> None:
    root = tk.Tk()
    GoldTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
