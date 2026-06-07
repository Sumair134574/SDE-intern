#!/usr/bin/env python3
"""
Automated Cold-Outreach Pipeline
One input → Four stages → Emails sent. Zero manual steps.

Usage:
    python main.py <seed_domain>
    python main.py stripe.com
"""

import sys
import json
import time
from pathlib import Path

from config.settings import load_config, validate_config
from stages.stage1_ocean import find_lookalike_companies
from stages.stage2_prospeo import find_decision_makers
from stages.stage3_eazyreach import resolve_emails
from stages.stage4_brevo import send_outreach_emails
from utils.logger import get_logger, print_banner, print_stage, print_summary
from utils.checkpoint import safety_checkpoint

logger = get_logger(__name__)


def run_pipeline(seed_domain: str) -> None:
    """
    Execute the full outreach pipeline end-to-end.

    Args:
        seed_domain: The seed company domain (e.g. stripe.com)
    """
    print_banner(seed_domain)

    # ── Load & validate config ───────────────────────────────────────────────
    config = load_config()
    validate_config(config)

    results = {}
    start_time = time.time()

    # ── STAGE 1 · Ocean.io → Lookalike Companies ────────────────────────────
    print_stage(1, "Ocean.io", "Finding lookalike companies")
    company_domains = find_lookalike_companies(seed_domain, config)
    results["stage1_domains"] = company_domains
    logger.info(f"Stage 1 complete → {len(company_domains)} companies found")
    print(f"  ✓ Found {len(company_domains)} lookalike companies\n")

    if not company_domains:
        logger.warning("No lookalike companies found. Exiting.")
        print("  ✗ No lookalike companies found. Try a different seed domain.")
        sys.exit(1)

    # ── STAGE 2 · Prospeo → Decision-Makers ─────────────────────────────────
    print_stage(2, "Prospeo", "Finding decision-makers + LinkedIn URLs")
    prospects = find_decision_makers(company_domains, config)
    results["stage2_prospects"] = prospects
    logger.info(f"Stage 2 complete → {len(prospects)} prospects found")
    print(f"  ✓ Found {len(prospects)} decision-makers across {len(company_domains)} companies\n")

    if not prospects:
        logger.warning("No prospects found. Exiting.")
        print("  ✗ No decision-makers found.")
        sys.exit(1)

    # ── STAGE 3 · Eazyreach → Verified Emails ───────────────────────────────
    print_stage(3, "Eazyreach", "Resolving verified work emails")
    contacts = resolve_emails(prospects, config)
    results["stage3_contacts"] = contacts
    verified = [c for c in contacts if c.get("email")]
    logger.info(f"Stage 3 complete → {len(verified)}/{len(contacts)} emails resolved")
    print(f"  ✓ Resolved {len(verified)} verified emails from {len(prospects)} prospects\n")

    if not verified:
        logger.warning("No verified emails resolved. Exiting.")
        print("  ✗ Could not resolve any work emails.")
        sys.exit(1)

    # ── SAFETY CHECKPOINT ────────────────────────────────────────────────────
    print_summary(seed_domain, company_domains, verified)
    approved_contacts = safety_checkpoint(verified)

    if not approved_contacts:
        print("\n  Aborted — no emails sent.")
        sys.exit(0)

    # ── STAGE 4 · Brevo → Send Outreach Emails ──────────────────────────────
    print_stage(4, "Brevo", f"Sending personalized outreach to {len(approved_contacts)} contacts")
    send_results = send_outreach_emails(approved_contacts, seed_domain, config)
    results["stage4_results"] = send_results

    sent = sum(1 for r in send_results if r.get("sent"))
    failed = len(send_results) - sent
    elapsed = round(time.time() - start_time, 1)

    print(f"\n  ✓ Pipeline complete in {elapsed}s")
    print(f"  ✓ Sent: {sent}  |  Failed: {failed}\n")

    # ── Save run log ─────────────────────────────────────────────────────────
    log_path = Path(f"run_log_{int(time.time())}.json")
    log_path.write_text(json.dumps(results, indent=2))
    print(f"  📄 Full run log saved → {log_path}\n")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    seed_domain = sys.argv[1].strip().lower()
    # Strip protocol if someone pastes a URL
    seed_domain = seed_domain.replace("https://", "").replace("http://", "").rstrip("/")

    run_pipeline(seed_domain)


if __name__ == "__main__":
    main()
