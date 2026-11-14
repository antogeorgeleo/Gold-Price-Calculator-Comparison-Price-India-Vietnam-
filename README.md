# 🦁 LEO — Vietnam & India Gold Rate Comparison Application
**Created by Anto George Leo**

A premium Python application for comparing gold prices between **Vietnam** (input by **Chỉ**) and **India** (input by **Gram**), generating executive comparison outputs in **Chỉ**, **Gram**, and **Pavan (Sovereign)**.

---

## ✨ Key Features
- **Vietnam & India User Inputs**:
  - **Vietnam Gold Price**: Entered per **1 Chỉ (3.75 grams)** in **VND (₫)** with live Lượng (10 Chỉ) preview and market presets.
  - **India Gold Price**: Entered per **1 Gram (1.00 gram)** in **INR (₹)** with Indian Lakh/Crore formatting and Pavan (8g) preview.
  - **Live Currency Exchange Sync**: Automatically fetches live `INR ↔ VND` forex rates (with manual override support).
- **Complete Multi-Unit Comparison**:
  - Side-by-side prices, exact savings/spreads, and cheaper-market verdict across **1 Chỉ (3.75g)**, **1 Gram (1.00g)**, **1 Pavan (8.00g)**, **1 Lượng (37.50g)**, and any **Custom Quantity**.
- **5 Output & Conversion Options**:
  1. **PDF Report**: Theme-styled A4 executive PDF generated with Python (`ReportLab`) including visual comparison bars.
  2. **WhatsApp**: Ready-to-send formatted WhatsApp report with one-click WhatsApp Web/App launch, optional phone number targeting, and clipboard copy.
  3. **Telegram**: Formatted Telegram comparison report with one-click Telegram share, clipboard copy, plus optional direct Python Telegram Bot API sender (attaching the PDF automatically).
  4. **Excel Workbook (`.xlsx`)**: Multi-sheet spreadsheet generated with Python (`OpenPyXL`) containing **live dynamic Excel formulas** so editing rates inside Excel recalculates everything automatically.
  5. **Print Option**: Dedicated single-page A4 print-optimized executive comparison sheet.
- **10 Luxury Color Themes**:
  1. *Imperial Gold & Obsidian*
  2. *Royal Emerald Vault*
  3. *Maharaja Ruby Velvet*
  4. *Midnight Sapphire Crown*
  5. *Amethyst Sovereign*
  6. *Champagne Ivory Pearl (Light Couture)*
  7. *Rose Gold Couture*
  8. *Saigon Jade & Amber*
  9. *Platinum Horology*
  10. *Saffron Sunset Palace*
- **Ambient Background Music**:
  - 3 stereo ambient instrumental tracks synthesized natively in Python (`Golden Lounge Serenity`, `Lotus & Silk`, `Royal Vault Nocturne`) + volume control + **Custom MP3/WAV** file player.

---

## 🚀 Running Locally on Your Computer

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the application (auto-opens in your browser):
   ```bash
   python run_leo.py
   ```
   *(Or run the server directly via `python app.py` and visit `http://127.0.0.1:8000`)*

---

## ⚖️ Bullion Weight Reference
| Unit | Grams (g) | Vietnam Chỉ | India Pavan | Vietnam Lượng |
| :--- | :---: | :---: | :---: | :---: |
| **1 Chỉ** | `3.75 g` | `1.0000` | `0.46875` | `0.1000` |
| **1 Gram** | `1.00 g` | `0.2667` | `0.12500` | `0.0267` |
| **1 Pavan (Sovereign)** | `8.00 g` | `2.1333` | `1.00000` | `0.2133` |
| **1 Lượng (Cây / Tael)** | `37.50 g` | `10.0000` | `4.68750` | `1.0000` |

---
*Application Name: **LEO** • Created by **Anto George Leo***
