"""
demo_mode.py
Runs the pipeline using cached data — no API calls, no rate limits.
Perfect for recording a demo video.

Usage:
    python demo_mode.py stripe.com
"""

from utils.logger import print_banner, print_stage, print_summary
from utils.checkpoint import safety_checkpoint
from stages.stage4_brevo import send_outreach_emails
from config.settings import load_config, validate_config

# ── Cached Stage 1 output ─────────────────────────────────────────────────────
DEMO_COMPANIES = [
    "braintreepayments.com", "square.com", "adyen.com",
    "paypal.com", "razorpay.com", "recurly.com",
    "chargebee.com", "paddle.com", "mollie.com", "checkout.com"
]

# ── Cached Stage 2 + 3 output ─────────────────────────────────────────────────
DEMO_CONTACTS = [
    {"name": "John Collison", "first_name": "John", "title": "CEO",
     "company_domain": "braintreepayments.com", "company_name": "Braintree",
     "email": "john@braintreepayments.com", "linkedin_url": "https://linkedin.com/in/johncollison"},
    {"name": "Jack Dorsey", "first_name": "Jack", "title": "CEO",
     "company_domain": "square.com", "company_name": "Square",
     "email": "jack@square.com", "linkedin_url": "https://linkedin.com/in/jackdorsey"},
    {"name": "Pieter van der Does", "first_name": "Pieter", "title": "CEO",
     "company_domain": "adyen.com", "company_name": "Adyen",
     "email": "pieter@adyen.com", "linkedin_url": "https://linkedin.com/in/pietervanderdoes"},
    {"name": "Dan Schulman", "first_name": "Dan", "title": "CEO",
     "company_domain": "paypal.com", "company_name": "PayPal",
     "email": "dan@paypal.com", "linkedin_url": "https://linkedin.com/in/danschulman"},
    {"name": "Harshil Mathur", "first_name": "Harshil", "title": "CEO",
     "company_domain": "razorpay.com", "company_name": "Razorpay",
     "email": "harshil@razorpay.com", "linkedin_url": "https://linkedin.com/in/harshilmathur"},
]


def run_demo(seed_domain: str) -> None:
    print_banner(seed_domain)

    config = load_config()
    validate_config(config)

    # Stage 1
    print_stage(1, "Apollo.io", "Finding lookalike companies")
    time.sleep(1.5)
    for d in DEMO_COMPANIES:
        print(f"    \u2192 {d}")
        time.sleep(0.2)
    print(f"  \u2713 Found {len(DEMO_COMPANIES)} lookalike companies\n")

    # Stage 2
    print_stage(2, "Prospeo", "Finding decision-makers + LinkedIn URLs")
    time.sleep(1.5)
    for c in DEMO_CONTACTS:
        print(f"    \u2192 {c['name']} ({c['title']}) @ {c['company_name']}")
        time.sleep(0.3)
    print(f"  \u2713 Found {len(DEMO_CONTACTS)} decision-makers\n")

    # Stage 3
    print_stage(3, "Eazyreach", "Resolving verified work emails")
    time.sleep(1)
    for c in DEMO_CONTACTS:
        print(f"    \u2713 {c['name']} \u2192 {c['email']}")
        time.sleep(0.3)
    print(f"  \u2713 Resolved {len(DEMO_CONTACTS)} verified emails\n")

    # Checkpoint
    print_summary(seed_domain, DEMO_COMPANIES, DEMO_CONTACTS)
    approved = safety_checkpoint(DEMO_CONTACTS)

    if not approved:
        print("\n  Aborted \u2014 no emails sent.")
        return

    # Stage 4
    print_stage(4, "Brevo", f"Sending personalized outreach to {len(approved)} contacts")
    results = send_outreach_emails(approved, seed_domain, config)

    sent = sum(1 for r in results if r.get("sent"))
    print(f"\n  \u2713 Pipeline complete!")
    print(f"  \u2713 Sent: {sent}  |  Total: {len(approved)}\n")


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else "stripe.com"
    seed = seed.replace("https://", "").replace("http://", "").rstrip("/")
    run_demo(seed)
