"""
website_descriptions.py — Phase 2 enrichment: ORIGINAL listing descriptions mined
from each advisory firm's OWN website.

Phase 1 (generate_fact_descriptions.py) removed the spun-content spam signal by
rebuilding descriptions from Google Business Profile facts. That clears the
"scaled content abuse" problem but adds little value beyond the GBP. Phase 2 is
what actually adds per-page value: it crawls the firm's own site, has Claude
Haiku extract distinguishing facts and write an ORIGINAL 2-4 sentence
description, and falls back to the Phase 1 description when the site yields
nothing usable. The same per-listing indexing gate then decides index/noindex.

Pipeline (per advisor):
  1. crawl    — homepage + up to 2 same-host about/services pages, main-content
                text via trafilatura. robots-aware (fail-open), polite UA, cached.
  2. compose  — Haiku extracts firm-specific facts and writes original prose
                grounded ONLY in those facts. YMYL-disciplined: no return/outcome
                promises, no verbatim copying, no invented facts. Strict JSON out.
  3. fallback — reuse Phase 1's compose() (GBP facts) when there is no usable site
                text, the model marks the page insufficient, or the result is too
                short.
  4. gate+write — same config.MIN_DESCRIPTION_LENGTH gate; write the "Description"
                field in Airtable. Existing records only — NEVER inserts.

Franchise / shared-host guard: many advisors list the same corporate/aggregator host
(advisor.ml.com, raymondjames.com, northwesternmutual.com, ...). These serve templated
copy — often byte-identical across advisors (two advisor.ml.com deep paths returned
100% identical extracted text in the pilot) — so crawling them manufactures DUPLICATE
content, the opposite of the goal. Any URL on a host shared by >= SHARED_HOST_MIN
advisors is skipped and uses the Phase 1 GBP fallback, whose facts are already
advisor-specific. Even the deep per-advisor paths on these hosts are corporate
boilerplate, so they are routed to the fallback too.

SAFETY: dry-run by default; --apply required to write. Before the first write the
existing descriptions are backed up to data/description_backup_<ts>.json. Crawl and
LLM responses are cached to disk so re-runs are cheap and idempotent.

Usage:
  python3 website_descriptions.py                       # dry run, first 25 advisors
  python3 website_descriptions.py --mix --limit 100     # dry run, representative pilot
  python3 website_descriptions.py --limit 6000 --apply  # full run, write Airtable
  python3 website_descriptions.py --refresh             # ignore cache, re-crawl/re-compose
"""
import os
import re
import sys
import json
import time
import argparse
import hashlib
import socket
from datetime import datetime
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher
from urllib.parse import urlparse, urljoin
from urllib import robotparser
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import trafilatura
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pyairtable import Api

import config
import generate_fact_descriptions as gfd  # reuse Phase 1 composer for the fallback

REPO = Path(__file__).resolve().parent
# override=True so .env wins over a stale/empty shell export (same guard Phase 1 uses).
load_dotenv(REPO / ".env", override=True)

CACHE_DIR = REPO / "data" / "site_cache"
CRAWL_CACHE = CACHE_DIR / "crawl"
LLM_CACHE = CACHE_DIR / "llm"
for d in (CRAWL_CACHE, LLM_CACHE):
    d.mkdir(parents=True, exist_ok=True)

DESC_FIELD = "Description"          # correctly spelled in this base (cf. DGL's "Decription")
TABLE_NAME = os.environ.get("AIRTABLE_ADVISORS_TABLE_NAME", "Advisors")
HAIKU_MODEL = "claude-haiku-4-5-20251001"
UA = "Mozilla/5.0 (compatible; SmartInvestorBot/1.0; +https://smart-investor-financial-tools.com/about.html)"
TIMEOUT = 8
MIN_SITE_TEXT = 250                # below this, treat the site as no usable content
MIN_DESC_LEN = config.MIN_DESCRIPTION_LENGTH   # must match build.py's indexing gate (250)
MAX_VERBATIM_WORDS = 10            # reject a website description copying >= this many consecutive words
CRAWL_DELAY = 0.5                  # politeness pause between requests to the same host
SHARED_HOST_MIN = 8                # a host this many advisors share is "corporate/shared"

# Approximate Claude Haiku 4.5 pricing (USD per million tokens). Used only for the
# pilot cost projection — update to current rates; raw token counts are printed too.
HAIKU_IN_PER_MTOK = 1.00
HAIKU_OUT_PER_MTOK = 5.00

# Bound any socket op that lacks an explicit timeout (notably robotparser.read(), which
# can otherwise hang on a slow host) — matters across the multi-thousand-site full run.
socket.setdefaulttimeout(TIMEOUT)

# Hosts that are never the firm's own site (social, reviews/aggregators, booking,
# generic site builders). Crawling these yields third-party or generic content.
SOCIAL = (
    "facebook.", "instagram.", "m.facebook", "fb.", "linkedin.", "twitter.", "x.com",
    "youtube.", "linktr.ee", "yelp.", "google.com", "sites.google", "business.site",
    "calendly.", "booking.", "smartasset.", "wealthtender.", "nerdwallet.", "bankrate.",
    "bbb.org", "brokercheck.finra.org", "adviserinfo.sec.gov",
)

# Link-text / href hints for a useful secondary page on an advisory site.
ABOUT_HINTS = ("about", "our-story", "who-we-are", "our-team", "team", "services",
               "approach", "philosophy", "process", "planning", "wealth", "advisor")


# ── url helpers ────────────────────────────────────────────────────────────────

def _norm_url(url):
    return url if url.startswith("http") else "https://" + url


def host_of(url):
    if not url:
        return ""
    try:
        return urlparse(_norm_url(url)).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def is_shared_host(url, shared_hosts):
    """True when the URL's host is shared by many advisors — a corporate/franchise/
    aggregator domain (advisor.ml.com, raymondjames.com, northwesternmutual.com, ...).
    These serve templated copy, often byte-identical across advisors, so crawling them
    manufactures DUPLICATE content. Route to the Phase 1 GBP fallback instead, which is
    advisor-specific. Verified in the pilot: two advisor.ml.com deep paths returned 100%
    identical extracted text."""
    return host_of(url) in shared_hosts


# ── crawl stage ───────────────────────────────────────────────────────────────

_robots_cache = {}


def robots_allows(url):
    """Best-effort robots.txt check, cached per host. Fails open on any error."""
    try:
        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in _robots_cache:
            rp = robotparser.RobotFileParser()
            rp.set_url(urljoin(base, "/robots.txt"))
            try:
                rp.read()
            except Exception:
                rp = None
            _robots_cache[base] = rp
        rp = _robots_cache[base]
        return rp.can_fetch(UA, url) if rp else True
    except Exception:
        return True


def _fetch(url):
    url = _norm_url(url)
    if not robots_allows(url):
        return None, "robots-disallow", None
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)
        return r.status_code, r.text, r.url
    except Exception as e:
        return None, type(e).__name__, None


def _extract(html):
    if not html:
        return ""
    txt = trafilatura.extract(html, include_comments=False, include_tables=False,
                              favor_precision=True)
    return (txt or "").strip()


def _find_secondary(html, base_url, host):
    """Return up to 2 same-host about/services URLs to deepen context."""
    found = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            txt = (a.get_text() or "").strip().lower()
            href = a["href"].lower()
            if any(h in txt or h in href for h in ABOUT_HINTS):
                full = urljoin(base_url, a["href"])
                if urlparse(full).netloc.lower().replace("www.", "") == host and full not in found:
                    found.append(full)
            if len(found) >= 2:
                break
    except Exception:
        pass
    return found


def crawl_site(url, use_cache=True):
    """Fetch homepage + secondary pages, return {url, host, text, status}.

    JS-rendered sites (Wix/Squarespace/app builders) return near-empty text here and
    simply fall through to the Phase 1 fallback. A Playwright renderer for those is a
    deliberate, unimplemented hook.
    """
    host = host_of(url)
    cache_path = CRAWL_CACHE / f"{hashlib.md5(url.encode()).hexdigest()}.json"
    if use_cache and cache_path.exists():
        return json.loads(cache_path.read_text())

    result = {"url": url, "host": host, "text": "", "status": None}
    if not host or any(s in host for s in SOCIAL):
        result["status"] = "social/skip"
        cache_path.write_text(json.dumps(result))
        return result

    code, html, final = _fetch(url)
    result["status"] = code
    if isinstance(code, int) and code < 400 and html:
        parts = [_extract(html)]
        for sec in _find_secondary(html, final or url, host):
            time.sleep(CRAWL_DELAY)
            sc, sh, _ = _fetch(sec)
            if isinstance(sc, int) and sc < 400:
                parts.append(_extract(sh))
        result["text"] = "\n".join(p for p in parts if p).strip()
    cache_path.write_text(json.dumps(result))
    return result


# ── compose stage (Haiku) ───────────────────────────────────────────────────

_anthropic_client = None


def _client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key or not key.strip():
            sys.exit("ANTHROPIC_API_KEY is missing or empty — check .env and unset any empty shell export.")
        _anthropic_client = anthropic.Anthropic(api_key=key.strip(), timeout=40.0)
    return _anthropic_client


LLM_SYSTEM = (
    "You write factual directory descriptions for financial advisory firms. You are given raw "
    "text scraped from the firm's OWN website plus structured facts already known about it. "
    "Extract concrete, firm-specific facts: services and specialties, fiduciary status, fee "
    "model (fee-only / fee-based / commission), professional credentials (CFP, CFA, CPA, ChFC, "
    "etc.), SEC/state registration, founding year or years in business, the principals or team, "
    "the clients or niches served, the stated planning approach or process, minimum investment, "
    "and location specifics. Then write an ORIGINAL 2-4 sentence description in your own words, "
    "grounded ONLY in those facts plus the structured data provided.\n"
    "STRICT RULES:\n"
    "- Never copy sentences or distinctive phrases from the source text — paraphrase into your "
    "own words.\n"
    "- Never invent facts. If something is not in the provided text or structured data, omit it.\n"
    "- This is regulated financial (YMYL) content. Describe only what the firm IS or DOES. NEVER "
    "promise or imply investment returns, performance, market-beating results, guaranteed "
    "outcomes, specific tax savings, or 'peace of mind'. Avoid result-implying verbs like "
    "'maximize', 'grow your wealth', 'beat the market'.\n"
    "- No marketing filler: avoid 'nestled', 'boasting', 'dedicated team', 'state-of-the-art', "
    "'comprehensive suite', 'one-stop shop', 'trusted partner', 'tailored solutions'.\n"
    "- Do not call the firm 'top-rated', 'leading', 'premier', or 'award-winning' unless that "
    "exact fact is in the provided data.\n"
    "Set sufficient=true whenever the text contains ANY concrete information specific to THIS "
    "firm (services, credentials, approach, team, clientele, history, location). Only set "
    "sufficient=false when the text is purely navigation links, cookie/legal notices, an error "
    "or parked page, or says nothing specific about this firm. Respond with strict JSON only."
)

LLM_SCHEMA_HINT = (
    'Return ONLY this JSON, nothing else: '
    '{"sufficient": true|false, '
    '"description": "the 2-4 sentence original description (empty string if not sufficient)"}'
)


def llm_compose(name, city, state, gbp_summary, site_text, use_cache=True):
    key = hashlib.md5(f"{name}|{city}|{state}|{site_text[:4000]}".encode()).hexdigest()
    cache_path = LLM_CACHE / f"{key}.json"
    if use_cache and cache_path.exists():
        return json.loads(cache_path.read_text())

    user = (
        f"Firm: {name}\nLocation: {city}, {state}\n"
        f"Structured data (already known, treat as true): {gbp_summary}\n\n"
        f"Website text (raw, may contain navigation/boilerplate):\n\"\"\"\n{site_text[:6000]}\n\"\"\"\n\n"
        f"{LLM_SCHEMA_HINT}"
    )
    try:
        msg = _client().messages.create(
            model=HAIKU_MODEL,
            max_tokens=600,
            system=LLM_SYSTEM,
            messages=[{"role": "user", "content": user}],
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
        data = json.loads(raw)
        data["_usage"] = {"in": msg.usage.input_tokens, "out": msg.usage.output_tokens}
    except Exception as e:
        data = {"sufficient": False, "description": "", "error": str(e), "_usage": {"in": 0, "out": 0}}
    cache_path.write_text(json.dumps(data))
    return data


# ── fallback (Phase 1) + structured summary ─────────────────────────────────

_about_by_key = None


def gbp_fallback(f):
    """Reuse Phase 1's GBP fact-grounded composer for advisors with no usable site."""
    global _about_by_key
    if _about_by_key is None:
        _about_by_key = gfd.load_about()
    k = gfd.join_key(f.get("Name"), f.get("City"), f.get("State"))
    about = gfd.parse_about(_about_by_key.get(k)) if k in _about_by_key else {}
    return gfd.compose(f, about)


def gbp_summary(f):
    """Compact structured-fact string handed to the LLM so it never contradicts known data."""
    bits = []
    if f.get("Firm Type"):
        bits.append(str(f["Firm Type"]))
    if f.get("Fiduciary") is True:
        bits.append("acts as a fiduciary")
    if f.get("SEC Registered") is True:
        bits.append("SEC-registered")
    svc = gfd._to_list(f.get("Services"))
    if svc:
        bits.append("services: " + ", ".join(svc))
    spec = gfd._to_list(f.get("Specialties"))
    if spec:
        bits.append("specialties: " + ", ".join(spec))
    creds = gfd._to_list(f.get("Credentials"))
    if creds:
        bits.append("credentials: " + ", ".join(creds))
    fee = gfd._to_list(f.get("Fee Structure"))
    if fee:
        bits.append("fee structure: " + ", ".join(fee))
    if f.get("Year Established"):
        bits.append("established " + str(f["Year Established"]))
    if f.get("Rating") and f.get("Review Count"):
        bits.append(f"{f['Rating']} stars / {f['Review Count']} Google reviews")
    return "; ".join(bits)


# ── orchestration ─────────────────────────────────────────────────────────────

def _longest_verbatim_words(desc, src):
    """Longest run of consecutive words copied verbatim from src into desc. Short
    factual/branded fragments (a few words) are fine; a long contiguous run means
    the model lifted prose rather than paraphrasing."""
    a = re.findall(r"[a-z0-9]+", desc.lower())
    b = re.findall(r"[a-z0-9]+", src.lower())
    if not a or not b:
        return 0
    return SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b)).size


def process_record(rec, use_cache, shared_hosts):
    f = rec["fields"]
    url = (f.get("Website URL") or "").strip()
    out = {"id": rec["id"], "name": f.get("Name", ""), "source": "gbp",
           "description": "", "site_chars": 0, "old": f.get(DESC_FIELD, "") or "",
           "usage": None}

    if not url:
        out["source"] = "gbp-no-url"
        out["description"] = gbp_fallback(f)
        return out

    if is_shared_host(url, shared_hosts):
        out["source"] = "gbp-shared-host"
        out["description"] = gbp_fallback(f)
        return out

    crawl = crawl_site(url, use_cache=use_cache)
    site_text = crawl.get("text", "")
    out["site_chars"] = len(site_text)

    if len(site_text) >= MIN_SITE_TEXT:
        result = llm_compose(f.get("Name", ""), f.get("City", ""), f.get("State", ""),
                             gbp_summary(f), site_text, use_cache=use_cache)
        out["usage"] = result.get("_usage")
        desc = (result.get("description") or "").strip()
        if result.get("sufficient") and len(desc) >= MIN_DESC_LEN:
            out["verbatim_run"] = _longest_verbatim_words(desc, site_text)
            if out["verbatim_run"] < MAX_VERBATIM_WORDS:
                out["source"] = "website"
                out["description"] = desc
                return out
            out["source"] = "gbp-verbatim"   # copied too much prose -> fall back
        else:
            out["source"] = "gbp-insufficient"
    else:
        out["source"] = "gbp-thin-site"

    out["description"] = gbp_fallback(f)
    return out


def build_pilot_mix(recs, shared_hosts, limit):
    """Representative pilot: ~half from crawlable hosts, ~half from shared-host roots,
    so a dry run exercises BOTH the website-derived path and the fallback path."""
    shared_ids = {r["id"] for r in recs
                  if is_shared_host((r["fields"].get("Website URL") or "").strip(), shared_hosts)}
    crawlable = [r for r in recs if r["id"] not in shared_ids
                 and (r["fields"].get("Website URL") or "").strip()]
    shared = [r for r in recs if r["id"] in shared_ids]
    half = limit // 2
    return crawlable[:limit - half] + shared[:half]


def main():
    ap = argparse.ArgumentParser(description="Phase 2: original website-derived advisor descriptions.")
    ap.add_argument("--limit", type=int, default=25, help="number of advisors to process")
    ap.add_argument("--apply", action="store_true", help="write the Description field to Airtable")
    ap.add_argument("--refresh", action="store_true", help="ignore crawl/LLM cache, re-fetch")
    ap.add_argument("--mix", action="store_true", help="build a representative pilot (standalone + shared-host)")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    use_cache = not args.refresh

    api = Api(gfd._require("AIRTABLE_API_KEY"))
    table = api.table(gfd._require("AIRTABLE_BASE_ID"), TABLE_NAME)
    fetch_fields = list(dict.fromkeys(gfd.FIELDS + ["Website URL"]))
    recs = table.all(fields=fetch_fields)
    print(f"Fetched {len(recs)} advisor records from '{TABLE_NAME}'.")

    # shared/corporate hosts (advisor.ml.com, raymondjames.com, ...) — computed from the data
    host_counts = Counter(host_of((r["fields"].get("Website URL") or "").strip())
                          for r in recs if (r["fields"].get("Website URL") or "").strip())
    shared_hosts = {h for h, c in host_counts.items() if h and c >= SHARED_HOST_MIN}
    top_shared = sorted(((h, c) for h, c in host_counts.items() if h in shared_hosts),
                        key=lambda x: -x[1])[:10]
    print(f"Shared hosts (>= {SHARED_HOST_MIN} advisors): {len(shared_hosts)}.  Top: "
          + ", ".join(f"{h}({c})" for h, c in top_shared))

    batch = build_pilot_mix(recs, shared_hosts, args.limit) if args.mix else recs[:args.limit]
    print(f"\nProcessing {len(batch)} of {len(recs)} advisors "
          f"({'APPLY' if args.apply else 'DRY RUN'}, cache={'on' if use_cache else 'off'}, "
          f"{'mixed pilot' if args.mix else 'first-N'})...\n")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process_record, r, use_cache, shared_hosts): r for r in batch}
        for i, fut in enumerate(as_completed(futs), 1):
            results.append(fut.result())
            if i % 25 == 0:
                print(f"  ...{i}/{len(batch)}")

    # ── report ──
    src = Counter(r["source"] for r in results)
    web = [r for r in results if r["source"] == "website"]
    n = len(results)
    print("\n=== RESULTS ===")
    for label in ("website", "gbp-shared-host", "gbp-thin-site", "gbp-insufficient", "gbp-verbatim", "gbp-no-url", "gbp"):
        if src.get(label):
            print(f"  {label:18s}: {src[label]:4d} ({100*src[label]/n:.0f}%)")

    lengths = sorted(len(r["description"]) for r in results)
    idx = sum(1 for L in lengths if L >= MIN_DESC_LEN)
    print(f"\n  description length: min={lengths[0]} median={lengths[n//2]} max={lengths[-1]}")
    print(f"  >= {MIN_DESC_LEN} chars (will INDEX): {idx} ({100*idx/n:.0f}%)   "
          f"< {MIN_DESC_LEN} (will noindex): {n-idx} ({100*(n-idx)/n:.0f}%)")
    runs = sorted(r.get("verbatim_run", 0) for r in web)
    if runs:
        print(f"  originality — longest verbatim word-run vs source: "
              f"min={runs[0]} median={runs[len(runs)//2]} max={runs[-1]} (gate rejects >= {MAX_VERBATIM_WORDS})")

    # ── cost (Haiku) ──
    llm = [r for r in results if r.get("usage")]
    tin = sum(r["usage"]["in"] for r in llm)
    tout = sum(r["usage"]["out"] for r in llm)
    cost = tin / 1e6 * HAIKU_IN_PER_MTOK + tout / 1e6 * HAIKU_OUT_PER_MTOK
    # full-run upper bound: every URL'd, non-shared-root advisor is an LLM candidate
    candidates = sum(1 for r in recs
                     if (r["fields"].get("Website URL") or "").strip()
                     and not is_shared_host((r["fields"].get("Website URL") or "").strip(), shared_hosts))
    print(f"\n=== COST (Haiku, approx ${HAIKU_IN_PER_MTOK}/{HAIKU_OUT_PER_MTOK} per Mtok in/out) ===")
    print(f"  LLM calls this run: {len(llm)}   tokens in/out: {tin:,}/{tout:,}   cost: ${cost:.4f}")
    if llm:
        per_call = cost / len(llm)
        print(f"  avg per LLM call: ${per_call:.5f}")
        print(f"  full-run candidates (URL'd, non-shared-host): {candidates}")
        print(f"  projected full-run upper bound: ${per_call * candidates:.2f} "
              f"(fewer in practice — thin/JS sites skip the LLM)")

    # ── sample review file ──
    sample_path = REPO / "WEBSITE_DESCRIPTIONS_SAMPLE.md"
    lines = ["# Phase 2 website-derived description samples\n",
             f"_Dry run: {len(batch)} advisors | website-derived {src.get('website',0)} | "
             f"generated {datetime.now():%Y-%m-%d %H:%M}_\n"]
    lines.append("\n## Website-derived (original prose from the firm's own site)\n")
    for r in web[:15]:
        lines.append(f"### {r['name']}  _(site {r['site_chars']} chars, {len(r['description'])} desc)_\n\n{r['description']}\n")
    lines.append("\n## Shared-host fallbacks (Phase 1 GBP facts — should NOT be duplicate corporate copy)\n")
    for r in [x for x in results if x["source"] == "gbp-shared-host"][:5]:
        lines.append(f"### {r['name']}  _(fallback)_\n\n{r['description']}\n")
    sample_path.write_text("\n".join(lines))
    print(f"\nWrote review file: {sample_path.name}")
    print("\n=== SAMPLE WEBSITE-DERIVED ===")
    for r in web[:6]:
        print(f"\n[{r['name']}] (site {r['site_chars']} chars)\n{r['description']}")

    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to write the Description field.")
        return

    # ── apply: back up, then update existing records only ──
    writes = [r for r in results if r["description"]]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = REPO / "data" / f"description_backup_{stamp}.json"
    backup_path.write_text(json.dumps({r["id"]: r["old"] for r in writes}, ensure_ascii=False, indent=2))
    print(f"\nBacked up {len(writes)} existing descriptions -> {backup_path}")

    print(f"--apply: updating Airtable (existing records only; never inserts) ...")
    updates = [{"id": r["id"], "fields": {DESC_FIELD: r["description"]}} for r in writes]
    for i in range(0, len(updates), 10):
        table.batch_update(updates[i:i + 10])
        print(f"  updated {min(i + 10, len(updates))}/{len(updates)}")
    print("Done.")


if __name__ == "__main__":
    main()
