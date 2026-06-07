"""
stages/stage4_brevo.py
Stage 4 — Brevo (formerly Sendinblue)
Send a personalized cold-outreach email to each resolved contact.

Brevo API docs: https://developers.brevo.com/
Auth: api-key header
Endpoint: POST /v3/smtp/email
"""

import time
from typing import Any

import requests

from utils.logger import get_logger
from utils.retry import with_retry

logger = get_logger(__name__)

BASE_URL = "https://api.brevo.com/v3"


def send_outreach_emails(
    contacts: list[dict[str, Any]],
    seed_domain: str,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Send one personalized outreach email per contact via Brevo.

    Returns:
        List of result dicts with keys: email, sent (bool), message_id, error.
    """
    api_key = config["BREVO_API_KEY"]
    print("BREVO KEY:", api_key[:20])
    print("KEY LENGTH:", len(api_key))
    sender_email = config["BREVO_SENDER_EMAIL"]
    sender_name = config["BREVO_SENDER_NAME"]
    delay_ms = config["BREVO_DELAY_MS"]
    dry_run = config["DRY_RUN"]
    max_emails = config["MAX_EMAILS_PER_RUN"]

    if dry_run:
        logger.info("DRY RUN mode — emails will NOT actually be sent")
        print("  ⚠  DRY RUN — printing emails, not sending")

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    results: list[dict[str, Any]] = []
    contacts_to_send = contacts[:max_emails]

    for i, contact in enumerate(contacts_to_send, 1):
        email = contact.get("email")
        if not email:
            continue

        name = contact.get("name", "")
        first_name = contact.get("first_name") or name.split()[0] if name else "there"
        title = contact.get("title", "")
        company = contact.get("company_name", contact.get("company_domain", ""))

        subject = _build_subject(first_name, company, seed_domain)
        html_body = _build_email_html(first_name, title, company, seed_domain, sender_name)
        text_body = _build_email_text(first_name, title, company, seed_domain, sender_name)

        logger.info(f"  Brevo [{i}/{len(contacts_to_send)}] → {email} ({name} @ {company})")

        if dry_run:
            print(f"\n  {'─'*60}")
            print(f"  TO:      {name} <{email}>")
            print(f"  SUBJECT: {subject}")
            print(f"  BODY:\n{text_body}")
            results.append({"email": email, "sent": False, "dry_run": True})
            continue

        result = _send_one(
            to_email=email,
            to_name=name,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            sender_email=sender_email,
            sender_name=sender_name,
            headers=headers,
        )
        results.append(result)

        if result["sent"]:
            logger.info(f"    ✓ Sent (message_id={result.get('message_id')})")
        else:
            logger.warning(f"    ✗ Failed: {result.get('error')}")

        if i < len(contacts_to_send):
            time.sleep(delay_ms / 1000)

    return results


def _send_one(
    to_email: str,
    to_name: str,
    subject: str,
    html_body: str,
    text_body: str,
    sender_email: str,
    sender_name: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    """Send a single transactional email via Brevo."""

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_body,
        "textContent": text_body,
        "tags": ["outreach-pipeline"],
    }

    print("API KEY SENT:", headers["api-key"])
    print("URL:", f"{BASE_URL}/smtp/email")
    print("HEADERS:", headers)
    try:
        response = with_retry(
            lambda: requests.post(
                f"{BASE_URL}/smtp/email",
                json=payload,
                headers=headers,
                timeout=30,
            )
        )
        
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
    except Exception as e:
        return {"email": to_email, "sent": False, "error": str(e)}

    if response.status_code == 401:
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
        raise ValueError("Brevo 401")

    if response.status_code == 429:
        logger.warning("Brevo rate limit hit — sleeping 5s")
        time.sleep(5)
        return {"email": to_email, "sent": False, "error": "rate_limited"}

    if not response.ok:
        return {
            "email": to_email,
            "sent": False,
            "error": f"HTTP {response.status_code}: {response.text[:200]}",
        }

    data = response.json()
    return {
        "email": to_email,
        "sent": True,
        "message_id": data.get("messageId", ""),
    }


# ── Email copy ────────────────────────────────────────────────────────────────

def _build_subject(first_name: str, company: str, seed_domain: str) -> str:
    """Craft a subject line that feels personal, not blasted."""
    seed_name = seed_domain.split(".")[0].capitalize()
    return f"Quick question for you, {first_name}"


def _build_email_text(
    first_name: str,
    title: str,
    company: str,
    seed_domain: str,
    sender_name: str,
) -> str:
    seed_name = seed_domain.split(".")[0].capitalize()

    return f"""Hi {first_name},

I came across {company} while looking at companies similar to {seed_name} — the overlap in what you're building caught my attention.

I'll keep this short: we help growth-stage companies like yours close the gap between their sales motion and the accounts most likely to convert. Most teams we work with see meaningful pipeline improvement within the first 60 days.

Would it make sense to spend 15 minutes this week or next to see if there's a fit? If the timing isn't right, no hard feelings — I just thought the match was worth a note.

{sender_name}

P.S. If you're not the right person for this, I'd appreciate a point in the right direction.
"""


def _build_email_html(
    first_name: str,
    title: str,
    company: str,
    seed_domain: str,
    sender_name: str,
) -> str:
    seed_name = seed_domain.split(".")[0].capitalize()
    text = _build_email_text(first_name, title, company, seed_domain, sender_name)
    # Simple HTML wrap — clean, renders well on all clients
    paragraphs = "".join(
        f"<p style='margin:0 0 14px 0'>{line}</p>"
        for line in text.strip().split("\n")
        if line.strip()
    )
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;font-size:15px;color:#222;max-width:600px;margin:40px auto;padding:0 20px;line-height:1.6">
  {paragraphs}
</body>
</html>
"""
