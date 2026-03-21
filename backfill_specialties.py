#!/usr/bin/env python3
"""
Backfill empty Specialties fields in Airtable by scanning
advisor descriptions, names, and other text fields for keyword matches.

Usage:
    python3 backfill_specialties.py              # Dry run — preview changes
    python3 backfill_specialties.py --apply      # Update Airtable
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_ADVISORS_TABLE_NAME", "Advisors")
CHUNK_SIZE = 10

# ==============================
# KEYWORD MAP
# ==============================

SPECIALTY_KEYWORDS = {
    "Retirement Planning": ["retirement", "retire", "401k", "401(k)", "ira", "pension", "social security", "rmd", "required minimum"],
    "Investment Management": ["investment management", "portfolio", "asset management", "asset allocation", "wealth management", "investment advisory"],
    "Tax Strategy": ["tax planning", "tax strategy", "tax-loss", "tax efficient", "roth conversion", "tax optimization", "capital gains"],
    "Estate Planning": ["estate planning", "estate plan", "trust", "inheritance", "wealth transfer", "legacy planning", "probate"],
    "College Savings": ["college", "529 plan", "education funding", "education planning", "college savings"],
    "Insurance Planning": ["insurance planning", "life insurance", "long-term care insurance", "disability insurance", "risk management", "annuity"],
    "Small Business": ["small business", "business owner", "succession planning", "business retirement", "sep ira", "solo 401k", "defined benefit"],
    "Wealth Management": ["wealth management", "high net worth", "family office", "ultra high", "comprehensive wealth"],
    "Debt Management": ["debt management", "student loan", "debt payoff", "debt reduction", "credit counseling"],
    "Social Security Planning": ["social security", "claiming strategy", "social security optimization", "ssa benefit"],
}

# Default assignment for advisors with "financial advisor" or "financial planner"
# in their text but no specific keyword matches
DEFAULT_SPECIALTIES = ["Retirement Planning", "Investment Management"]


def derive_from_text(text, keyword_map):
    """Match keywords against text and return matching categories."""
    text_lower = text.lower()
    matches = set()
    for category, keywords in keyword_map.items():
        if any(kw in text_lower for kw in keywords):
            matches.add(category)
    return sorted(matches)


def get_searchable_text(fields):
    """Combine all text fields for keyword scanning."""
    parts = [
        fields.get("Name", ""),
        fields.get("Description", ""),
        fields.get("Hours", ""),
    ]
    return " ".join(str(p) for p in parts if p)


def main():
    from pyairtable import Api

    apply_mode = "--apply" in sys.argv

    print(f"\n{'='*62}")
    print(f"  Backfill Specialties  [{'APPLY' if apply_mode else 'DRY RUN'}]")
    print(f"{'='*62}\n")

    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, TABLE_NAME)

    print("Fetching records from Airtable...")
    records = table.all()
    print(f"Fetched {len(records)} records.\n")

    # Find records missing specialties
    updates = []
    stats = {"specialties_filled": 0, "defaulted": 0}

    for r in records:
        fields = r["fields"]
        existing_specialties = fields.get("Specialties") or ""

        has_specialties = bool(existing_specialties.strip() if isinstance(existing_specialties, str) else existing_specialties)

        if has_specialties:
            continue

        text = get_searchable_text(fields)

        derived = derive_from_text(text, SPECIALTY_KEYWORDS)
        if not derived and ("financial advisor" in text.lower() or "financial planner" in text.lower()):
            derived = DEFAULT_SPECIALTIES
            stats["defaulted"] += 1
        if derived:
            updates.append({
                "id": r["id"],
                "fields": {"Specialties": derived},
                "_name": fields.get("Name", ""),
            })
            stats["specialties_filled"] += 1

    print(f"Records missing specialties:  {stats['specialties_filled']}")
    print(f"Defaulted (no keyword match): {stats['defaulted']}")
    print(f"Total updates:                {len(updates)}")

    if not updates:
        print("\nNothing to update.")
        return

    # Preview
    print(f"\n{'─'*60}")
    print("Preview (first 5):")
    print(f"{'─'*60}")
    for u in updates[:5]:
        print(f"\n  {u['_name']}")
        for key, val in u["fields"].items():
            print(f"    {key}: {val}")
    print(f"{'─'*60}")

    if not apply_mode:
        print("\nDry run complete. Use --apply to update Airtable.")
        return

    # Clean internal fields and apply
    airtable_updates = [{"id": u["id"], "fields": u["fields"]} for u in updates]

    print(f"\nApplying {len(airtable_updates)} updates to Airtable...")
    for i in range(0, len(airtable_updates), CHUNK_SIZE):
        batch = airtable_updates[i:i + CHUNK_SIZE]
        table.batch_update(batch)
        print(f"  Updated {min(i + CHUNK_SIZE, len(airtable_updates))}/{len(airtable_updates)}...")

    print(f"\nDone! {len(airtable_updates)} records updated.")


if __name__ == "__main__":
    main()
