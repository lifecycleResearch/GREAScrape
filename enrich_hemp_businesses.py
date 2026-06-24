#!/usr/bin/env python3
"""
CA Industrial Hemp Business Enrichment Pipeline
Uses ScrapeGraphAI SmartScraperGraph to scrape contact info from business websites.
"""

import os
import csv
import json
import time
from pathlib import Path

# API Keys - read from environment
OPENROUTER_API_KEY=os.environ.get("OPENROUTER_API_KEY", "")
COHERE_API_KEY=os.environ.get("COHERE_API_KEY", "")

BASE_DIR = Path("/teamspace/studios/this_studio")
OUTPUT_CSV = BASE_DIR / "business_enrichment_final.csv"

# Businesses with known websites to scrape
BUSINESSES_TO_SCRAPE = [
    {"name": "Advanced Cosmetic Research Laboratories", "website": "https://www.advancedcosmeticlabs.com", "city": "Chatsworth"},
    {"name": "Best Formulations PC LLC", "website": "https://www.bestformulations.com", "city": "Huntington Beach"},
    {"name": "Common Collabs, LLC", "website": "http://www.commoncollabs.com", "city": "Fullerton"},
    {"name": "Coastal Contract Packaging, Inc.", "website": "https://www.coastalcontractpackaging.com", "city": "Ventura"},
    {"name": "GT Ventures", "website": "https://gtventures.vc/", "city": "El Monte"},
    {"name": "Merle Norman Cosmetics, Inc", "website": "https://www.merlenorman.com", "city": "Los Angeles"},
    {"name": "Nufill Biosciences Corporation", "website": "https://nufillbio.com", "city": "Irvine"},
    {"name": "Rock Island Refrigerated", "website": "http://www.therockrd.com", "city": "Petaluma"},
    {"name": "The Planetone Company DBA The Planetone Company", "website": "https://www.theplanetonecompany.com", "city": "Ventura"},
    {"name": "Trans-India Products, Inc DBA Shikai Products", "website": "https://shikai.com", "city": "Graton"},
    {"name": "Vertosa Wellness, LLC", "website": "https://www.vertosa.com", "city": "Walnut Creek"},
    {"name": "Yuzu Soap LLC DBA Yuzu Soap", "website": "https://www.yuzusoap.com", "city": "Fremont"},
]

PROMPT_TEMPLATE = """Extract the following information for this business from the webpage content:
1. Phone number (main contact or headquarters phone)
2. Email address (contact, info, or sales email)
3. Full street address (headquarters or main office address with street, city, state, zip)
4. Owner name, founder name, or CEO name

Return ONLY a valid JSON object with exactly these four keys: phone, email, address, owner.
Use empty string "" for any value you cannot find. Do not include any other text or explanation."""


def scrape_business(business_name: str, website: str, api_key: str) -> dict:
    """
    Use ScrapeGraphAI SmartScraperGraph to scrape contact info from a business website.
    """
    from scrapegraphai.graphs import SmartScraperGraph

    graph_config = {
        "llm": {
            "api_key": api_key,
            "model": "openrouter/google/gemini-2.0-flash-001",
            "temperature": 0,
            "max_tokens": 512,
        },
        "verbose": False,
        "headless": True,
    }

    try:
        smart_scraper = SmartScraperGraph(
            prompt=PROMPT_TEMPLATE,
            source=website,
            config=graph_config,
        )
        result = smart_scraper.run()
        return _parse_result(result)
    except Exception as e:
        print(f"    [SCRAPE ERROR] {business_name}: {e}")
    return {"phone": "", "email": "", "address": "", "owner": ""}


def _parse_result(result) -> dict:
    """Parse ScrapeGraphAI result into standardized dict."""
    import re

    if isinstance(result, dict):
        return {
            "phone": str(result.get("phone", "")).strip(),
            "email": str(result.get("email", "")).strip(),
            "address": str(result.get("address", "")).strip(),
            "owner": str(result.get("owner", "")).strip(),
        }
    elif isinstance(result, str):
        try:
            parsed = json.loads(result)
            return {
                "phone": str(parsed.get("phone", "")).strip(),
                "email": str(parsed.get("email", "")).strip(),
                "address": str(parsed.get("address", "")).strip(),
                "owner": str(parsed.get("owner", "")).strip(),
            }
        except (json.JSONDecodeError, TypeError):
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    return {
                        "phone": str(parsed.get("phone", "")).strip(),
                        "email": str(parsed.get("email", "")).strip(),
                        "address": str(parsed.get("address", "")).strip(),
                        "owner": str(parsed.get("owner", "")).strip(),
                    }
                except (json.JSONDecodeError, TypeError):
                    pass
    return {"phone": "", "email": "", "address": "", "owner": ""}


def enrich_with_scrapegraphai():
    """
    Main enrichment pipeline:
    1. Scrape business websites using ScrapeGraphAI
    2. Compile results into JSON output
    3. Output coverage statistics
    """
    if not OPENROUTER_API_KEY and not COHERE_API_KEY:
        print("Error: No API keys found. Set OPENROUTER_API_KEY or COHERE_API_KEY env var.")
        return

    api_key = OPENROUTER_API_KEY or COHERE_API_KEY
    results = {}
    has_website = [b for b in BUSINESSES_TO_SCRAPE if b["website"]]

    print(f"🔄 Scraping {len(has_website)} business websites with ScrapeGraphAI...")

    for i, biz in enumerate(has_website, 1):
        print(f"  [{i}/{len(has_website)}] {biz['name']}")
        info = scrape_business(biz["name"], biz["website"], api_key)
        results[biz["name"]] = info

        if any(v for v in info.values()):
            found = [k for k, v in info.items() if v]
            print(f"         Found: {', '.join(found)}")
        else:
            print(f"         No data found")

        if i < len(has_website):
            time.sleep(2)

    # Save results
    output_path = BASE_DIR / "scrapegraphai_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Stats
    has_phone = sum(1 for v in results.values() if v.get("phone"))
    has_email = sum(1 for v in results.values() if v.get("email"))
    has_address = sum(1 for v in results.values() if v.get("address"))
    has_owner = sum(1 for v in results.values() if v.get("owner"))

    print(f"\n✅ Scraping complete. Results saved to {output_path}")
    print(f"   Total businesses: {len(results)}")
    print(f"   With phone: {has_phone}")
    print(f"   With email: {has_email}")
    print(f"   With address: {has_address}")
    print(f"   With owner: {has_owner}")

    return results


if __name__ == "__main__":
    enrich_with_scrapegraphai()
