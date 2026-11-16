"""Telegram Bot API & Personal WhatsApp Web notifiers."""

from __future__ import annotations

import html
import re
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any

import requests


def _clean_phone(phone: str) -> tuple[str, str]:
    """Return (with_plus, digits_only) from user-entered phone number."""
    raw = phone.strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        raise ValueError("Please enter a valid WhatsApp phone number with country code (e.g. +919876543210 or +84912345678).")
    return f"+{digits}", digits


def _markdown_to_telegram_html(text: str) -> str:
    """Safely convert our simple *bold* and _italic_ report to Telegram HTML."""
    escaped = html.escape(text)
    escaped = re.sub(r"\*(.+?)\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", escaped)
    return escaped


def test_telegram_bot(bot_token: str) -> str:
    """Verify bot token via getMe and return bot username."""
    token = bot_token.strip()
    if not token:
        raise ValueError("Telegram Bot Token is empty.")
    resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=12)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "Invalid Telegram Bot Token"))
    result = data["result"]
    return f"@{result.get('username', 'bot')} ({result.get('first_name', '')})"


def detect_telegram_chat_id(bot_token: str) -> list[dict[str, str]]:
    """Fetch recent chats from getUpdates so user can pick their Chat ID easily."""
    token = bot_token.strip()
    if not token:
        raise ValueError("Enter your Telegram Bot Token first.")
    resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=12)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "Failed to read Telegram updates"))
    seen: dict[str, dict[str, str]] = {}
    for upd in data.get("result", []):
        msg = upd.get("message") or upd.get("channel_post") or upd.get("edited_message") or {}
        chat = msg.get("chat") or {}
        cid = str(chat.get("id", ""))
        if cid:
            title = chat.get("title") or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip() or chat.get("username", "Chat")
            seen[cid] = {"id": cid, "title": title, "type": chat.get("type", "")}
    return list(seen.values())


def send_telegram_report(
    bot_token: str,
    chat_id: str,
    message: str,
    pdf_path: str | Path | None = None,
) -> str:
    """Send text message and optional PDF document via Telegram Bot API."""
    token = bot_token.strip()
    cid = chat_id.strip()
    if not token or not cid:
        raise ValueError("Telegram Bot Token and Chat ID are required in Settings.")

    base_url = f"https://api.telegram.org/bot{token}"
    html_text = _markdown_to_telegram_html(message)

    r_msg = requests.post(
        f"{base_url}/sendMessage",
        json={"chat_id": cid, "text": html_text, "parse_mode": "HTML"},
        timeout=20,
    )
    msg_data = r_msg.json()
    if not msg_data.get("ok"):
        # Fallback plain text
        r_plain = requests.post(
            f"{base_url}/sendMessage",
            json={"chat_id": cid, "text": message},
            timeout=20,
        )
        plain_data = r_plain.json()
        if not plain_data.get("ok"):
            raise RuntimeError(f"Telegram sendMessage failed: {plain_data.get('description')}")

    status_parts = ["Telegram message sent"]

    if pdf_path is not None:
        p = Path(pdf_path)
        if p.exists():
            with p.open("rb") as f:
                r_doc = requests.post(
                    f"{base_url}/sendDocument",
                    data={"chat_id": cid, "caption": "Kerala & Hanoi Live Gold Report (Gram & Pavan)"},
                    files={"document": (p.name, f, "application/pdf")},
                    timeout=45,
                )
            doc_data = r_doc.json()
            if not doc_data.get("ok"):
                raise RuntimeError(f"Telegram sendDocument failed: {doc_data.get('description')}")
            status_parts.append(f"PDF sent ({p.name})")

    return " + ".join(status_parts)


def open_whatsapp_qr_login() -> str:
    """Open persistent Playwright Chromium window on web.whatsapp.com for one-time QR scan."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run: pip install playwright && playwright install chromium"
        ) from exc

    profile_dir = Path.home() / ".gold_tracker_wa_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            viewport={"width": 1200, "height": 820},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        # Wait until user logs in (search/chat list appears) or closes window (max 120s)
        try:
            page.wait_for_selector("div[contenteditable='true'][data-tab]", timeout=120_000)
            msg = "WhatsApp Web linked and session saved! You can close the browser or keep sending."
        except Exception:
            msg = "WhatsApp Web window timed out waiting for login. Please try again."
        finally:
            context.close()
    return msg


def send_whatsapp_report(
    phone: str,
    message: str,
    mode: str = "browser_url",
    pdf_path: str | Path | None = None,
) -> str:
    """Send live gold report (and optionally PDF) via personal WhatsApp Web."""
    phone_plus, phone_digits = _clean_phone(phone)

    if mode == "browser_url":
        encoded = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send?phone={phone_digits}&text={encoded}"
        webbrowser.open(url)
        return (
            f"Opened WhatsApp Web for {phone_plus} with your message pre-filled. "
            "Press Enter in WhatsApp Web to send."
        )

    if mode == "pywhatkit":
        try:
            import pywhatkit  # type: ignore
        except ImportError as exc:
            raise RuntimeError("pywhatkit is not installed. Run: pip install pywhatkit") from exc
        pywhatkit.sendwhatmsg_instantly(
            phone_no=phone_plus,
            message=message,
            wait_time=15,
            tab_close=False,
            close_time=4,
        )
        return f"WhatsApp message triggered via pywhatkit to {phone_plus}."

    if mode == "playwright_pdf":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Run: pip install playwright && playwright install chromium"
            ) from exc

        profile_dir = Path.home() / ".gold_tracker_wa_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(profile_dir),
                headless=False,
                viewport={"width": 1280, "height": 840},
            )
            page = context.pages[0] if context.pages else context.new_page()
            encoded = urllib.parse.quote(message)
            page.goto(
                f"https://web.whatsapp.com/send?phone={phone_digits}&text={encoded}",
                wait_until="domcontentloaded",
            )
            # Wait for chat input box (allows time for QR scan if not yet logged in)
            compose_box = page.wait_for_selector(
                "footer div[contenteditable='true'][data-tab]",
                timeout=90_000,
            )
            compose_box.click()
            page.keyboard.press("Enter")
            page.wait_for_timeout(1500)

            sent_pdf = False
            if pdf_path is not None and Path(pdf_path).exists():
                pdf_file = str(Path(pdf_path).resolve())
                # Click Attach (+) button in WhatsApp Web footer
                attach_btn = page.locator("footer button[title='Attach'], footer span[data-icon='plus'], footer span[data-icon='clip']").first
                attach_btn.click()
                page.wait_for_timeout(600)
                # Document file input accepts any file
                file_input = page.locator("input[type='file']").first
                file_input.set_input_files(pdf_file)
                page.wait_for_timeout(1500)
                send_media_btn = page.locator("span[data-icon='send'], div[aria-label='Send']").first
                send_media_btn.click()
                page.wait_for_timeout(3000)
                sent_pdf = True

            context.close()
        return (
            f"WhatsApp message + PDF sent to {phone_plus}!"
            if sent_pdf
            else f"WhatsApp message sent to {phone_plus}!"
        )

    raise ValueError(f"Unknown WhatsApp mode: {mode}")
