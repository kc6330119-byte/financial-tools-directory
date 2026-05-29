"""
generate_fact_descriptions.py — fact-grounded listing descriptions for advisors.

Replaces the hash-seeded spintax approach (enrich_descriptions.py) and the
AI-prose approach (auto_descriptions.py). Each description is assembled ONLY
from facts that are true for that specific firm, joined from:
  - Airtable structured fields (Firm Type, Services, Specialties, Credentials,
    Fee Structure, Fiduciary, SEC Registered, Minimum Investment, Year
    Established, Languages, Hours, Rating, Review Count)
  - Outscraper `about` attribute JSON (service options, accessibility, planning),
    joined by normalized name+city+state.

Variation between listings comes from real differing facts, not shuffled
synonyms — removing the "scaled content abuse" spam signal. There is NO length
padding: descriptions that come out under config.MIN_DESCRIPTION_LENGTH (250)
are left short on purpose; build.py's per-listing gate noindexes them, shrinking
the indexed surface to genuinely fact-rich listings.

YMYL discipline: clauses state only what a firm IS or DOES (fiduciary status,
registration, services, fees). They never promise returns, outcomes, tax savings,
or "peace of mind" — financial content is held to a higher bar by Google.

Safety: dry-run by default; --apply is required to write. Before the first write
the existing descriptions are backed up to a timestamped JSON keyed by record id.
This ONLY updates existing records; it never inserts.

Usage:
  python3 generate_fact_descriptions.py          # dry run: stats + samples + review file
  python3 generate_fact_descriptions.py --apply   # write the "Description" field in Airtable
"""
import os
import re
import sys
import json
import glob
from datetime import datetime
from pathlib import Path

import openpyxl
from dotenv import load_dotenv
from pyairtable import Api

import config

REPO = Path(__file__).resolve().parent
# override=True so .env wins over a stale/empty shell export (a common silent bug:
# an empty exported AIRTABLE_API_KEY shadows the real key otherwise).
load_dotenv(REPO / ".env", override=True)

DESC_FIELD = "Description"          # correctly spelled in this base (cf. DGL's "Decription")
TABLE_NAME = os.environ.get("AIRTABLE_ADVISORS_TABLE_NAME", "Advisors")
BACKUP_DIR = REPO / "data"
MIN_LEN = config.MIN_DESCRIPTION_LENGTH
APPLY = "--apply" in sys.argv

# Firm Type -> noun phrase for the opening sentence. Falls back gracefully.
FIRM_TYPE_PHRASE = {
    "Registered Investment Advisor": "registered investment advisor (RIA)",
    "RIA": "registered investment advisor (RIA)",
    "Wealth Management": "wealth management firm",
    "Financial Planning": "financial planning firm",
    "Investment Management": "investment management firm",
    "Broker-Dealer": "broker-dealer",
    "Independent": "independent advisory firm",
    "Insurance": "insurance and advisory firm",
}

JUNK_MIN = ("", "0", "none", "n/a", "na", "nan", "tbd", "unknown")


def _require(key):
    """Fetch an env var, failing loudly if missing OR empty (not just missing)."""
    val = os.environ.get(key)
    if not val or not val.strip():
        sys.exit(f"{key} is missing or empty — check {REPO/'.env'} and unset any empty shell export.")
    return val.strip()


def norm(s):
    if s is None:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", str(s).strip().lower()))


def join_key(n, c, s):
    return f"{norm(n)}|{norm(c)}|{norm(s)}"


def oxford(items):
    items = [str(i).strip() for i in items if i and str(i).strip()]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def firm_phrase(typ):
    t = (typ or "").strip()
    if not t:
        return "investment advisory firm"
    if t in FIRM_TYPE_PHRASE:
        return FIRM_TYPE_PHRASE[t]
    tl = t.lower()
    if any(w in tl for w in ("firm", "advisor", "management", "planning", "services", "advisory")):
        return tl
    return f"{tl} firm"


def a_an(word):
    """'a' / 'an' by first letter. Sufficient for the firm-type and fee
    vocabulary here — none of it has silent-h ('hour') or 'yu-' ('unit') cases."""
    return "an" if (word or "")[:1].lower() in "aeiou" else "a"


# ---------- load + dedupe Outscraper about ----------
def load_about():
    """Join Outscraper `about` JSON by normalized name+city+state. Prefers the
    richest (longest) `about` blob when a key appears in more than one export."""
    by_key = {}
    for path in sorted(glob.glob(str(REPO / "outscraper_advisors*.xlsx"))):
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        ci = {h: i for i, h in enumerate(norm(x) for x in next(rows))}
        if "name" not in ci or "about" not in ci:
            wb.close()
            continue
        for row in rows:
            def cell(col):
                return row[ci[col]] if col in ci and ci[col] < len(row) else None
            name, about = cell("name"), cell("about")
            if not name or not about or not str(about).strip():
                continue
            k = join_key(name, cell("city"), cell("state"))
            if k not in by_key or len(str(about)) > len(str(by_key[k])):
                by_key[k] = about
        wb.close()
    return by_key


def parse_about(raw):
    """Flatten about JSON {category: {attr: bool}} into true-attribute sets per category."""
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    out = {}
    for cat, attrs in data.items():
        trues = set()
        if isinstance(attrs, dict):
            trues = {a for a, v in attrs.items() if v is True}
        elif isinstance(attrs, list):
            trues = {str(x) for x in attrs}
        if trues:
            out.setdefault(norm(cat), set()).update(trues)
    return out


# ---------- hours summary ----------
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
NUMWORD = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}


def hours_clause(hours):
    if not hours:
        return ""
    h = str(hours)
    if h.lower().startswith("daily"):
        return "The office is open daily"
    open_days = [d for d in DAYS if re.search(rf"{d}:\s*(?!Closed)\S", h)]
    if not open_days:
        return ""
    n = len(open_days)
    if n == 7:
        base = "The office is open seven days a week"
    else:
        unit = "day" if n == 1 else "days"
        base = f"The office is open {NUMWORD.get(n, n)} {unit} a week"
    if "Saturday" in open_days and "Sunday" in open_days:
        base += ", including weekends"
    elif "Saturday" in open_days:
        base += ", including Saturdays"
    return base


# ---------- compose ----------
def _to_list(val):
    if isinstance(val, list):
        return [str(v).strip() for v in val if v and str(v).strip()]
    if isinstance(val, str) and val.strip():
        return [s.strip() for s in val.split(",") if s.strip()]
    return []


def compose(f, about):
    name = (f.get("Name") or "").strip()
    city = (f.get("City") or "").strip()
    state = (f.get("State") or "").strip()
    loc = f"{city}, {state}".strip(", ")
    sentences = []

    # 1. opening (always)
    phrase = firm_phrase(f.get("Firm Type"))
    sentences.append(f"{name} is {a_an(phrase)} {phrase}" + (f" in {loc}." if loc else "."))

    # 2. year established
    year = str(f.get("Year Established") or "").strip()
    if re.fullmatch(r"(19|20)\d{2}", year):
        sentences.append(f"The firm was established in {year}.")

    # 3. fiduciary / registration (only-true booleans)
    reg = []
    if f.get("Fiduciary") is True:
        reg.append("acts as a fiduciary")
    if f.get("SEC Registered") is True:
        reg.append("is registered with the SEC")
    if reg:
        sentences.append(f"It {oxford(reg)}.")

    # 4. services
    services = _to_list(f.get("Services"))
    if services:
        sentences.append(f"Services include {oxford(services)}.")

    # 5. specialties (drop any already named among services)
    svc_lower = {s.lower() for s in services}
    specialties = [s for s in _to_list(f.get("Specialties")) if s.lower() not in svc_lower]
    if specialties:
        sentences.append(f"The firm specializes in {oxford(specialties)}.")

    # 6. credentials
    creds = _to_list(f.get("Credentials"))
    if creds:
        sentences.append(f"Its advisors hold {oxford(creds)} credentials.")

    # 7. fee structure
    fees = [s.lower() for s in _to_list(f.get("Fee Structure"))]
    if fees:
        sentences.append(f"Compensation is on {a_an(fees[0])} {oxford(fees)} basis.")

    # 8. minimum investment (only when it carries an actual figure)
    mi = str(f.get("Minimum Investment") or "").strip()
    if mi and mi.lower() not in JUNK_MIN and any(ch.isdigit() for ch in mi):
        sentences.append(f"The firm reports a minimum investment of {mi}.")

    # 9. languages (only when more than English is offered)
    non_english = [l for l in _to_list(f.get("Languages")) if l.lower() != "english"]
    if non_english:
        sentences.append(f"Advisory services are available in {oxford(['English'] + non_english)}.")

    # 10. about-derived service options
    opt_phrases = []
    for a in about.get("service options", set()):
        al = a.lower()
        if "online appointment" in al:
            opt_phrases.append("online appointment booking")
        elif "onsite" in al:
            opt_phrases.append("onsite meetings")
        elif "virtual" in al or "video" in al:
            opt_phrases.append("virtual consultations")
    opt_phrases = list(dict.fromkeys(opt_phrases))
    if opt_phrases:
        sentences.append(f"Service options include {oxford(opt_phrases)}.")

    # 11. planning
    plan = about.get("planning", set())
    if any("required" in p.lower() for p in plan):
        sentences.append("Appointments are required.")
    elif any("recommend" in p.lower() for p in plan):
        sentences.append("Appointments are recommended.")

    # 12. accessibility
    if any("wheelchair accessible entrance" in a.lower() for a in about.get("accessibility", set())):
        sentences.append("The office has a wheelchair-accessible entrance.")

    # 13. hours
    hc = hours_clause(f.get("Hours"))
    if hc:
        sentences.append(hc + ".")

    # 14. social proof (last) — prose mention only; NOT structured aggregateRating markup
    rating = f.get("Rating")
    reviews = f.get("Review Count")
    if rating and reviews:
        try:
            rn = int(reviews)
            if rn > 0:
                sentences.append(
                    f"It holds a {rating}-star rating from {rn:,} Google review"
                    + ("s" if rn != 1 else "") + "."
                )
        except (ValueError, TypeError):
            pass

    return " ".join(sentences)


# ---------- run ----------
FIELDS = ["Name", "City", "State", "Firm Type", "Services", "Specialties", "Credentials",
          "Fee Structure", "Fiduciary", "SEC Registered", "Minimum Investment",
          "Year Established", "Languages", "Hours", "Rating", "Review Count", DESC_FIELD]


def main():
    about_by_key = load_about()
    print(f"Loaded Outscraper 'about' for {len(about_by_key)} businesses.")

    api = Api(_require("AIRTABLE_API_KEY"))
    table = api.table(_require("AIRTABLE_BASE_ID"), TABLE_NAME)
    recs = table.all(fields=FIELDS)
    print(f"Fetched {len(recs)} advisor records from '{TABLE_NAME}'.")

    results = []   # (rec_id, name, new_text, old_desc, length)
    matched = 0
    for r in recs:
        f = r["fields"]
        k = join_key(f.get("Name"), f.get("City"), f.get("State"))
        about = parse_about(about_by_key.get(k)) if k in about_by_key else {}
        if about:
            matched += 1
        text = compose(f, about)
        results.append((r["id"], f.get("Name", ""), text, f.get(DESC_FIELD, ""), len(text)))

    n = len(results)
    if not n:
        sys.exit("No records returned — nothing to do.")

    lengths = sorted(x[4] for x in results)
    def pct(p):
        return lengths[min(n - 1, int(p * n))]
    idx = sum(1 for L in lengths if L >= MIN_LEN)
    print(f"\nComposed {n} descriptions  ('about' matched on {matched}, {100*matched/n:.1f}%).")
    print(f"  length: min={lengths[0]} p25={pct(.25)} median={pct(.5)} p75={pct(.75)} p90={pct(.9)} max={lengths[-1]}")
    print(f"  >= {MIN_LEN} chars (will INDEX): {idx} ({100*idx/n:.1f}%)   "
          f"< {MIN_LEN} (will noindex): {n-idx} ({100*(n-idx)/n:.1f}%)")

    # samples across the information-density spectrum -> review file
    by_len = sorted(results, key=lambda x: x[4])
    picks = [by_len[int(p * (n - 1))] for p in (0.10, 0.35, 0.55, 0.75, 0.90, 0.98)]
    review_lines = ["# Fact-grounded advisor description samples\n"]
    print("\n===== SAMPLES (low -> high information density) =====")
    for _id, name, text, _old, L in picks:
        print(f"\n[{L} chars] {name}\n{text}")
        review_lines.append(f"## {name}  _({L} chars, {'INDEX' if L >= MIN_LEN else 'noindex'})_\n\n{text}\n")
    (REPO / "FACT_DESCRIPTIONS_SAMPLE.md").write_text("\n".join(review_lines))
    print("\nWrote review file: FACT_DESCRIPTIONS_SAMPLE.md")

    if not APPLY:
        print("\nDRY RUN — nothing written. Re-run with --apply to write the Description field.")
        return

    # backup existing descriptions before the first write
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"description_backup_{stamp}.json"
    backup = {rid: old for rid, _n, _t, old, _L in results}
    backup_path.write_text(json.dumps(backup, ensure_ascii=False, indent=2))
    print(f"\nBacked up {len(backup)} existing descriptions -> {backup_path}")

    print("--apply: updating Airtable (existing records only; never inserts) ...")
    updates = [{"id": rid, "fields": {DESC_FIELD: text}} for rid, _n, text, _old, _L in results]
    for i in range(0, len(updates), 10):
        table.batch_update(updates[i:i + 10])
        print(f"  updated {min(i + 10, len(updates))}/{len(updates)}")
    print("Done.")


if __name__ == "__main__":
    main()
