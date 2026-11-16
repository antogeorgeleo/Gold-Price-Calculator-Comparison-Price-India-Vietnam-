# Kerala & Hanoi Live Gold Tracker (Ready-to-Run PC App)

A ready-to-run Python desktop application that fetches **real-time gold prices** for **Kerala, India (INR)** and **Hanoi, Vietnam (VND + converted INR)**, displays them both **per Gram** and **per Pavan (8 grams)**, exports polished **A4 PDF reports**, and sends updates directly to **Telegram (Text + PDF)** and **Personal WhatsApp Web**.

## One-Click Launch (No Manual Setup Needed)

1. Extract the folder anywhere on your PC (requires Python 3.10+ installed).
2. **Windows**: Double-click **`run_app.bat`**
   - On first launch, it automatically creates `.venv`, installs the core packages (`requests`, `beautifulsoup4`, `reportlab`), and opens the desktop window.
   - *(Optional)* Double-click **`Create_Desktop_Shortcut.bat`** to place a shortcut on your Desktop.
3. **macOS / Linux**: Run **`./run_app.sh`** (or `python3 launcher.py`).

## Optional: Build a Standalone Single-File `.exe` (No Python Needed on Target PC)
- **Windows**: Double-click **`build_exe.bat`** -> generates `dist/KeralaHanoiGoldTracker.exe`.
- **macOS / Linux**: Run **`./build_exe.sh`** -> generates `dist/KeralaHanoiGoldTracker`.

## Quick Setup for Telegram & WhatsApp (Inside the App's Settings Tab)
1. **Telegram**:
   - Message `@BotFather` on Telegram -> `/newbot` -> copy the Bot Token.
   - Paste it into **Settings** and click **Test Bot**.
   - Open your bot in Telegram, press **Start**, then click **Detect My Chat ID** in Settings.
   - Clicking **Send to Telegram** sends both the formatted Gram/Pavan summary and the attached PDF report.
2. **Personal WhatsApp Web**:
   - Enter your phone number with country code (e.g., `+919876543210` or `+84912345678`).
   - **Browser WhatsApp Web** (default, zero setup): Opens WhatsApp Web in your browser with the Gram & Pavan message pre-filled.
   - **PyWhatKit / Playwright + PDF**: Click **Install PyWhatKit + Playwright** in Settings, then **Link WhatsApp QR** once to auto-send both text and PDF files.
