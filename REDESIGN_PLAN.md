# Homepage Redesign Plan — Smart Investor

**Status:** Proposed. Awaiting Kevin's review before any CSS or template code is written.
**Scope:** Homepage (`templates/index.html`) only, plus whatever in `base.html` is visible on the homepage (nav, footer, newsletter). No other page types.
**Branch (planned):** `redesign/homepage-finance-native` — not created yet.

---

## 1. Inventory summary

### Build script

- **Entry point:** `build.py` at project root, run as `python3 build.py`.
- **Netlify invocation:** `netlify.toml` → `pip install -r requirements.txt && python build.py`, publishes `dist/`.
- **Engine:** Python 3.9 target (per `netlify.toml`), Jinja2 static site generation. Falls back to sample data when `AIRTABLE_API_KEY` is unset — build succeeds without credentials.
- **Output directory:** `dist/` (gitignored via `.gitignore` — not checked; will verify before committing).
- **Reproducibility:** Verified locally today. Sample-data build produces **39 URLs** (sitemap count); no errors. Python 3.13 + existing system deps worked; the repo's `venv/` contains a broken cross-machine symlink and should be rebuilt before any Airtable-mode testing. Not a blocker for the redesign itself.

### Template layout

`templates/` (17 files):

| File | Purpose |
|---|---|
| `base.html` | Global shell — `<head>`, nav, footer, newsletter, AdSense loader, Tailwind CDN, GA, search JS |
| `index.html` | **Homepage (focus of this milestone)** |
| `_advisor_card.html` | Advisor card partial (reused on state/city/specialty pages) |
| `state.html`, `city.html`, `advisor.html`, `specialty.html` | Advisor directory pages |
| `tools.html`, `category.html`, `tool.html` | Preserved "Investor Tools" section from original site |
| `blog.html`, `post.html` | Blog |
| `about.html`, `contact.html`, `privacy.html`, `terms.html`, `success.html` | Static pages |

### Static assets

- `static/css/custom.css` — **3.1 KB**, thin supplement to Tailwind (line-clamp shims, prose styles for blog, focus outlines, print rules).
- `static/images/` — `logo.png` (1.1 MB — large; flag for optimization later), `README.txt`.
- No JS files in `static/`; all JS is inline in templates.

### Current CSS approach

- **Tailwind via CDN:** `<script src="https://cdn.tailwindcss.com"></script>` in `base.html:67`.
- **Inline JIT config** in `base.html:69-113` — custom `primary` (blue 500=`#3b82f6`), `secondary` (teal 500=`#14b8a6`), `accent` (amber 500=`#f59e0b`).
- **No build step** for CSS. Utility classes compile at runtime in the browser via the CDN.
- Hand-authored `custom.css` handles the gaps (prose, print, `.ad-container` reserved space).
- **Implication for redesign:** The Tailwind CDN locks us to Tailwind's defaults (no custom fonts without adding `<link>` tags, no custom font-feature-settings without arbitrary values, no real dark-mode token system). For a finance-native redesign with tabular figures, theme tokens, and distinctive typography, I'd recommend **keeping the Tailwind CDN as a safety net but writing a small hand-authored `custom.css` as the primary style layer** for the redesigned homepage. No build step added. See Open Question 7.

### AdSense slot audit

- **Publisher ID:** `ca-pub-9265762311868507` (in `base.html:63` and `ads.txt`).
- **Loader:** `base.html:63` — loads `adsbygoogle.js` on every page.
- **Reserved-space CSS:** `base.html:122` — `.ad-container { min-height: 90px; }`.
- **Actual `<ins class="adsbygoogle">` tags in templates:** `grep` returned **zero matches**. The site ships the loader but no active slot placements.
- **`.ad-container` placeholder divs (reserved space, empty):**

| File | Line | Location |
|---|---|---|
| `templates/tool.html` | 73, 170, 180 | 3× on individual tool pages |
| `templates/tools.html` | 28, 100 | 2× on the tools hub |
| `templates/category.html` | 19 | 1× on category pages |
| **`templates/index.html`** | **(none)** | **Homepage has zero AdSense slots today.** |

- **Context (from `ADSENSE_RESUBMISSION_PLAN.md`):** The site is in a **pre-submission resubmission posture** — previously rejected, now rebuilt as an advisor directory, awaiting content-quality thresholds before resubmitting to AdSense. Ad `<ins>` tags will be added once approval is granted; the empty `.ad-container` divs are forward-looking reserved space.
- **What this means for the homepage redesign:** There are no existing homepage slots to preserve. But the skill's hard rule — *don't add AdSense slots without asking first* — still applies. Below (§5) I propose reserved slot locations and dimensions for Kevin to approve, not populate. The redesigned layout will ship with empty `.ad-container` placeholders sized for CLS-safe insertion later, matching the pattern already used on tool pages.

---

## 2. Proposed homepage structure (mobile-first, section by section)

The existing homepage has the right information architecture. The redesign reframes it in a finance-native register: data-dense, numeric-first, confident typography, dark by default. No new page types, no new data requirements. Every section below maps to data already produced by `build_homepage()` in `build.py:621`.

### Section stack (top to bottom)

1. **Ticker strip (new; optional — Open Question 3)**
   Thin utility bar above the nav. Monospace. `SPX · DJI · IXIC · VIX`, each with level, delta, pct change in semantic green/red. Reuses existing `/.netlify/functions/market-data`. Degrades silently if JS or the function fails. 32 px tall desktop, hides on very small screens or collapses to one ticker. Mobile-first: one scrolling row, no overflow layout breakage.

2. **Nav (preserved from `base.html`, restyled only)**
   Sticky, borderless on dark, 1 px divider on light. Same links, same mobile hamburger, same search. Finance-native: brand mark gets a bigger, opinionated wordmark treatment; dropdowns use the new font system.

3. **Hero — locator + stats**
   - **Left (or top on mobile):** editorial-finance headline. Example voice draft: *"Find a fiduciary advisor. Compare credentials, fees, and minimums — not marketing pages."* Tabular figures inline (`{{ total_advisor_count }}` in mono).
   - **Primary action:** state picker (existing dropdown → styled as a real search input with state abbr ghosted). Secondary: "Use my location" (progressive geolocation → IP lookup disabled; falls back to dropdown if denied — see Open Question 4).
   - **Right (desktop) / below (mobile):** a 3-stat block, Bloomberg-style:
     - `{{ total_advisor_count }}` **Advisors listed**
     - `51` **States + DC**
     - `{{ total_posts }}` **Published guides**
   - No gradient hero. No stock illustration. One dominant numeric figure.

4. **Credential legend (replaces current "Trust Signals" row)**
   The current row — "✓ Verified credentials / ✓ Fiduciary / ✓ Free to search / ✓ No commitment" — is generic. Replace with a scannable credential legend: `CFP CFA CPA ChFC RICP CLU EA`, each a chip with a hover/tap tooltip describing what it means. Directly useful. Reinforces the site's trust claim through specifics, not adjectives.

5. **[Ad Slot A — reserved space, requires approval]**
   Responsive horizontal unit. ~728×90 desktop / 320×100 mobile anchor. Above the fold on desktop, below the hero on mobile. See §5.

6. **Featured advisors — data table (replaces current card grid)**
   Finance-native reframe. Same 6 advisors, rendered as a true comparison table at `≥768px`, reflowing to stacked label:value rows on mobile (CSS `grid-template-rows`, no JS).
   - **Columns:** Firm, City/State, Credentials, Fee structure, Minimum, Rating, — (CTA arrow).
   - **Tabular figures** on all numeric columns (`font-variant-numeric: tabular-nums`). Minimums right-aligned.
   - **Fiduciary** shown as a badge in the first column, not a separate bucket.
   - Subtle zebra banding or a single hairline divider per row. No card shadows.
   - On small screens: each row becomes a stacked "record" with label columns aligned on the left.

7. **Specialty matrix**
   The existing 5-col grid of 10 specialties, reframed: drop emoji icons in favor of a small number badge showing **advisor count per specialty** (we already compute this logic implicitly — easy extension). Each tile: specialty name (display font), count (mono, tabular), one-line description. Rationale: advisors-per-specialty is a real numeric signal; emoji feels childlike against the finance direction.

8. **[Ad Slot B — reserved space, requires approval]**
   In-content responsive unit. See §5.

9. **State heatmap grid (replaces current "Browse by State")**
   Same grid, same 51 tiles, same links — but each tile gets a background-opacity tint scaled by `state_counts[slug]`. Dense states glow; sparse states read as outlines. Preserves all existing URLs and the "noindex < 3 advisors" build logic. This is the one section closest to a "dashboard" aesthetic.

10. **Investor Tools preview**
    Preserved. Restyled as a tight list-table rather than a card grid: 4 rows × (logo, name, category, pricing, rating). Same destination links. Honors the "don't break the tools section" constraint.

11. **From the Blog**
    Preserved. 3 recent posts. Replace the gradient placeholder heroes with a clean text-first treatment (category eyebrow, headline in display font, 2-line excerpt, date in mono). No placeholder images; if `post.featured_image` exists, use it; otherwise the card is type-only.

12. **[Ad Slot C — reserved space, requires approval]**
    In-content responsive unit. See §5.

13. **Editorial block (replaces current "SEO Text Block")**
    The current two paragraphs are serviceable but feel growth-marketing. Rewrite in editorial-finance voice (confident, skeptical, specific — *"Most directories take paid placements. We don't. Every advisor here is listed on the strength of their credentials and fee disclosure."*). Max 120 words. Keeps SEO weight; drops the breeziness.

14. **FAQ**
    Preserved. Same four Q&A entries, same JSON-LD `FAQPage` schema. Restyle only — rules above/below rather than pill-shape containers; chevron rotates on open.

15. **Newsletter (in `base.html`)**
    Preserved. Restyled to match dark/light tokens. Netlify Forms integration untouched.

16. **Footer (in `base.html`)**
    Preserved, retypeset. No link changes.

### Layout tokens (mobile-first)

- Container: `max-width: 1200px` at desktop; 20 px gutter at mobile, 48 px at desktop.
- Vertical rhythm: sections separated by 64 px mobile / 96 px desktop.
- Breakpoints: **320 / 480 / 768 / 1024 / 1280**. All sections render usefully at 320 px (the finance-native-direction requirement).

---

## 3. Typography system

**Two families, plus the matching monospace sibling for numerics.**

### Display (headlines, section eyebrows)

**Fraunces** — variable serif, open-source (Google Fonts / OFL), built for editorial. Adjustable `opsz`, `wght`, `SOFT` axes. Reads confident and contemporary without the corporate-bland feel of a neutral grotesque. Pairs with the editorial-finance voice.

- Usage: h1, h2, the hero stat labels, the eyebrow above sections.
- Fallback stack: `"Fraunces", ui-serif, Georgia, "Times New Roman", serif`.

### Body / UI (paragraphs, table content, nav, buttons)

**Geist Sans** — Vercel's open-source UI sans. Designed for product/data interfaces. Tabular figures by default. High x-height, narrow counters, reads dense.

- Usage: everything that isn't a display headline or a number in a table.
- Fallback stack: `"Geist", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif`.

### Numeric / mono (tickers, table figures, price ranges, minimums, credential codes)

**Geist Mono** — companion to Geist Sans. Same family DNA, same metrics. Numbers line up cleanly with the sans.

- Usage: ticker strip, table figures, `$`/`%` values, credential chips (CFP, CFA…).
- Fallback stack: `"Geist Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace`.

### Tabular figures — enforced globally

Tabular lining figures on every numeric context:

```css
:where(table, .stat, .ticker, .mono, .nums) {
    font-variant-numeric: tabular-nums lining-nums;
    font-feature-settings: "tnum", "lnum";
}
```

This is the single most important typographic rule of the redesign. Columns that don't align are a finance-native credibility leak.

### Rationale for avoiding the obvious

- **Inter / Roboto / Arial / SF / Space Grotesk:** excluded — too generic, breaks the finance-native intent and violates my design skill's rules against convergence.
- **IBM Plex Sans** was a strong alternative (and would be my #2 pick). It has the institutional weight we want. I'm favoring Geist because Plex Sans is getting common enough that it reads as "default developer-tool" rather than "designed choice." Fraunces + Geist is more distinctive.
- **Source Serif / Merriweather / PT Serif:** too stationery; Fraunces has more edge.

### Font loading

- **Proposed:** Google Fonts CDN (`<link>` tags added to `base.html <head>`). Two requests. `rel="preconnect"` + `display=swap`. No build change.
- **Alternative (flagged for approval):** Self-host the three .woff2 files in `static/fonts/` (~450 KB total). Faster, zero third-party request, slightly bigger repo. See Open Question 6.

---

## 4. Color palette

**Dark-first. Light theme as a toggle.** (The finance-native-direction reference explicitly positions dark as "often the default" for finance.) Light theme is the fallback for AdSense reviewers and anyone who prefers it; both themes ship from day one.

### Semantic first

Three colors are non-negotiable and have fixed meaning across both themes:

| Token | Dark | Light | Meaning |
|---|---|---|---|
| `--gain` | `#3DDC84` | `#13A85B` | Up, positive, growth |
| `--loss` | `#FF5A5F` | `#D03A40` | Down, negative, loss |
| `--warn` | `#F4B73E` | `#B8860B` | Caution, pending, amber |

Never used decoratively. Never in the brand accent. Never on non-data elements.

### Dark theme (default)

| Token | Value | Usage |
|---|---|---|
| `--bg` | `#0B0D10` | Page background — near-black with a 2° blue lean, avoids pure black's OLED harshness |
| `--surface` | `#13171C` | Cards, table rows, nav bar |
| `--raised` | `#1A1F25` | Hovered/selected surfaces, dropdowns |
| `--text` | `#E6EAF0` | Primary text |
| `--text-muted` | `#9AA3AD` | Secondary text, labels |
| `--text-faint` | `#5B6370` | Tertiary, hints, disabled |
| `--border` | `#242A31` | Dividers, card borders, table lines |
| `--accent` | `#E8B547` | Brand accent — muted gold. Used sparingly: CTA underlines, selected states, logo mark. Chosen because blue is the tech-SaaS default and doesn't carry finance weight; gold signals value without the "crypto neon" trope. |

### Light theme

| Token | Value | Usage |
|---|---|---|
| `--bg` | `#F7F7F4` | Paper — warm off-white, not clinical `#FFFFFF` |
| `--surface` | `#FFFFFF` | Cards, table rows |
| `--raised` | `#FFFFFF` with `box-shadow` | Hovered surfaces |
| `--text` | `#0B0D10` | Primary |
| `--text-muted` | `#596070` | Secondary |
| `--text-faint` | `#8B95A3` | Tertiary |
| `--border` | `#E6E8ED` | Dividers |
| `--accent` | `#1F3A5F` | Navy — the natural editorial-finance light partner to gold (think: Economist, FT). |

### Theme toggle

- Small button in nav (sun/moon glyph, no emoji).
- Persists to `localStorage` under `smart-investor-theme`.
- Initial render honors `prefers-color-scheme` if no stored preference; otherwise respects stored choice.
- Inline head script (~400 B) sets the `<html data-theme="…">` attribute before first paint to avoid flash-of-wrong-theme. Safe because it runs synchronously before CSS parse.

### Current Tailwind theme

The existing `primary/secondary/accent` palette in `base.html:69-113` is decorative and non-semantic (blue/teal/amber with no fixed meaning). It's used by every other page type. **The redesign won't delete it** — it stays available to the preserved templates (tools, blog, state, etc.) until those pages are redesigned in a later milestone. The new CSS custom properties layer on top.

---

## 5. AdSense slots in the new layout

**Summary:** The current homepage has **zero** active AdSense slots. I propose **three reserved placements** for the redesign, all as empty `<div class="ad-container">` elements with explicit CLS-safe `min-height`. Kevin populates the `<ins class="adsbygoogle">` with `data-ad-client` and `data-ad-slot` values when AdSense resubmission is approved.

### Current state (for the record)

| Slot | Location | Notes |
|---|---|---|
| — | none on homepage | No `<ins>` tags; no `.ad-container` placeholders in `index.html` |

### Proposed placements — requires Kevin's approval before implementation

| New slot | Where in new layout | Approx. size | Reserved `min-height` | Rationale |
|---|---|---|---|---|
| **Slot A** (above the fold on desktop) | Between §4 Credential legend and §6 Featured advisors table | Responsive horizontal — 728×90 desktop / 320×100 mobile anchor | 100 px | Standard above-content leaderboard position. Clear separation from hero — no chance of being confused with the search action |
| **Slot B** (mid-content) | Between §7 Specialty matrix and §9 State heatmap grid | Responsive — Google auto size | 250 px | Natural break between two browse affordances; user has consumed enough content to render a relevant ad |
| **Slot C** (lower-content) | Between §11 Blog preview and §13 Editorial block | Responsive — Google auto size | 250 px | Before the final editorial/FAQ block; captures scroll-depth users |

**Constraints honored** (from `references/adsense-constraints.md`):

- Only **one** slot above the fold (Slot A, desktop only on the fold; on mobile it sits below the hero).
- Every slot has reserved `min-height` → zero CLS.
- Visual separation preserved: no ad sits flush against a CTA or interactive element.
- No sticky/anchor ad proposed for the homepage this milestone — that's a site-wide change that belongs in `base.html`. If Kevin wants one, we add it in a follow-up (Open Question 3, companion).

**Per the skill's hard rule**, I will not ship ad-slot markup until Kevin explicitly approves these three positions and sizes.

---

## 6. Dependencies requested — flagged for approval

| Item | Type | Rationale | Approval required? |
|---|---|---|---|
| **Fraunces** (Google Fonts) | Font CDN link | Display/serif family for editorial-finance voice; open-source, free, variable font | **Yes — adds a third-party CDN request** |
| **Geist Sans + Geist Mono** (Google Fonts) | Font CDN link | Body/UI family + numeric sibling; open-source, free | **Yes — adds a third-party CDN request** |
| **Alternative:** self-host all three as `.woff2` in `static/fonts/` | Repo bytes | Removes third-party request; ~450 KB added to repo | **Pick one or the other with Kevin** |
| **No new JS libraries** | — | Theme toggle is ~30 LOC vanilla; market ticker reuses existing Netlify function; FAQ accordion already exists | No |
| **No Tailwind config/package change** | — | Keep the CDN + inline config as-is; new styles live in `static/css/custom.css` | No |
| **No build-pipeline change** | — | No PostCSS, no bundler, no new Python package | No |

I would not introduce Alpine.js, htmx, or any icon-set package for this milestone. The entire interactive surface is small enough to author in vanilla JS.

---

## 7. Open questions (please answer before I start building)

1. **Theme default — dark or light?** My proposal: dark. The resubmission posture makes this a real question — an AdSense reviewer's first impression is a light-preferring desktop. If you want light-as-default with a dark toggle, I'll flip it. No design cost either way; one CSS variable flip.
2. **AdSense slot approval.** Sign off on the three positions in §5, or redline. Also: do you want a site-wide sticky anchor ad proposed as a separate follow-up task?
3. **Market ticker location.** Keep it homepage-only as today, or hoist to a site-wide top bar (appears on every page)? Site-wide is higher-impact but means editing `base.html` more deeply.
4. **"Use my location" button.** OK to add progressive geolocation (asks browser permission, falls back to the state dropdown if denied or unsupported)? No IP lookup, no third-party service.
5. **Featured advisors — table or cards?** My proposal: data table at ≥768 px, stacked rows at <768 px. Alternative: keep the card grid but restyle in the new tokens. The table is more finance-native; cards are a safer SEO/visitor experience. I'll go with whichever you pick.
6. **Font loading — Google Fonts CDN vs self-host.** See §6. Tradeoff: one third-party request (simpler) vs ~450 KB in the repo (faster, fewer moving parts).
7. **Primary style layer — Tailwind CDN or hand-authored CSS.** My proposal: keep the Tailwind CDN in place (so nothing on the other page types breaks), but write the redesigned homepage primarily in a hand-authored CSS block in `static/css/custom.css` using the new tokens. This avoids fighting Tailwind's defaults for typography, tabular figures, and dark-mode tokens, and stays within the "no build step" constraint. Alternative: stay 100% inside Tailwind utilities with arbitrary values — doable but verbose and less readable.
8. **Scope: `base.html`.** Nav, footer, newsletter, AdSense loader, font `<link>`s all live in `base.html`. Restyling them is necessary for the homepage to feel cohesive, but changes there also affect every other page. Am I cleared to touch `base.html` for (a) font links, (b) theme-toggle button in nav, (c) new CSS variable declarations, (d) restyled footer and newsletter — with the understanding that other page types inherit these changes? Or strictly homepage template only?
9. **Copy rewrite.** OK to rewrite the homepage microcopy (hero headline, trust signals, editorial block, CTA labels) in the finance-native editorial voice? Or keep existing strings and only restyle? My proposal: rewrite within this milestone — voice is half of the finance-native direction.
10. **Rollback plan.** The redesign lives on `redesign/homepage-finance-native`. Rollback = `git checkout main` or a revert of the branch merge; no data or URL changes, so rollback is clean. Confirm this posture is sufficient, or do you want a feature flag / toggle approach?

---

## Out of scope for this milestone (confirmed)

- Airtable schema or data pipeline changes
- URLs, slugs, canonical tags (all preserved)
- New Airtable fields
- Other page types (state, city, advisor, specialty, tools, blog, static)
- The other four directory sites (holistic vet, splash pad, senior home care, dog groomer)
- Deploying to production / Netlify main branch
- Image optimization of `static/images/logo.png` (a follow-up task)
- Blog content, listing data quality, advisor imports (tracked separately in `ADSENSE_RESUBMISSION_PLAN.md`)

---

*Next step:* Kevin reviews and answers Open Questions 1–10. On approval, I create the `redesign/homepage-finance-native` branch, append decisions to `REDESIGN_NOTES.md`, and begin implementation in the order: tokens → typography → base.html shell changes → homepage sections top-to-bottom.
