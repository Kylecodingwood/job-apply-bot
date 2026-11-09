"""
Email verification code reader for job-apply-bot.
Polls Gmail via IMAP and extracts the latest verification code.

Usage:
  uv run python email_code.py                      # fetch latest code immediately
  uv run python email_code.py --wait               # wait up to 90s for new code
  uv run python email_code.py --wait --sender noreply@oracle  # filter by sender
"""

import imaplib
import email
import re
import ssl
import time
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

PROFILE_PATH = Path(__file__).parent / "profile.json"

# Only look at emails received within this window to avoid stale codes
RECENT_MINUTES = 10


def get_credentials():
    profile = json.loads(PROFILE_PATH.read_text())
    gmail = profile.get("gmail", {})
    return gmail.get("email"), gmail.get("app_password")


def extract_code(text: str) -> str | None:
    """Extract verification code — prefer 6-digit, then 8-digit, then 4-digit."""
    for pat in [r'\b(\d{6})\b', r'\b(\d{8})\b', r'\b(\d{4})\b']:
        matches = re.findall(pat, text)
        if matches:
            return matches[0]
    return None


def _imap_date_str(dt: datetime) -> str:
    """Format datetime as IMAP SINCE date string (e.g. '12-Oct-2026')."""
    return dt.strftime("%d-%b-%Y")


def fetch_latest_code(sender_hint: str = "", subject_hint: str = "",
                       since_minutes: int = RECENT_MINUTES) -> str | None:
    """Fetch the most recent verification code from Gmail inbox.

    Only considers emails received in the last `since_minutes` minutes
    so stale codes from previous applications are never returned.
    """
    gmail_email, app_password = get_credentials()
    if not gmail_email or not app_password:
        print("Gmail credentials not found in profile.json")
        return None

    try:
        # Use DNS-over-HTTPS to bypass DNS hijacking (system DNS may return fake IPs)
        import urllib.request as _ureq, json as _json
        _doh_ctx = ssl.create_default_context()
        _req = _ureq.Request(
            "https://1.1.1.1/dns-query?name=imap.gmail.com&type=A",
            headers={"Accept": "application/dns-json"},
        )
        _resp = _json.loads(_ureq.urlopen(_req, context=_doh_ctx, timeout=5).read())
        _real_ip = next(
            (a["data"] for a in _resp.get("Answer", []) if a["type"] == 1), "imap.gmail.com"
        )
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.options |= getattr(ssl, "OP_IGNORE_UNEXPECTED_EOF", 0)
        mail = imaplib.IMAP4_SSL(_real_ip, 993, ssl_context=ssl_ctx)
        mail.login(gmail_email, app_password)
        mail.select("INBOX")

        # Narrow search to today (IMAP SINCE is date-granular, we filter time below)
        since_dt = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        since_str = _imap_date_str(since_dt)
        _, data = mail.search(None, f'(SINCE "{since_str}")')
        email_ids = data[0].split()

        if not email_ids:
            mail.logout()
            return None

        # Iterate newest-first
        for eid in reversed(email_ids):
            _, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            # Time check: reject emails older than since_minutes
            date_str = msg.get("Date", "")
            try:
                from email.utils import parsedate_to_datetime
                msg_dt = parsedate_to_datetime(date_str)
                if msg_dt.tzinfo is None:
                    msg_dt = msg_dt.replace(tzinfo=timezone.utc)
                if msg_dt < since_dt:
                    continue
            except Exception:
                pass  # if we can't parse the date, allow it through

            from_addr = msg.get("From", "").lower()
            if sender_hint and sender_hint.lower() not in from_addr:
                continue

            subject = msg.get("Subject", "").lower()
            if subject_hint and subject_hint.lower() not in subject:
                continue

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            code = extract_code(body)
            if code:
                print(f"Found code: {code}  (from: {from_addr[:60]})")
                mail.logout()
                return code

        mail.logout()
        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def wait_for_code(sender_hint: str = "", subject_hint: str = "",
                   timeout: int = 90, poll_interval: int = 5) -> str | None:
    """Poll Gmail until a fresh verification code arrives or timeout."""
    print(f"Waiting for verification code (up to {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        code = fetch_latest_code(sender_hint, subject_hint, since_minutes=RECENT_MINUTES)
        if code:
            return code
        time.sleep(poll_interval)
    print("Timeout — no code received")
    return None


if __name__ == "__main__":
    args = sys.argv[1:]
    do_wait = "--wait" in args
    sender = ""
    subject = ""
    for i, a in enumerate(args):
        if a == "--sender" and i + 1 < len(args):
            sender = args[i + 1]
        if a == "--subject" and i + 1 < len(args):
            subject = args[i + 1]

    if do_wait:
        code = wait_for_code(sender_hint=sender, subject_hint=subject)
    else:
        code = fetch_latest_code(sender_hint=sender, subject_hint=subject)

    if code:
        print(code)
    else:
        print("NO_CODE_FOUND")
        sys.exit(1)
