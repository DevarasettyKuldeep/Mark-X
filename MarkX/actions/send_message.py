# actions/send_message.py
#
# Sends a WhatsApp message by opening WhatsApp Web in the browser.
# No third-party packages needed beyond the Python standard library.
# Works by constructing a wa.me deep-link URL with the pre-filled message.

import webbrowser
import urllib.parse
import time


def send_message(parameters: dict, player=None, session_memory: dict = None) -> None:
    contact: str = parameters.get("contact", "").strip()
    message: str = parameters.get("message", "").strip()

    # ── Resolve phone number ──────────────────────────────────────────────────
    phone_number: str | None = None

    # 1. Contact string is already a number (e.g. "+905551234567")
    cleaned = contact.replace(" ", "").replace("-", "")
    if cleaned.startswith("+") or cleaned.lstrip("+").isdigit():
        phone_number = cleaned

    # 2. Look up in session memory contacts dict
    if not phone_number and isinstance(session_memory, dict):
        contacts: dict = session_memory.get("contacts", {})
        phone_number = contacts.get(contact.lower()) or contacts.get(contact)

    # 3. Not found — ask the user
    if not phone_number:
        msg = (
            f"Sir, I don't have a phone number stored for '{contact}'. "
            "Please provide their number including country code, "
            "for example +1 555 123 4567."
        )
        if player:
            player.write_log(f"Mark-X: {msg}")
        print(f"send_message: no number for '{contact}'")
        return

    if not message:
        msg = "Sir, what message would you like me to send?"
        if player:
            player.write_log(f"Mark-X: {msg}")
        return

    # ── Build WhatsApp Web URL ─────────────────────────────────────────────────
    # Strip leading + for the URL (wa.me uses plain digits)
    number = phone_number.lstrip("+").replace(" ", "").replace("-", "")
    encoded_msg = urllib.parse.quote(message)
    url = f"https://wa.me/{number}?text={encoded_msg}"

    try:
        reply = f"Sir, opening WhatsApp Web to send '{message}' to {contact}."
        if player:
            player.write_log(f"Mark-X: {reply}")

        webbrowser.open(url)

        # Brief pause so the browser has time to open
        time.sleep(1)

    except Exception as e:
        err = f"Sir, I couldn't open WhatsApp Web: {e}"
        if player:
            player.write_log(f"Mark-X: {err}")
        print(f"send_message error: {e}")
