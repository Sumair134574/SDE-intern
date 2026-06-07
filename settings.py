"""
config/settings.py
Loads API keys and pipeline settings from a .env file.
"""

import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # python-dotenv optional — env vars still work


# ── Required keys ────────────────────────────────────────────────────────────
_REQUIRED_KEYS = [
    "OCEAN_API_KEY",
    "PROSPEO_API_KEY",
    "EAZYREACH_API_KEY",
    "BREVO_API_KEY",
    "BREVO_SENDER_EMAIL",
    "BREVO_SENDER_NAME",
]

# ── Optional tuning knobs ─────────────────────────────────────────────────────
_DEFAULTS = {
    "OCEAN_MAX_COMPANIES": "10",      # Max lookalike companies to pull
    "PROSPEO_TITLES": "CEO,CTO,COO,CMO,VP,Director",  # Seniority filter
    "EAZYREACH_DELAY_MS": "500",      # ms to wait between LinkedIn resolutions
    "BREVO_DELAY_MS": "200",          # ms between outreach sends
    "MAX_EMAILS_PER_RUN": "50",       # Hard cap — prevents accidental mass-blast
    "DRY_RUN": "false",               # Set to "true" to skip actual email sends
}


def load_config() -> dict[str, Any]:
    """Return a merged config dict of env vars + defaults."""
    cfg: dict[str, Any] = {}

    for key, default in _DEFAULTS.items():
        cfg[key] = os.getenv(key, default)

    for key in _REQUIRED_KEYS:
        cfg[key] = os.getenv(key, "")

    # Type coercions
    cfg["OCEAN_MAX_COMPANIES"] = int(cfg["OCEAN_MAX_COMPANIES"])
    cfg["EAZYREACH_DELAY_MS"] = int(cfg["EAZYREACH_DELAY_MS"])
    cfg["BREVO_DELAY_MS"] = int(cfg["BREVO_DELAY_MS"])
    cfg["MAX_EMAILS_PER_RUN"] = int(cfg["MAX_EMAILS_PER_RUN"])
    cfg["DRY_RUN"] = cfg["DRY_RUN"].lower() in ("true", "1", "yes")

    return cfg


def validate_config(cfg: dict[str, Any]) -> None:
    """Raise ValueError if any required key is missing."""
    missing = [k for k in _REQUIRED_KEYS if not cfg.get(k)]
    if missing:
        raise ValueError(
            f"\n[CONFIG ERROR] Missing required environment variables:\n"
            + "\n".join(f"  • {k}" for k in missing)
            + "\n\nCopy .env.example → .env and fill in your API keys.\n"
        )
