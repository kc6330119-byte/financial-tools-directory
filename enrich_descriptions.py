#!/usr/bin/env python3
"""
Deterministic description enrichment for investment advisors.

Uses MD5 hash of the advisor slug with bit-shifting to select from varied
sentence pools, producing natural-sounding, diverse descriptions that
rebuild identically every time. No API calls — $0 cost.

Adapted from senior-home-care-directory/enrich_descriptions.py pattern.

Usage:
    python3 enrich_descriptions.py              # Dry run — preview changes
    python3 enrich_descriptions.py --apply      # Replace thin/irrelevant descriptions
    python3 enrich_descriptions.py --append     # Append to short descriptions (100-149 chars)
"""
import os
import sys
import hashlib
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_ADVISORS_TABLE_NAME", "Advisors")

MIN_DESC_LENGTH = 100  # Descriptions under this are "thin"
APPEND_THRESHOLD = 150  # Descriptions 100-149 are "short" — append mode
CHUNK_SIZE = 10

# ==============================
# IRRELEVANT DESCRIPTION DETECTION
# ==============================

IRRELEVANT_PHRASES = [
    "official website",
    "visit our website",
    "click here",
    "sign up for",
    "we are a staffing",
    "nursing home",
    "home care",
    "senior care",
    "caregiver",
    "auto insurance",
    "car insurance",
    "home insurance only",
    "tax preparation service",
    "bookkeeping service",
]


def is_irrelevant(desc):
    """Check if a description contains generic boilerplate or non-advisor content."""
    lower = desc.lower()
    return any(phrase in lower for phrase in IRRELEVANT_PHRASES)


# ==============================
# SENTENCE POOLS
# ==============================

# 6 opening variations — selected by h % 6
OPENINGS = [
    "{name} is a trusted investment advisory firm serving clients in {city}, {state}.",
    "Based in {city}, {name} provides personalized financial planning and investment management services.",
    "{name} helps individuals and families in {city}, {state} build and protect their wealth through comprehensive financial planning.",
    "Serving the {city} community, {name} offers professional investment advisory services tailored to each client's goals.",
    "{name} is a financial advisory firm in {city}, {state} dedicated to helping clients achieve their financial objectives.",
    "Clients in {city} and throughout {state} rely on {name} for expert financial guidance and investment management.",
]

# Fallback openings when city or state is missing
OPENINGS_NO_LOCATION = [
    "{name} is a trusted investment advisory firm serving clients nationwide.",
    "{name} provides personalized financial planning and investment management services.",
    "{name} helps individuals and families build and protect their wealth through comprehensive financial planning.",
    "{name} offers professional investment advisory services tailored to each client's goals.",
    "{name} is a financial advisory firm dedicated to helping clients achieve their financial objectives.",
    "Clients rely on {name} for expert financial guidance and investment management.",
]

# 4 service intro variations — selected by (h >> 4) % 4
SERVICE_INTROS = [
    "Their advisory team specializes in",
    "The firm provides expertise in",
    "Clients benefit from",
    "Areas of focus include",
]

# Append-specific service intros (different phrasing to read naturally after existing text)
APPEND_SERVICE_INTROS = [
    "Additional areas of expertise include",
    "The firm also specializes in",
    "Clients can also access",
    "Other advisory services include",
]

SPECIALTY_DESCRIPTIONS = {
    "Retirement Planning": "comprehensive retirement planning and income distribution strategies",
    "Investment Management": "professional portfolio management and asset allocation",
    "Tax Strategy": "tax-efficient investing and strategic tax planning",
    "Estate Planning": "estate planning and wealth transfer strategies",
    "College Savings": "college savings planning and 529 plan management",
    "Insurance Planning": "insurance analysis and risk management",
    "Small Business": "small business financial planning and retirement plans",
    "Wealth Management": "holistic wealth management for high-net-worth clients",
    "Debt Management": "debt management and financial recovery planning",
    "Social Security Planning": "Social Security optimization and claiming strategies",
}

SERVICE_DESCRIPTIONS = {
    "Financial Planning": "comprehensive financial planning",
    "Investment Management": "investment portfolio management",
    "Tax Planning": "tax planning and preparation",
    "Estate Planning": "estate and legacy planning",
    "Retirement Planning": "retirement planning",
    "Insurance Analysis": "insurance and risk analysis",
    "Social Security Optimization": "Social Security claiming optimization",
}

# 3 fee variations — selected by (h >> 8) % 3
FEE_SENTENCES = [
    "The firm operates on a {options} basis.",
    "{name} charges on a {options} fee structure.",
    "Compensation is structured as {options}.",
]

# 3 language variations — selected by (h >> 12) % 3
LANGUAGE_SENTENCES = [
    "Advisors are available who speak {langs}.",
    "Staff members speak {langs}.",
    "The team includes advisors fluent in {langs}.",
]

# 3 rating variations — selected by (h >> 16) % 3 (only used when rating >= 4.0)
RATING_SENTENCES = [
    "The firm holds a {rating}-star rating based on {count} reviews.",
    "With a {rating}-star Google rating from {count} reviews, {name} is well-regarded by clients in the area.",
    "Clients have given {name} a {rating}-star rating across {count} reviews.",
]

# 4 closing variations — selected by (h >> 20) % 4
CLOSINGS = [
    "Contact {name} to schedule a consultation and discuss your financial goals.",
    "Reach out to {name} to learn how their advisors can help you build a stronger financial future.",
    "Call {name} today to explore personalized financial planning options.",
    "Get in touch with {name} to start working toward your investment and retirement goals.",
]

# 3 hours variations — selected by (h >> 24) % 3
HOURS_SENTENCES = [
    "{name} is available {hours}.",
    "Hours of operation: {hours}.",
    "The firm operates {hours}.",
]

# 3 credential variations — selected by (h >> 28) % 3
CREDENTIAL_SENTENCES = [
    "The team holds {creds} credentials.",
    "Advisors at the firm are credentialed with {creds} designations.",
    "{name}'s professionals hold {creds} certifications.",
]


def format_list(items):
    """Format a list as 'a, b, and c'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def extract_fields(record):
    """Extract and normalize fields from an Airtable record."""
    fields = record.get("fields", {})

    def to_list(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str) and val.strip():
            return [s.strip() for s in val.split(",") if s.strip()]
        return []

    return {
        "slug": fields.get("Slug", ""),
        "name": fields.get("Name", "Advisor"),
        "city": fields.get("City", ""),
        "state": fields.get("State", ""),
        "rating": fields.get("Rating"),
        "review_count": fields.get("Review Count"),
        "specialties": to_list(fields.get("Specialties", [])),
        "services": to_list(fields.get("Services", [])),
        "fee_structure": to_list(fields.get("Fee Structure", [])),
        "credentials": to_list(fields.get("Credentials", [])),
        "languages": to_list(fields.get("Languages", [])),
        "hours": fields.get("Hours", ""),
    }


def generate_description(record):
    """Generate a deterministic, varied full description for an advisor."""
    f = extract_fields(record)
    slug = f["slug"]

    # Single hash, bit-shifted for each pool selection
    h = int(hashlib.md5(slug.encode()).hexdigest(), 16)

    parts = []

    # Opening (h % 6)
    if f["city"] and f["state"]:
        opening = OPENINGS[h % 6].format(name=f["name"], city=f["city"], state=f["state"])
    else:
        opening = OPENINGS_NO_LOCATION[h % 6].format(name=f["name"])
    parts.append(opening)

    # Specialties/services ((h >> 4) % 4)
    service_items = []
    for sp in f["specialties"][:4]:
        desc = SPECIALTY_DESCRIPTIONS.get(sp)
        if desc:
            service_items.append(desc)
    for svc in f["services"][:3]:
        desc = SERVICE_DESCRIPTIONS.get(svc)
        if desc and desc not in service_items:
            service_items.append(desc)

    if service_items:
        intro = SERVICE_INTROS[(h >> 4) % len(SERVICE_INTROS)]
        parts.append(f"{intro} {format_list(service_items)}.")

    # Fee structure ((h >> 8) % 3)
    if f["fee_structure"]:
        fee = FEE_SENTENCES[(h >> 8) % len(FEE_SENTENCES)].format(
            options=format_list(f["fee_structure"]), name=f["name"]
        )
        parts.append(fee)

    # Languages ((h >> 12) % 3) — only if multilingual
    non_english = [l for l in f["languages"] if l.lower() != "english"]
    if non_english:
        lang_sentence = LANGUAGE_SENTENCES[(h >> 12) % len(LANGUAGE_SENTENCES)].format(
            langs=format_list(["English"] + non_english)
        )
        parts.append(lang_sentence)

    # Rating ((h >> 16) % 3) — only if rating >= 4.0
    if f["rating"] and f["review_count"] and f["review_count"] > 0:
        try:
            if float(f["rating"]) >= 4.0:
                rating_sentence = RATING_SENTENCES[(h >> 16) % len(RATING_SENTENCES)].format(
                    rating=f["rating"], count=f["review_count"], name=f["name"]
                )
                parts.append(rating_sentence)
        except (ValueError, TypeError):
            pass

    # Hours ((h >> 24) % 3)
    if f["hours"] and len(f["hours"]) < 60:
        hours_sentence = HOURS_SENTENCES[(h >> 24) % len(HOURS_SENTENCES)].format(
            name=f["name"], hours=f["hours"]
        )
        parts.append(hours_sentence)

    # Credentials ((h >> 28) % 3)
    if f["credentials"]:
        cred_sentence = CREDENTIAL_SENTENCES[(h >> 28) % len(CREDENTIAL_SENTENCES)].format(
            creds=format_list(f["credentials"]), name=f["name"]
        )
        parts.append(cred_sentence)

    # Closing ((h >> 20) % 4)
    closing = CLOSINGS[(h >> 20) % len(CLOSINGS)].format(name=f["name"])
    parts.append(closing)

    return " ".join(parts)


def generate_supplement(record):
    """Generate supplementary content to append to short descriptions.
    Uses different phrasing than full generation to read naturally after existing text."""
    f = extract_fields(record)
    slug = f["slug"]

    h = int(hashlib.md5(slug.encode()).hexdigest(), 16)

    parts = []

    # Specialties/services — use append-specific intros
    service_items = []
    for sp in f["specialties"][:3]:
        desc = SPECIALTY_DESCRIPTIONS.get(sp)
        if desc:
            service_items.append(desc)
    for svc in f["services"][:2]:
        desc = SERVICE_DESCRIPTIONS.get(svc)
        if desc and desc not in service_items:
            service_items.append(desc)

    if service_items:
        intro = APPEND_SERVICE_INTROS[(h >> 4) % len(APPEND_SERVICE_INTROS)]
        parts.append(f"{intro} {format_list(service_items)}.")

    # Fee structure
    if f["fee_structure"]:
        fee = FEE_SENTENCES[(h >> 8) % len(FEE_SENTENCES)].format(
            options=format_list(f["fee_structure"]), name=f["name"]
        )
        parts.append(fee)

    # Languages
    non_english = [l for l in f["languages"] if l.lower() != "english"]
    if non_english:
        lang_sentence = LANGUAGE_SENTENCES[(h >> 12) % len(LANGUAGE_SENTENCES)].format(
            langs=format_list(["English"] + non_english)
        )
        parts.append(lang_sentence)

    # Rating
    if f["rating"] and f["review_count"] and f["review_count"] > 0:
        try:
            if float(f["rating"]) >= 4.0:
                rating_sentence = RATING_SENTENCES[(h >> 16) % len(RATING_SENTENCES)].format(
                    rating=f["rating"], count=f["review_count"], name=f["name"]
                )
                parts.append(rating_sentence)
        except (ValueError, TypeError):
            pass

    # Credentials
    if f["credentials"]:
        cred_sentence = CREDENTIAL_SENTENCES[(h >> 28) % len(CREDENTIAL_SENTENCES)].format(
            creds=format_list(f["credentials"]), name=f["name"]
        )
        parts.append(cred_sentence)

    # Closing
    closing = CLOSINGS[(h >> 20) % len(CLOSINGS)].format(name=f["name"])
    parts.append(closing)

    return " ".join(parts)


def main():
    from pyairtable import Api

    append_mode = "--append" in sys.argv
    apply_mode = "--apply" in sys.argv or append_mode

    mode_label = "APPEND" if append_mode else ("APPLY" if apply_mode else "DRY RUN")
    print(f"\n{'='*62}")
    print(f"  Description Enrichment for Investment Advisors  [{mode_label}]")
    print(f"{'='*62}\n")

    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, TABLE_NAME)

    print("Fetching records from Airtable...")
    records = table.all()
    print(f"Fetched {len(records)} records.\n")

    if append_mode:
        # Append mode: find records with short descriptions (100-149 chars)
        # that are NOT irrelevant
        targets = []
        for r in records:
            desc = (r["fields"].get("Description") or "").strip()
            if MIN_DESC_LENGTH <= len(desc) < APPEND_THRESHOLD and not is_irrelevant(desc):
                targets.append(r)

        print(f"Short descriptions (100-149 chars, not irrelevant): {len(targets)}")

        if not targets:
            print("Nothing to append.")
            return

        updates = []
        for r in targets:
            existing = r["fields"]["Description"].strip()
            supplement = generate_supplement(r)
            new_desc = f"{existing} {supplement}"
            updates.append({
                "id": r["id"],
                "fields": {"Description": new_desc},
                "_label": "APPEND",
                "_name": r["fields"].get("Name", ""),
            })

    else:
        # Replace mode: find thin OR irrelevant descriptions
        enriched_thin = 0
        replaced_irrelevant = 0
        updates = []

        for r in records:
            desc = (r["fields"].get("Description") or "").strip()
            desc_clean = desc.replace("nan", "").strip()

            label = None
            if len(desc_clean) < MIN_DESC_LENGTH:
                label = "ENRICH (thin)"
                enriched_thin += 1
            elif is_irrelevant(desc):
                label = "REPLACE (irrelevant)"
                replaced_irrelevant += 1

            if label:
                new_desc = generate_description(r)
                updates.append({
                    "id": r["id"],
                    "fields": {"Description": new_desc},
                    "_label": label,
                    "_name": r["fields"].get("Name", ""),
                })

        print(f"Thin descriptions (< {MIN_DESC_LENGTH} chars): {enriched_thin}")
        print(f"Irrelevant descriptions (boilerplate):  {replaced_irrelevant}")

        if not updates:
            print("\nNothing to enrich.")
            return

    # Preview
    print(f"\nTotal updates: {len(updates)}")
    print(f"\n{'─'*60}")
    print("Preview (first 3):")
    print(f"{'─'*60}")
    for u in updates[:3]:
        print(f"\n  [{u['_label']}] {u['_name']}")
        desc = u["fields"]["Description"]
        if len(desc) > 200:
            print(f"  {desc[:200]}...")
        else:
            print(f"  {desc}")
    print(f"{'─'*60}")

    if not apply_mode:
        print("\nDry run complete. Use --apply to update Airtable, or --append for short descriptions.")
        return

    # Clean internal fields before sending to Airtable
    airtable_updates = [{"id": u["id"], "fields": u["fields"]} for u in updates]

    print(f"\nApplying {len(airtable_updates)} updates to Airtable...")
    for i in range(0, len(airtable_updates), CHUNK_SIZE):
        batch = airtable_updates[i:i + CHUNK_SIZE]
        table.batch_update(batch)
        print(f"  Updated {min(i + CHUNK_SIZE, len(airtable_updates))}/{len(airtable_updates)}...")

    print(f"\nDone! {len(airtable_updates)} descriptions {'appended' if append_mode else 'enriched'}.")


if __name__ == "__main__":
    main()
