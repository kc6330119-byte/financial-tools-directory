"""
extract_protected_urls.py — grandfather traffic-earning pages past the indexing gate.

build.py's per-listing gate (advisor_is_indexable) noindexes any advisor whose
fact-grounded description falls under config.MIN_DESCRIPTION_LENGTH. That is
intentional: it shrinks the synthetic indexed surface. But a page that ALREADY
earns Google Search traffic must never get noindexed on the next build, or we'd
throw away real rankings. This script reads a Search Console "Pages" performance
export and writes the URLs that earn traffic to protected_urls.txt, which
_load_protected_slugs() reads to force those listings to stay indexed.

Fail-open everywhere: if no export is found it prints guidance and leaves any
existing protected_urls.txt untouched (missing file = no protections = the gate
applies to everything).

Re-run after every data/GSC refresh (see CLAUDE.md):
  python3 extract_protected_urls.py [path/to/Pages.csv] [--min-clicks N] [--min-impressions N]

Defaults: auto-detect the export; protect any page with >= 1 click.
"""
import csv
import re
import sys
import glob
import argparse
from datetime import date
from pathlib import Path

import config

REPO = Path(__file__).resolve().parent
OUT = REPO / "protected_urls.txt"

# Exact (case-insensitive) header names. Exact-match — not substring — so an
# Airtable "Website URL" column never gets mistaken for a GSC "URL" column.
URL_COLS = ("top pages", "page", "landing page", "url", "final url", "address")
CLICK_COLS = ("clicks", "url clicks")
IMPR_COLS = ("impressions", "impr.", "impr")


def _num(v):
    """Parse a metric cell ('1,234', '12%', '', None) into an int. Junk -> 0."""
    if v is None:
        return 0
    s = str(v).strip().replace(",", "").replace("%", "")
    if not s:
        return 0
    try:
        return int(float(s))
    except ValueError:
        return 0


def _find_col(fieldnames, candidates):
    """First header (case-insensitive, trimmed) that exactly matches a candidate."""
    lookup = {(h or "").strip().lower(): h for h in fieldnames}
    for c in candidates:
        if c in lookup:
            return lookup[c]
    return None


def _perf_columns(path):
    """If `path` looks like a performance export, return (url_col, click_col,
    impr_col); else None. A performance export = a URL column AND at least one of
    clicks/impressions. That signature is what separates a GSC export from the
    Airtable/validation CSVs that also live in this repo."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            header = next(csv.reader(fh), [])
    except (OSError, UnicodeDecodeError):
        return None
    url_col = _find_col(header, URL_COLS)
    click_col = _find_col(header, CLICK_COLS)
    impr_col = _find_col(header, IMPR_COLS)
    if url_col and (click_col or impr_col):
        return url_col, click_col, impr_col
    return None


def autodetect():
    """Scan repo CSVs for ones that look like a performance export."""
    hits = []
    for p in sorted(glob.glob(str(REPO / "*.csv"))):
        cols = _perf_columns(p)
        if cols:
            hits.append((p, cols))
    return hits


def main():
    ap = argparse.ArgumentParser(description="Build protected_urls.txt from a Search Console Pages export.")
    ap.add_argument("export", nargs="?", help="Path to the GSC 'Pages' CSV export (auto-detected if omitted).")
    ap.add_argument("--min-clicks", type=int, default=1,
                    help="Protect pages with at least this many clicks (default 1).")
    ap.add_argument("--min-impressions", type=int, default=0,
                    help="Also protect pages with at least this many impressions (default 0 = clicks only).")
    ap.add_argument("--site-url", default=config.SITE_URL,
                    help="Keep only URLs on this site (default config.SITE_URL).")
    args = ap.parse_args()

    # locate the export
    if args.export:
        if not Path(args.export).exists():
            sys.exit(f"Export not found: {args.export}")
        cols = _perf_columns(args.export)
        if not cols:
            sys.exit(f"{args.export} doesn't look like a performance export "
                     "(need a URL column + a clicks/impressions column).")
        path, columns = args.export, cols
    else:
        hits = autodetect()
        if not hits:
            print("No Google Search Console export found in the repo (looked for a CSV with a")
            print("URL column + clicks/impressions). Fail-open: leaving protected_urls.txt as-is.")
            print("\nTo generate it: export Performance > Pages from Search Console, then run:")
            print("  python3 extract_protected_urls.py path/to/Pages.csv")
            return
        if len(hits) > 1:
            print("Multiple performance-export candidates:")
            for p, _ in hits:
                print(f"  - {Path(p).name}")
            print(f"Using the first ({Path(hits[0][0]).name}). Pass an explicit path to override.\n")
        path, columns = hits[0]

    url_col, click_col, impr_col = columns
    host = re.sub(r"^https?://", "", args.site_url.rstrip("/")).lower()

    protected = set()
    total = off_site = 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            url = (row.get(url_col) or "").strip()
            if not url:
                continue
            total += 1
            clicks = _num(row.get(click_col)) if click_col else 0
            imprs = _num(row.get(impr_col)) if impr_col else 0
            if not (clicks >= args.min_clicks or (args.min_impressions > 0 and imprs >= args.min_impressions)):
                continue
            if url.lower().startswith("http") and host not in url.lower():
                off_site += 1
                continue
            protected.add(url)

    rule = f"clicks >= {args.min_clicks}"
    if args.min_impressions > 0:
        rule += f" or impressions >= {args.min_impressions}"

    if not protected:
        print(f"Parsed {total} rows from {Path(path).name}; 0 pages meet '{rule}'.")
        print("Expected for a site with little/no Search traffic — the gate will apply to every")
        print("listing. Not overwriting protected_urls.txt with an empty file.")
        return

    header = [
        "# Protected URLs — pages already earning Google Search traffic. build.py's",
        "# _load_protected_slugs() reads these so the indexing gate never noindexes a page",
        "# that already ranks. Regenerate after every data/GSC refresh (see CLAUDE.md):",
        "#   python3 extract_protected_urls.py [export.csv]",
        f"# Source: {Path(path).name} | Generated: {date.today().isoformat()} | Rule: {rule} | Count: {len(protected)}",
    ]
    OUT.write_text("\n".join(header + sorted(protected)) + "\n")

    advisor_n = sum(1 for u in protected if "/advisor/" in u)
    print(f"Parsed {total} rows from {Path(path).name}.")
    if off_site:
        print(f"  Skipped {off_site} off-site URLs (host != {host}).")
    print(f"Wrote {len(protected)} protected URLs ({advisor_n} advisor pages) -> {OUT.name}  (rule: {rule})")


if __name__ == "__main__":
    main()
