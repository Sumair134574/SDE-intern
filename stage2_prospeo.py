"""
stages/stage2_prospeo.py
Stage 2 — Prospeo
Given a list of company domains, return C-suite / VP-level decision-makers
with their LinkedIn profile URLs.

Prospeo API docs: https://prospeo.io/api-docs/search-person
Auth: X-KEY header
Endpoint: POST https://api.prospeo.io/search-person
"""

import time
from typing import Any

import requests

from utils.logger import get_logger
from utils.retry import with_retry

logger = get_logger(__name__)

BASE_URL = "https://api.prospeo.io"


def find_decision_makers(
    domains: list[str], config: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    For each domain, fetch decision-makers from Prospeo.

    Returns:
        List of prospect dicts with keys:
            name, first_name, title, company_domain, linkedin_url, company_name
    """
    api_key = config["PROSPEO_API_KEY"]

    headers = {
        "X-KEY": api_key,
        "Content-Type": "application/json",
    }

    all_prospects: list[dict[str, Any]] = []
    seen_linkedin: set[str] = set()

    for i, domain in enumerate(domains, 1):
        logger.info(f"  Prospeo [{i}/{len(domains)}] → {domain}")
        prospects = _fetch_domain_prospects(domain, headers, seen_linkedin)
        all_prospects.extend(prospects)
        logger.info(f"    → {len(prospects)} decision-makers at {domain}")

        if i < len(domains):
            time.sleep(0.5)

    return all_prospects


def _fetch_domain_prospects(
    domain: str,
    headers: dict[str, str],
    seen_linkedin: set[str],
) -> list[dict[str, Any]]:
    """Fetch decision-makers for a single domain using Prospeo search-person API."""

    # Exact format from Prospeo docs
    payload = {
        "filters": {
            "company": {
                "websites": {
                    "include": [domain]
                }
            },
            "person_seniority": {
                "include": ["C-Suite", "Vice President", "Director", "Founder/Owner"]
            }
        },
        "page": 1
    }

    try:
        response = with_retry(
            lambda: requests.post(
                f"{BASE_URL}/search-person",
                json=payload,
                headers=headers,
                timeout=30,
            )
        )
    except Exception as e:
        logger.warning(f"Prospeo error for {domain}: {e}")
        return []

    if response.status_code == 401:
        raise ValueError("Prospeo: Invalid API key. Check PROSPEO_API_KEY in .env")
    if response.status_code == 429:
        logger.warning("Prospeo rate limit — sleeping 5s")
        time.sleep(5)
        return []
    if not response.ok:
        logger.warning(f"Prospeo returned {response.status_code} for {domain}: {response.text[:200]}")
        return []

    data = response.json()

    if data.get("error"):
        logger.warning(f"Prospeo error for {domain}: {data}")
        return []

    results_list = data.get("results", [])
    if not isinstance(results_list, list):
        return []

    results: list[dict[str, Any]] = []

    for item in results_list:
        person = item.get("person", {})
        company = item.get("company", {})

        title = (person.get("job_title") or person.get("title", "")).strip()

        # Get LinkedIn URL from socials
        linkedin = ""
        socials = person.get("socials", {})
        if isinstance(socials, dict):
            linkedin = socials.get("linkedin_url", "")
        if not linkedin:
            linkedin = person.get("linkedin_url", "").strip()

        if not linkedin or linkedin in seen_linkedin:
            continue
        seen_linkedin.add(linkedin)

        first = person.get("first_name", "")
        last = person.get("last_name", "")
        name = f"{first} {last}".strip()
        company_name = company.get("name", domain)

        # Capture email if already present in search results
        email_data = person.get("email_data", {}) or {}
        email = email_data.get("email") or person.get("email", "")

        results.append({
            "name": name,
            "first_name": first,
            "title": title,
            "company_domain": domain,
            "company_name": company_name,
            "linkedin_url": linkedin,
            "email": email,
        })

    return results
