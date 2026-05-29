# Smart Investor Financial Tools — Redesign Session

## Project context

`smart-investor-financial-tools.com` is one of Kevin Collins's directory sites. It was built first, then shelved due to a challenging niche. It is now being used as a UI playground to experiment with modern frontend design patterns, with the intent of applying successful patterns back to the active sites (holisticvetdirectory.com, splashpadlocator.com, seniorhomecarefinder.com, doggroomerlocator.com).

## Session scope (strict)

- **In scope:** UI redesign — HTML, CSS, minimal progressive JS, template structure
- **In scope:** The homepage, as the first milestone
- **Out of scope (this session):** Airtable schema changes, build pipeline changes, new data sources, any modifications to the other four directory sites
- **Out of scope entirely:** Account creation, deploys to production, AdSense account changes

## Stack

Python static site generation → Airtable (read-only CMS) → Netlify hosting → Google AdSense monetization. See the `smart-investor-redesign` skill for full stack conventions.

## Runbooks (cross-site methodology)

When the user reports a search-engine indexing alert, performance question, or asks "is something wrong with our SEO" — read the SEO diagnostic runbook before starting:

- `~/notes/claude-runbooks/SEO_DIAGNOSTIC_RUNBOOK.md` — playbooks for GSC indexing alerts (noindex / alternate canonical / 404), single-URL 5xx errors, open-ended SEO health checks, Bing-specific diagnosis, meta description audits, and IndexNow integration. Built from the 2026-05-11 tuning session and intended to transfer across all 5 directory sites.

The runbook is centralized at `~/notes/claude-runbooks/` so the same playbook serves all Kevin's directory sites without drift.

## Skills to use on this project

At session start, load skills in this order when relevant:

1. **`smart-investor-redesign`** (personal skill) — stack constraints, AdSense rules, visual direction. Read this first; it defines the guardrails.
2. **`frontend-design`** — typography, spacing, component taste, distinctive aesthetic.
3. **`web-design-guidelines`** (if installed) — modern layout primitives and patterns.

If the `smart-investor-redesign` skill contradicts a general design skill, the personal skill wins — it encodes project-specific constraints.

## Design direction

Finance-native: Bloomberg / Kraken Pro / Robinhood / Koyfin as reference points. Data-dense, confident typography, semantic color (green/red/amber), dark-mode-friendly. Full details in the skill's `references/finance-native-direction.md`.

## First milestone

Redesign the homepage only. Before writing new CSS:
1. Inventory the current codebase
2. Identify all AdSense slots and preserve them
3. Produce a one-page plan describing the proposed homepage structure, typography system, and color palette
4. Wait for Kevin's approval before implementing

## AdSense content remediation — after any data refresh

The site failed AdSense for "Low Value Content" because listing descriptions were spun/templated (`enrich_descriptions.py`, now deprecated). The fix is fact-grounded descriptions + a per-listing indexing gate. **Whenever the advisor data is refreshed** (a new Outscraper export, or new advisors imported via `outscraper_to_airtable.py`), re-run the remediation so the new listings get the same treatment — otherwise fresh records ship with blank/thin descriptions and either get noindexed or, worse, dilute the indexed set:

1. **Refresh protected URLs.** Export Performance → Pages from Google Search Console, then `python3 extract_protected_urls.py path/to/Pages.csv`. This regenerates `protected_urls.txt` (pages already earning traffic, grandfathered past the gate). Fail-open: with no export it leaves the file as-is. Commit `protected_urls.txt` — it is a Netlify build input.
2. **Regenerate descriptions.** `python3 generate_fact_descriptions.py` (dry-run) to review the length distribution, indexed ratio, and `FACT_DESCRIPTIONS_SAMPLE.md`; then `python3 generate_fact_descriptions.py --apply` to write Airtable. `--apply` backs up existing descriptions to `data/description_backup_<ts>.json` first and **only updates existing records, never inserts.**
3. **Build + verify locally.** `python3 build.py`, then confirm indexed advisor pages carry `index, follow` + canonical + a real body description + the AdSense loader, and noindexed ones carry `noindex, follow` + suppressed ads + are absent from `sitemap.xml`.
4. **Deploy.** Hand the git push / Netlify deploy to Kevin — he drives deploys.

Gate threshold lives in `config.MIN_DESCRIPTION_LENGTH` (currently 250). Phase 2 (website-crawl enrichment for per-page value) is the planned follow-on once Phase 1 is live. **Never** re-run `enrich_descriptions.py` (it re-introduces the spam signal; it now hard-stops), **never** add `aggregateRating` markup from scraped ratings, and **never** insert new CMS records from a description script.

## Decision log

All non-obvious design decisions get a one-line entry in `REDESIGN_NOTES.md` in the project root. Create this file on day one and keep it current.

## Commit conventions

- Small, scoped commits
- Commit messages describe the design intent, not just the file change
- Redesign work happens on a branch (`redesign/homepage-finance-native` or similar), never directly on main
- Do not commit generated build output (verify the existing `.gitignore` covers `build/`, `dist/`, or `public/` as appropriate)

## Deploy

Do not deploy during this session unless Kevin explicitly asks. Netlify auto-deploys from main by default; that's why redesign work stays on a branch.

## Things to ask before doing

- Adding any new dependency (npm, Python package, or CDN script)
- Changing any URL, slug, or canonical tag
- Moving or removing an AdSense slot
- Any change that touches the build pipeline
- Any work on the other four directory sites

## Kevin's working style

- Prefers explicit plans before implementation for anything non-trivial
- Values a decision log
- Works across Mac mini, MacBook Pro, and Windows — use cross-platform paths and shell commands; when platform matters, ask
- ITIL-minded — expects clear rollback paths for changes
