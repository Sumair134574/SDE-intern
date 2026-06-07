"""
utils/checkpoint.py
Safety checkpoint — shows a summary and asks for explicit confirmation
before any emails are sent. This is the "human in the loop" guardrail.
"""

from typing import Any

BOLD = "\033[1m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def safety_checkpoint(
    contacts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Prompt the user for confirmation before sending emails.
    Supports: send all, send N, or abort.

    Returns:
        The subset of contacts approved for sending.
    """
    total = len(contacts)

    print(f"\n{YELLOW}{BOLD}⚠  CHECKPOINT — Review before sending{RESET}")
    print(f"  {total} email(s) are queued and ready to fire.\n")
    print(f"  Options:")
    print(f"    {BOLD}[A]{RESET}  Send all {total} emails")
    print(f"    {BOLD}[N]{RESET}  Send first N emails  (you choose N)")
    print(f"    {BOLD}[Q]{RESET}  Abort — send nothing\n")

    while True:
        choice = input("  Your choice [A / N / Q]: ").strip().upper()

        if choice == "Q":
            print(f"  {RED}Aborted.{RESET} No emails sent.")
            return []

        if choice == "A":
            print(f"  {GREEN}✓ Confirmed — sending all {total} emails.{RESET}\n")
            return contacts

        if choice == "N":
            while True:
                raw = input(f"  How many to send (1–{total})? ").strip()
                if raw.isdigit():
                    n = int(raw)
                    if 1 <= n <= total:
                        print(f"  {GREEN}✓ Confirmed — sending first {n} email(s).{RESET}\n")
                        return contacts[:n]
                print(f"  Please enter a number between 1 and {total}.")

        print("  Invalid choice. Please enter A, N, or Q.")
