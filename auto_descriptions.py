#!/usr/bin/env python3
"""
auto_descriptions.py — Two-pass description cleanup for Airtable Advisors.

Pass 1 (all records, free):
    Strips JSON blobs, advisor-CRM software lists, regulatory boilerplate,
    embedded 'nan' values, URLs masquerading as descriptions, and normalizes
    whitespace.

Pass 2 (records still lacking a useful description after Pass 1):
    Generates clean, factual descriptions using Claude Haiku 4.5 with prompt
    caching on the system message — cuts per-record cost ~70% after the first
    call. YMYL-aware: prompt explicitly forbids return claims, guarantees, and
    income promises. Estimated ~$0.001–0.002 per record after cache hits;
    ~$0.004 baseline without caching.

Adapted from dog-grooming-directory/auto_descriptions.py with finance-specific
junk patterns and YMYL constraints.

Usage:
    python3 auto_descriptions.py                  # Dry run
    python3 auto_descriptions.py --apply          # Pass 1 cleanup only (free)
    python3 auto_descriptions.py --apply --ai     # Pass 1 + AI generation

Requirements:
    - For --ai: ANTHROPIC_API_KEY in .env
    - pip install anthropic  (>=0.40.0)
"""

import sys
import os
import re
import time
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv()

DRY_RUN = "--apply" not in sys.argv
USE_AI = "--ai" in sys.argv

MIN_DESC_LENGTH = 100   # Descriptions shorter than this (after cleaning) need replacement
CHUNK_SIZE = 10         # Airtable batch size
FLUSH_EVERY = 100       # Write AI results to Airtable in batches to preserve progress

AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_ADVISORS_TABLE_NAME", "Advisors")

# ── Junk-pattern detection ───────────────────────────────────────────────────

# Advisor-CRM and planning software names that scrapers pick up from "tools we
# use" pages and stuff into the description field.
ADVISOR_SOFTWARE_PATTERNS = [
    r"MoneyGuide\s*Pro",
    r"eMoney(\s*Advisor)?",
    r"Riskalyze",
    r"Wealthbox(\s*CRM)?",
    r"Redtail(\s*CRM)?",
    r"Orion\s*Advisor",
    r"Black\s*Diamond",
    r"Salesforce\s*Financial\s*Services",
    r"Tamarac",
    r"Albridge",
    r"Junxure",
    r"Practifi",
    r"Advyzon",
    r"Right\s*Capital",
    r"NaviPlan",
]

SOFTWARE_RE = re.compile("|".join(ADVISOR_SOFTWARE_PATTERNS), re.IGNORECASE)

# Regulatory boilerplate that scrapers grab from disclaimer footers and
# present as descriptions. These are real legal text but say nothing about
# the firm itself.
BOILERPLATE_PATTERNS = [
    r"Securities\s+offered\s+through",
    r"Investment\s+advisory\s+services\s+offered\s+through",
    r"Member\s+FINRA(?:\s*[/&]\s*SIPC)?",
    r"Member\s+SIPC",
    r"Registered\s+(?:Representative|Investment)\s+Advis",
    r"Insurance\s+products\s+offered\s+through",
    r"Not\s+FDIC\s+Insured",
    r"This\s+is\s+not\s+an\s+offer",
    r"Past\s+performance\s+is\s+not\s+indicative",
    r"^\s*Copyright\s*\xa9?\s*\d{4}",
]

BOILERPLATE_RE = re.compile("|".join(BOILERPLATE_PATTERNS), re.IGNORECASE)

# URL or contact info as the entire description (very common in scraped data)
URL_ONLY_RE = re.compile(r"^\s*(https?://\S+|www\.\S+)\s*$")
PHONE_ONLY_RE = re.compile(r"^\s*[\(\d][\d\s\-\(\)\.]+\s*$")
EMAIL_ONLY_RE = re.compile(r"^\s*\S+@\S+\.\S+\s*$")


def is_json_blob(text):
    """Detect JSON-like content (services dicts, hours blobs)."""
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return True
    if stripped.count("{") >= 2 and stripped.count("}") >= 2:
        return True
    if re.search(r'\{["\'][\w\s]+["\']:\s*\{', stripped):
        return True
    return False


def is_software_list(text):
    """Detect strings dominated by advisor-CRM software names."""
    if SOFTWARE_RE.search(text):
        # If the description is mostly a list of tool names, treat it as junk.
        # Heuristic: if it's <200 chars and contains software refs, it's a list.
        if len(text) < 200:
            return True
        # Or if it's a bullet/dot-separated list
        segments = re.split(r"\s*[·•|]\s*", text)
        if len(segments) >= 3 and SOFTWARE_RE.search(text):
            return True
    return False


def is_boilerplate(text):
    """Detect regulatory disclaimer text that says nothing about the firm."""
    return bool(BOILERPLATE_RE.search(text))


def is_contact_only(text):
    """Detect when the entire description is just a URL, phone, or email."""
    stripped = text.strip()
    return bool(URL_ONLY_RE.match(stripped) or PHONE_ONLY_RE.match(stripped) or EMAIL_ONLY_RE.match(stripped))


def clean_description(raw):
    """Strip junk and normalize. Returns cleaned string.

    Strategy: split into sentences (real-world descriptions are usually one
    paragraph with multiple sentences). Drop sentences that are pure junk —
    JSON blobs, software lists, regulatory boilerplate, URLs, phone numbers,
    or 'nan' literals. Keep everything else and rejoin."""
    if not raw:
        return ""
    text = str(raw).strip()

    # Whole-value rejections that don't make sense to sentence-split
    if is_json_blob(text):
        return ""
    if is_software_list(text):
        return ""
    if is_contact_only(text):
        return ""

    # Normalize line breaks into spaces, then split on sentence boundaries.
    # Pattern keeps the terminal punctuation with the preceding sentence.
    text_flat = re.sub(r"\s*\n+\s*", ". ", text)  # turn line breaks into sentence breaks
    sentences = re.split(r"(?<=[.!?])\s+", text_flat)

    kept = []
    for s in sentences:
        s_stripped = s.strip()
        if not s_stripped:
            continue
        if s_stripped.lower().rstrip(".") == "nan":
            continue
        if is_json_blob(s_stripped):
            continue
        if is_software_list(s_stripped):
            continue
        if is_boilerplate(s_stripped):
            continue
        if is_contact_only(s_stripped):
            continue
        kept.append(s_stripped)

    cleaned = " ".join(kept).strip()
    # Collapse multiple spaces and strip stray punctuation at the very end
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip(" .,;:")
    return cleaned


def is_useful(desc):
    """True if the cleaned description is long enough to display."""
    return len(clean_description(desc)) >= MIN_DESC_LENGTH


# ── AI generation ────────────────────────────────────────────────────────────

# System prompt is identical across every record in a run, so we cache it
# (5-min TTL). After the first call writes to cache, subsequent calls read at
# ~10% the cost of normal input tokens. Worth ~70% savings on a 3000-record
# batch.
SYSTEM_PROMPT = """You are writing factual business descriptions for an investment-advisor directory.

STYLE
- Professional and direct. No salesmanship, no superlatives.
- 2 to 4 sentences. ~50–90 words.
- Specific over generic: name actual specialties, fee structures, credentials, locations rather than vague qualities.

PROHIBITED PHRASES (do not use any variant of these — they read as AI slop)
- "trusted partner", "trusted advisor", "trusted choice"
- "dedicated team", "dedicated to providing"
- "tailored solutions", "tailored to your needs", "customized solutions"
- "comprehensive suite", "comprehensive services"
- "holistic approach", "holistic wealth"
- "world-class", "premier", "elite", "leading", "top-tier", "best-in-class"
- "nestled", "boasting", "passionate"
- "your financial goals" / "your financial future" / "achieve your goals"
- "peace of mind"

YMYL CONSTRAINTS (financial content is held to higher standards by Google and regulators)
- Do NOT make claims about investment returns, performance, or growth rates.
- Do NOT use guarantee language ("ensures", "guarantees", "secure", "protect against losses").
- Do NOT promise tax savings or income generation.
- Do NOT recommend specific products, securities, or strategies.
- It is OK to say a firm SPECIALIZES in or PROVIDES a service area; it is NOT OK to promise outcomes from that service.

FACTUAL DISCIPLINE
- Use only the information provided in the data block. Do not invent credentials, services, fee structures, or years in business.
- If data is sparse, write a shorter description. Do not pad.

OUTPUT
- Plain text only. No quotes, no labels, no markdown, no bullet points.
- Start with the firm name or a clear subject. End with a complete sentence."""


def generate_ai_description(advisor):
    """Call Claude Haiku 4.5 to write a factual 2–4 sentence description.
    Uses prompt caching on the system message to amortize cost across the batch."""
    import anthropic

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        timeout=30.0,
    )

    def _list(val):
        if isinstance(val, list):
            return ", ".join(str(v) for v in val if v) or "not specified"
        if isinstance(val, str) and val.strip():
            return val.strip()
        return "not specified"

    rating_line = ""
    rating = advisor.get("rating")
    review_count = advisor.get("review_count")
    if rating and str(rating) not in ("0", ""):
        rating_line = f"Rating: {rating}"
        if review_count and str(review_count) not in ("0", ""):
            rating_line += f" ({review_count} Google reviews)"
        rating_line += "\n"

    fiduciary_line = ""
    if advisor.get("fiduciary"):
        fiduciary_line = "Fiduciary: yes\n"

    year_line = ""
    if advisor.get("year_established"):
        year_line = f"Year established: {advisor['year_established']}\n"

    user_msg = (
        "Write a factual description for this investment-advisor business listing. "
        "Follow the style and YMYL rules in the system prompt strictly.\n\n"
        f"Firm name: {advisor['name']}\n"
        f"Location: {advisor.get('city','')}, {advisor.get('state','')}\n"
        f"Firm type: {advisor.get('firm_type', 'not specified')}\n"
        f"Specialties: {_list(advisor.get('specialties'))}\n"
        f"Services: {_list(advisor.get('services'))}\n"
        f"Fee structure: {_list(advisor.get('fee_structure'))}\n"
        f"Credentials held by team: {_list(advisor.get('credentials'))}\n"
        f"Languages: {_list(advisor.get('languages'))}\n"
        f"{year_line}"
        f"{fiduciary_line}"
        f"{rating_line}"
        "\nWrite only the description text."
    )

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_msg}],
    )

    return msg.content[0].text.strip()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    api = Api(os.getenv("AIRTABLE_API_KEY"))
    table = api.table(os.getenv("AIRTABLE_BASE_ID"), AIRTABLE_TABLE_NAME)

    mode_label = "DRY RUN" if DRY_RUN else ("APPLY + AI" if USE_AI else "APPLY — Pass 1 only")
    print(f"\n{'='*62}")
    print(f"  Auto-Descriptions for Investment Advisors  [{mode_label}]")
    print(f"{'='*62}\n")

    print("Fetching records from Airtable...")
    records = table.all()
    print(f"Fetched {len(records)} records.\n")

    # ── Categorize every record ──────────────────────────────────────────────
    pass1_changes = []   # cleaning changed the value (junk stripped)
    still_needs = []     # even after cleaning, description is too short

    for rec in records:
        fields = rec["fields"]
        name = (fields.get("Name") or "").strip()
        if not name:
            continue

        original = fields.get("Description", "")
        cleaned = clean_description(original)

        if cleaned != str(original).strip():
            pass1_changes.append({
                "id": rec["id"],
                "name": name,
                "original": original,
                "cleaned": cleaned,
            })

        if not is_useful(cleaned):
            still_needs.append({
                "id": rec["id"],
                "name": name,
                "fields": fields,
                "cleaned": cleaned,
            })

    print(f"── Pass 1: junk cleanup ────────────────────────────────────")
    print(f"  Records with junk to strip:           {len(pass1_changes)}")
    print(f"  Still need a description after clean: {len(still_needs)}\n")

    # ── Pass 2 cost estimate ─────────────────────────────────────────────────
    # Without caching: ~$0.004/record. With caching, system-prompt reads cost
    # ~10% of input — most of the cost moves to output tokens. Estimate ~$0.0015
    # per record after cache warmup.
    est_cost_min = len(still_needs) * 0.0015
    est_cost_max = len(still_needs) * 0.004
    print(f"── Pass 2: AI generation ───────────────────────────────────")
    print(f"  Records requiring AI:                 {len(still_needs)}")
    print(f"  Estimated AI cost (with cache):       ~${est_cost_min:.2f} – ${est_cost_max:.2f}\n")

    # ── Dry run output ───────────────────────────────────────────────────────
    if DRY_RUN:
        print("─" * 62)
        print("PASS 1 SAMPLES (before → after):\n")
        for c in pass1_changes[:5]:
            print(f"  {c['name']}")
            print(f"    Before: {repr(str(c['original']).strip()[:90])}")
            print(f"    After:  {repr(c['cleaned'][:90])}")
            print()

        if still_needs:
            print("─" * 62)
            print(f"PASS 2 AI: {len(still_needs)} records would be sent to Claude Haiku\n")
            print("  Sample records:")
            for r in still_needs[:8]:
                city = r["fields"].get("City", "")
                state = r["fields"].get("State", "")
                print(f"    - {r['name']} ({city}, {state})")

        print("\n" + "─" * 62)
        print("DRY RUN complete — nothing written to Airtable.")
        print("  --apply         Apply Pass 1 cleanup (free, safe)")
        print("  --apply --ai    Apply Pass 1 + AI generation")
        print("─" * 62)
        return

    # ── Build update map (Pass 1) ────────────────────────────────────────────
    # IDs that will get AI descriptions — don't pre-write a short cleaned value
    # that the AI is about to overwrite anyway.
    ai_ids = {r["id"] for r in still_needs}

    updates = {}
    for c in pass1_changes:
        if c["id"] not in ai_ids:
            updates[c["id"]] = c["cleaned"]

    if updates:
        print(f"Applying {len(updates)} Pass 1 updates...")
        batch = [{"id": rid, "fields": {"Description": desc}} for rid, desc in updates.items()]
        for i in range(0, len(batch), CHUNK_SIZE):
            table.batch_update(batch[i:i + CHUNK_SIZE])
            print(f"  Updated {min(i + CHUNK_SIZE, len(batch))}/{len(batch)}...")
    else:
        print("Nothing to clean in Pass 1.")

    # ── AI generation ────────────────────────────────────────────────────────
    if not USE_AI:
        if still_needs:
            print(f"\nSkipped AI generation for {len(still_needs)} records.")
            print("Re-run with --apply --ai to generate those descriptions.")
        print(f"\nDone! Updated {len(updates)} records via Pass 1.")
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\nError: ANTHROPIC_API_KEY not found in .env — skipping AI generation.")
        return

    try:
        import anthropic  # noqa: F401
    except ImportError:
        print("\nError: anthropic package not installed.")
        print("Run: pip install anthropic")
        return

    print(f"\nGenerating AI descriptions for {len(still_needs)} records...")
    print("(System prompt is cached — first call writes the cache, subsequent calls read at ~10% cost.)\n")

    ai_batch = []
    total_written = 0
    errors = 0
    cache_creation_tokens = 0
    cache_read_tokens = 0

    for i, rec in enumerate(still_needs):
        try:
            advisor_data = {
                "name": rec["name"],
                "city": rec["fields"].get("City", ""),
                "state": rec["fields"].get("State", ""),
                "firm_type": rec["fields"].get("Firm Type", ""),
                "specialties": rec["fields"].get("Specialties", []),
                "services": rec["fields"].get("Services", []),
                "fee_structure": rec["fields"].get("Fee Structure", []),
                "credentials": rec["fields"].get("Credentials", []),
                "languages": rec["fields"].get("Languages", []),
                "year_established": rec["fields"].get("Year Established", ""),
                "fiduciary": rec["fields"].get("Fiduciary", False),
                "rating": rec["fields"].get("Rating", ""),
                "review_count": rec["fields"].get("Review Count", ""),
            }
            new_desc = generate_ai_description(advisor_data)
            ai_batch.append({"id": rec["id"], "fields": {"Description": new_desc}})
            preview = new_desc[:80].replace("\n", " ")
            print(f"  [{i+1}/{len(still_needs)}] {rec['name'][:42]}: {preview}...")
            time.sleep(0.25)  # gentle rate limiting
        except Exception as e:
            print(f"  [{i+1}/{len(still_needs)}] Error — {rec['name']}: {e}")
            errors += 1

        # Flush incrementally so progress is preserved on interruption
        if len(ai_batch) >= FLUSH_EVERY:
            for j in range(0, len(ai_batch), CHUNK_SIZE):
                table.batch_update(ai_batch[j:j + CHUNK_SIZE])
            total_written += len(ai_batch)
            print(f"  ↳ Flushed {total_written}/{len(still_needs)} to Airtable")
            ai_batch = []

    # Final flush
    if ai_batch:
        print(f"\nWriting final {len(ai_batch)} AI descriptions to Airtable...")
        for i in range(0, len(ai_batch), CHUNK_SIZE):
            table.batch_update(ai_batch[i:i + CHUNK_SIZE])
            print(f"  Updated {min(i + CHUNK_SIZE, len(ai_batch))}/{len(ai_batch)}...")
        total_written += len(ai_batch)

    total = len(updates) + total_written
    print(f"\nDone! Total records updated: {total}")
    if errors:
        print(f"  ({errors} records skipped due to errors — re-run to retry)")
    print("Run python3 build.py to rebuild the site with updated descriptions.")


if __name__ == "__main__":
    main()
