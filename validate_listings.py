#!/usr/bin/env python3
"""
Validate financial advisor listings in Airtable.

Scans advisor names, descriptions, and categories for non-advisor businesses
that may have been scraped from Google Maps (e.g., insurance agencies, tax prep
chains, banks, auto shops, restaurants).

Usage:
    python3 validate_listings.py              # Scan and report
    python3 validate_listings.py --remove     # Remove LIKELY NOT ADVISOR records from Airtable
    python3 validate_listings.py --remove-all # Remove LIKELY NOT ADVISOR + REVIEW NEEDED records
"""
import os
import sys
import csv
import re
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Advisors")
CHUNK_SIZE = 10

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(BASE_DIR, "validation_results.csv")
FLAGGED_FILE = os.path.join(BASE_DIR, "validation_flagged.csv")

# ==============================
# KEYWORD SCORING
# ==============================

# Strong positive signals -- these are financial advisor businesses
POSITIVE_KEYWORDS = [
    # Core advisor terms
    "financial advisor", "investment advisor", "wealth management",
    "financial planner", "certified financial planner", "cfp", "cfa",
    "fiduciary", "retirement planning", "financial planning",
    "portfolio management", "asset management", "estate planning",
    "registered investment advisor", "ria", "fee-only", "wealth manager",
    # Major advisor brand names
    "edward jones", "merrill lynch", "morgan stanley", "raymond james",
    "ameriprise", "northwestern mutual", "charles schwab", "fidelity",
    "lpl financial", "stifel", "baird", "janney",
]

# Strong negative signals -- these are NOT financial advisor businesses
NEGATIVE_KEYWORDS = [
    # Insurance-only
    "insurance agency", "allstate", "state farm", "geico", "progressive",
    "farmers insurance", "liberty mutual",
    # Tax prep chains
    "h&r block", "jackson hewitt", "liberty tax", "tax preparation service",
    # Banks
    "bank", "credit union", "atm", "mortgage", "lending", "loan officer",
    # Real estate
    "real estate", "realty", "realtor", "property management",
    # Auto/mechanical
    "auto", "car wash", "mechanic", "body shop",
    # Food/restaurant
    "restaurant", "pizza", "cafe", "bakery", "bar & grill",
    # Retail
    "liquor", "smoke shop", "pawn", "thrift",
    # Construction/trades
    "plumbing", "electrician", "roofing", "hvac", "landscaping",
    # Legal
    "law firm", "attorney", "lawyer",
    # Medical
    "dentist", "chiropract", "physical therapy", "veterinar",
    # Other non-advisor
    "staffing", "recruiting", "hotel", "motel", "salon", "gym", "church",
]

# Medium negative -- could be advisor-adjacent but usually aren't standalone advisors
MEDIUM_NEGATIVE = [
    "accounting firm", "bookkeeping", "payroll service",
    "tax preparer", "cpa firm",
    "insurance broker",
]


def score_record(fields):
    """Score a record as LIKELY ADVISOR, REVIEW NEEDED, or LIKELY NOT ADVISOR."""
    name = (fields.get("Name") or "").lower()
    description = (fields.get("Description") or "").lower()
    text = f"{name} {description}"

    positive_score = 0
    negative_score = 0
    flags = []

    # Check positive keywords
    for kw in POSITIVE_KEYWORDS:
        if kw in text:
            positive_score += 2
            if positive_score >= 4:
                break  # Strong enough signal

    # Word boundary matching to avoid false positives like "inn" in "Cincinnati"
    def word_match(keyword, text):
        """Check if keyword appears as a whole word/phrase, not inside another word."""
        pattern = r'(?<![a-zA-Z])' + re.escape(keyword) + r'(?![a-zA-Z])'
        return bool(re.search(pattern, text))

    # Check strong negative keywords (match against name only, not city)
    for kw in NEGATIVE_KEYWORDS:
        if word_match(kw, name):
            negative_score += 5
            flags.append(f"NAME: '{kw}'")
        elif word_match(kw, description):
            negative_score += 1
            if negative_score >= 3:
                flags.append(f"DESC: '{kw}'")

    # Check medium negative keywords
    for kw in MEDIUM_NEGATIVE:
        if word_match(kw, name):
            negative_score += 2
            flags.append(f"NAME: '{kw}'")
        elif word_match(kw, text):
            negative_score += 0.5

    # No description at all is a minor flag
    if not description.strip() or len(description.strip()) < 50:
        negative_score += 0.5

    # If negative keywords found in the NAME, don't let auto-generated descriptions override
    name_flags = [f for f in flags if f.startswith("NAME:")]
    has_name_flag = len(name_flags) > 0

    # Classification
    if has_name_flag and negative_score >= 5:
        return "LIKELY NOT ADVISOR", negative_score, positive_score, "; ".join(flags[:3])
    elif negative_score >= 5 and positive_score < 4:
        return "LIKELY NOT ADVISOR", negative_score, positive_score, "; ".join(flags[:3])
    elif has_name_flag and negative_score >= 2:
        return "REVIEW NEEDED", negative_score, positive_score, "; ".join(flags[:3])
    elif negative_score >= 2 and positive_score < 3:
        return "REVIEW NEEDED", negative_score, positive_score, "; ".join(flags[:3])
    else:
        return "LIKELY ADVISOR", negative_score, positive_score, ""


def main():
    from pyairtable import Api
    import time

    remove_all = "--remove-all" in sys.argv
    remove_mode = "--remove" in sys.argv or remove_all

    print(f"\n{'='*62}")
    print(f"  Listing Validation  [{'REMOVE' if remove_mode else 'SCAN'}]")
    print(f"{'='*62}\n")

    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, TABLE_NAME)

    print("Fetching records from Airtable...")
    records = []
    for page in table.iterate(page_size=100):
        records.extend(page)
        print(f"  Fetched {len(records)} records...")
        time.sleep(0.2)
    print(f"Total records: {len(records)}\n")

    # Score all records
    results = []
    likely_advisor = 0
    review_needed = 0
    likely_not = 0

    for r in records:
        fields = r["fields"]
        classification, neg_score, pos_score, flags = score_record(fields)

        results.append({
            "id": r["id"],
            "name": fields.get("Name", ""),
            "city": fields.get("City", ""),
            "state": fields.get("State", ""),
            "classification": classification,
            "neg_score": neg_score,
            "pos_score": pos_score,
            "flags": flags,
        })

        if classification == "LIKELY ADVISOR":
            likely_advisor += 1
        elif classification == "REVIEW NEEDED":
            review_needed += 1
        else:
            likely_not += 1

    print(f"LIKELY ADVISOR:     {likely_advisor}")
    print(f"REVIEW NEEDED:      {review_needed}")
    print(f"LIKELY NOT ADVISOR: {likely_not}")
    print(f"Total:              {len(results)}")

    # Save all results
    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "city", "state", "classification", "neg_score", "pos_score", "flags"])
        writer.writeheader()
        for r in results:
            writer.writerow({k: r[k] for k in writer.fieldnames})
    print(f"\nAll results saved: {RESULTS_FILE}")

    # Save flagged records
    flagged = [r for r in results if r["classification"] != "LIKELY ADVISOR"]
    if flagged:
        with open(FLAGGED_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "city", "state", "classification", "neg_score", "pos_score", "flags"])
            writer.writeheader()
            for r in sorted(flagged, key=lambda x: (-x["neg_score"], x["name"])):
                writer.writerow({k: r[k] for k in writer.fieldnames})
        print(f"Flagged records saved: {FLAGGED_FILE}")

    # Preview LIKELY NOT ADVISOR
    not_advisor = [r for r in results if r["classification"] == "LIKELY NOT ADVISOR"]
    if not_advisor:
        print(f"\n{'-'*60}")
        print(f"LIKELY NOT ADVISOR (top 20):")
        print(f"{'-'*60}")
        for r in sorted(not_advisor, key=lambda x: -x["neg_score"])[:20]:
            print(f"  {r['name']} -- {r['city']}, {r['state']}")
            print(f"    Flags: {r['flags']}")
        print(f"{'-'*60}")

    if not remove_mode:
        print(f"\nScan complete. Review {FLAGGED_FILE} then run --remove to delete LIKELY NOT ADVISOR records.")
        return

    # Remove mode
    to_remove = [r for r in results if r["classification"] != "LIKELY ADVISOR"] if remove_all else not_advisor
    label = "LIKELY NOT ADVISOR + REVIEW NEEDED" if remove_all else "LIKELY NOT ADVISOR"

    if not to_remove:
        print("\nNo records to remove.")
        return

    print(f"\nRemoving {len(to_remove)} {label} records from Airtable...")
    ids_to_delete = [r["id"] for r in to_remove]

    for i in range(0, len(ids_to_delete), CHUNK_SIZE):
        batch = ids_to_delete[i:i + CHUNK_SIZE]
        table.batch_delete(batch)
        print(f"  Deleted {min(i + CHUNK_SIZE, len(ids_to_delete))}/{len(ids_to_delete)}...")

    print(f"\nDone! {len(ids_to_delete)} non-advisor records removed.")
    print(f"Review {FLAGGED_FILE} for REVIEW NEEDED records that may need manual checking.")


if __name__ == "__main__":
    main()
