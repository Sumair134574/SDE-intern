"""
utils/logger.py
Logging setup + CLI pretty-print helpers.
"""

import logging
import sys
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger writing to pipeline.log and stderr."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # File handler — full debug log
        fh = logging.FileHandler("pipeline.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

        # Console handler — INFO and above only
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.WARNING)
        ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger


# ── CLI pretty-print helpers ──────────────────────────────────────────────────

BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_banner(seed_domain: str) -> None:
    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  🚀 Automated Cold-Outreach Pipeline{RESET}")
    print(f"{'═' * 60}")
    print(f"  Seed domain : {CYAN}{seed_domain}{RESET}")
    print(f"  Stages      : Ocean.io → Prospeo → Eazyreach → Brevo")
    print(f"{'─' * 60}\n")


def print_stage(number: int, tool: str, description: str) -> None:
    print(f"{BOLD}Stage {number} · {tool}{RESET}  {description}")


def print_summary(
    seed_domain: str,
    companies: list[str],
    contacts: list[dict[str, Any]],
) -> None:
    """Print a pre-send summary table for the safety checkpoint."""
    print(f"\n{'═' * 60}")
    print(f"{BOLD}  📋 Pre-Send Summary{RESET}")
    print(f"{'─' * 60}")
    print(f"  Seed domain         : {seed_domain}")
    print(f"  Lookalike companies : {len(companies)}")
    print(f"  Verified contacts   : {len(contacts)}")
    print(f"\n  {'NAME':<25} {'TITLE':<25} {'EMAIL':<30}")
    print(f"  {'─'*25} {'─'*25} {'─'*30}")
    for c in contacts:
        name = (c.get("name") or "")[:24]
        title = (c.get("title") or "")[:24]
        email = (c.get("email") or "")[:29]
        print(f"  {name:<25} {title:<25} {email:<30}")
    print(f"{'─' * 60}")
