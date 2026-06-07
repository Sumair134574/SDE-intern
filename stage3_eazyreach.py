"""
stages/stage3_eazyreach.py
Stage 3 — Email Resolution
Prospeo's search-person already returns email data in results.
This stage extracts those emails and fills any gaps using
domain-pattern guessing as fallback.
"""

import time
import re
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


def resolve_emails(
    prospects: list[dict[str, Any]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Extract verified emails from prospect data (already fetched in Stage 2).
    Falls back to email pattern guessing for prospects without emails.

    Returns:
        The same prospect list, each dict updated with 'email' key.
    """
    resolved = 0
    guessed = 0
    failed = 0

    for prospect in prospects:
        # ── Try email already in prospect data from Prospeo ──────────────────
        email = _extract_existing_email(prospect)

        if email:
            prospect["email"] = email
            prospect["email_status"] = "verified"
            resolved += 1
            logger.info(f"  ✓ {prospect.get('name')} → {email}")
            continue

        # ── Fallback: guess email from name + domain pattern ─────────────────
        guessed_email = _guess_email(prospect)
        if guessed_email:
            prospect["email"] = guessed_email
            prospect["email_status"] = "guessed"
            guessed += 1
            logger.info(f"  ~ {prospect.get('name')} → {guessed_email} (guessed)")
        else:
            prospect["email"] = None
            prospect["email_status"] = "not_found"
            failed += 1

    logger.info(f"Emails: {resolved} verified, {guessed} guessed, {failed} failed")
    return prospects


def _extract_existing_email(prospect: dict[str, Any]) -> str | None:
    """Try to get email from data already present in prospect dict."""
    # Direct email field
    email = prospect.get("email") or prospect.get("work_email") or ""
    if email and _looks_valid(email):
        return email.lower().strip()

    # Nested email_data
    email_data = prospect.get("email_data", {}) or {}
    email = email_data.get("email", "")
    if email and _looks_valid(email):
        return email.lower().strip()

    return None


def _guess_email(prospect: dict[str, Any]) -> str | None:
    """
    Guess work email from first name + domain using common patterns.
    Patterns tried: firstname@domain, f.lastname@domain, firstnamelastname@domain
    """
    first = (prospect.get("first_name") or "").lower().strip()
    name = (prospect.get("name") or "").lower().strip()
    domain = (prospect.get("company_domain") or "").strip()

    if not domain or not first:
        return None

    # Clean names — remove special chars
    first = re.sub(r"[^a-z]", "", first)
    parts = name.split()
    last = re.sub(r"[^a-z]", "", parts[-1]) if len(parts) > 1 else ""

    if not first:
        return None

    # Most common pattern: firstname@company.com
    return f"{first}@{domain}"


def _looks_valid(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1] and len(email) > 5
