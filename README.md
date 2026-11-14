# 🦁 LEO — Vietnam ⇄ India Gold Rate Comparison

**Created by Anto George Leo**

A premium **desktop application** written in Python that compares Vietnamese and
Indian gold prices side by side, and exports the result as **PDF, Excel,
WhatsApp, Telegram or Print** — with **10 luxury themes** and **background music**.

---

## ▶ How to run (the one thing you need)

```bash
python3 leo_desktop.py
```

That's it. A window called **LEO** opens — this is a real desktop program
(Tkinter), **not** a web page and **not** something you view in the browser.

Faster ways to launch it:

| System | Do this |
|---|---|
| **Windows** | Double-click **`Leo.bat`** (or run `python leo_desktop.py`) |
| **macOS** | Double-click **`Leo.command`** (or `python3 leo_desktop.py`) |
| **Linux** | `python3 leo_desktop.py` |

> If the window does not appear, run the command in a terminal and read the
> message — see **Troubleshooting** below.

### Optional extras (the app works without them)

```bash
pip install reportlab openpyxl          # PDF + Excel export
pip install requests                    # Telegram bot delivery
```

Missing packages never crash the app: you get a friendly message telling you
exactly what to install.

---

## ✨ What it does

**Input**
* Vietnam gold price **per Chỉ (3.75 g)** in VND
* India gold price **per Gram (1.00 g)** in INR
* INR → VND exchange rate

**Comparison** — every unit, both currencies, and a clear verdict:

| Unit | Weight |
|---|---|
| Chỉ | 3.75 g |
| Gram | 1.00 g |
| Pavan | 8.00 g |
| (Lượng | 37.50 g — shown in the standards panel) |

For each unit LEO shows the Vietnam price in ₫ **and** ₹, the India price in ₹
**and** ₫, which market is cheaper, the saving, and a visual bar comparison.

**Output & sharing**
* 🖨 **PDF Report** – branded A4 report using the active theme
* ▦ **Excel** – 2 sheets: a formatted comparison + a live formula *Calculator* you can edit
* ✆ **WhatsApp** – opens WhatsApp with the full comparison pre-filled
* ✈ **Telegram** – opens Telegram share (or delivers via bot, see below)
* 🖨 **Print** – builds a print-ready PDF and sends it to the printer
* ⧉ **Copy Summary** – plain-text summary to the clipboard

**Personalisation**
* **10 luxury themes** — one click on the swatch bar, everything recolours instantly
* **Background music** — a warm lounge loop synthesised in Python
  (no internet, no external files; press the ♪ button in the header)

---

## 📁 Files

| File | Purpose |
|---|---|
| `leo_desktop.py` | **The application** — single file, standard library only |
| `Leo.bat` / `Leo.command` | One-click launchers (Windows / macOS) |
| `music/leo_lounge.wav` | Generated background music (auto-created on first run) |
| `exports/` | PDF / Excel reports land here |
| `preview_dark.png`, `preview_ivory.png` | Screenshots of the interface |
| `app.py`, `gold_engine.py`, `export_service.py`, `templates/`, `static/` | Optional Flask *web* version of the same idea |
| `requirements.txt` | Optional Python packages |

---

## ⌨ Keyboard shortcuts

| Key | Action |
|---|---|
| `Enter` / `F5` | Compare |
| `Ctrl + S` | Save PDF report |
| `Ctrl + P` | Print |

---

## ✈ Telegram bot delivery (optional)

Set these two environment variables before launching, and the Telegram button
sends the report straight to your chat instead of opening the share window:

```bash
export LEO_TELEGRAM_BOT_TOKEN="123456:ABCDEF..."
export LEO_TELEGRAM_CHAT_ID="123456789"
```

---

## 🛠 Troubleshooting — "the app won't open"

1. **Run it from a terminal** (`python3 leo_desktop.py`) so you can read the error.
2. **Check Python:** `python3 --version` → needs **3.9 or newer**.
3. **Tkinter missing on Linux:**
   ```bash
   sudo apt install python3-tk
   ```
   On Windows/macOS Tkinter ships with Python from python.org — if you used the
   Microsoft Store build, reinstall from https://python.org and tick
   *“Add python.exe to PATH”*.
4. **“python is not recognized” (Windows):** use `py leo_desktop.py`, or tick
   *Add python.exe to PATH* during installation.
5. **Music button says “no audio player”:** Windows/macOS work out of the box;
   on Linux install one of `ffmpeg`, `mpv`, `pulseaudio-utils` (`paplay`) or
   `alsa-utils` (`aplay`).
6. **Nothing at all happens on macOS:** right-click `Leo.command` →
   *Open* the first time (Gatekeeper), or run `python3 leo_desktop.py`.

---

## ⚖ Disclaimer

Prices are entered by you, or loaded from sample benchmarks
(Vietnam ≈ ₫14,100,000 per Chỉ · India ≈ ₹13,849 per gram · 1 INR ≈ 273.07 VND).
Always confirm with your jeweller before trading.

---

**LEO** · Created by **Anto George Leo**
