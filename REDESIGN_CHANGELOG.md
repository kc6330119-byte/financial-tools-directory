# Redesign Changelog

Narrative log of the Smart Investor redesign work. **Most recent milestone at the top.** Each entry captures what shipped, what it changed for users / Google / the business, and what's still open.

This file is the "release notes" view of the redesign. For the terse one-line-per-decision log, see [`REDESIGN_NOTES.md`](REDESIGN_NOTES.md). For the original homepage plan, see [`REDESIGN_PLAN.md`](REDESIGN_PLAN.md). For the AdSense-resubmission critical path, see [`ADSENSE_RESUBMISSION_PLAN.md`](ADSENSE_RESUBMISSION_PLAN.md).

---

## Milestone 3 — Advisor Compare feature (2026-04-18)

**Branch:** `redesign/advisor-compare`
**Commits:** (landed as four scoped commits — see git log)
**Type:** First non-migration milestone — net-new functionality, not a template rewrite.

### What changed

- **New page: `/compare.html`.** A disclosure-level side-by-side comparison of up to three fiduciary advisors. Renders columns for fiduciary status, rating, credentials, fee structure, minimum investment, firm type, specialties, and description. No "pros and cons" framing — just the firm's own disclosures laid out so they can be compared at a glance.
- **"+ Compare" toggle on every advisor listing and detail page.** Absolute-positioned on the card (outside the anchor, valid HTML) so the card's "view details" click behavior stays intact. Inline `.btn`-style toggle in the advisor-detail actions row.
- **Sticky compare bar** (site-wide, below the main content, above the newsletter). Fades in at ≥1 selected, shows count + chip list + Clear + Compare → CTA. Chips have per-item remove buttons. Cross-tab synced via the `storage` event.
- **Selection state.** `localStorage` key `smart-investor-compare` holds the list of `{slug, name}` objects (max 3). The compare page treats the URL query string (`?advisors=slug1,slug2`) as the source of truth when present, falling back to localStorage when the page is opened without params. Removing a column updates both the URL and localStorage so reload and share work identically.
- **Data delivery: new `/compare-data.json`** emitted at build time with richer fields than the existing `/search-index.json` (which stays focused on nav autocomplete). One fetch on page load, cached for the session.
- **`compare.html` is `noindex, follow`** — it's a tool, not content. Excluded from `sitemap.xml` automatically because it isn't in the sitemap builder's indexable-pages list.

### Why it helps

- **A genuinely finance-native feature, not just a restyle.** Every other advisor directory forces sequential browsing. Side-by-side disclosure comparison is what someone hiring an advisor actually wants to do — and the visual pattern is native to the spec-sheet aesthetic we've been building.
- **Portfolio reuse.** The pattern is directly portable to the other four directory sites (compare 3 splash pads, 3 dog groomers, 3 home-care agencies, 3 vets) — same URL shape, same localStorage key scheme, same sticky-bar UX. Genuine differentiator for all of them.
- **Zero backend.** All build-time static + client-side JS. Fits the "nothing runs at request time" constraint from the stack conventions cleanly.
- **Valid HTML.** The toggle sits outside the advisor card's anchor element (the old pattern of nested `<button>` inside `<a>` is invalid HTML and interacts badly with assistive tech — we avoided it via the new `<article><a/><button/></article>` structure).
- **Shareable URLs.** A comparison can be linked directly. Good for the audience that sends "check these three" links to a spouse or advisor-committee.
- **Accessibility.** Toggle is a real `<button>` with `aria-pressed` true/false and a paired `aria-label`. Disabled state guards the full-list case so a user can't accidentally add a fourth.

### Known gaps

- With only 5 sample advisors in the current local build, the compare page is lightly testable; it really shines once the Outscraper data lands and there are thousands of slug-addressable advisors.
- Compare bar uses a generic `box-shadow` that's slightly heavy on dark; could tune.
- No keyboard shortcut to open the compare page (e.g., `?`). Deferred.

---

## Milestone 2 — Directory pages (2026-04-18)

**Branch:** `redesign/directory-pages` (fast-forwarded to main, branch deleted)
**Commits:** `7604d10`, `729e7e8`, `e5726f7`, `2a30cc1`
**Templates rewritten:** `state.html`, `city.html`, `specialty.html`, `advisor.html`, `_advisor_card.html`
**Shell change:** `base.html` — one-line addition to broadcast a `smart-investor-theme-change` event
**CSS:** ~750 new lines appended to `static/css/custom.css` (no changes to the homepage component layer)

### What changed

- **State / city / specialty pages** traded blue-gradient heroes for an editorial page head: Fraunces display name, the existing `state.description` as a lede paragraph, a meta row with tabular-figure counts for listings and cities.
- **Advisor listings** converted from photo-headed cards to a **type-first list row**: firm name + fiduciary + rating on the top line, credential chips, a fee/minimum/firm-type stats line, specialty chips, a two-line description, a view-details affordance. One `_advisor_card.html` partial now drives listing UX everywhere it appears (state, city, specialty, and the advisor-detail "related advisors" section).
- **State-page sidebar** now holds a Leaflet map using **CartoDB Positron on light / Dark Matter on dark** (tile URL selected at init from `data-theme`, hot-swapped on theme toggle via the new event bus) plus a sticky city filter list with advisor counts. Markers use the `--gold` token in both themes so icons don't need to be rebuilt on theme change.
- **Specialty page** has a sticky state-filter sidebar and a new "other specialties" chip row at the foot. Specialty-icon emoji dropped.
- **Advisor detail page** restructured around a spec-sheet metaphor: About (prose), Specialties (chips), Fee Structure (warn-tinted mono chips — fee structure is a signal, treat it like one), Firm Details (two-column `dl` with mono-caps labels and Geist values), Professional Credentials (code + name + teaching description).
- **Advisor right sidebar** is tokenized: contact card with label/value rows, Call and Visit Website CTAs, a BrokerCheck verification card, and a three-link share row (Facebook, X, email).
- **Empty states on noindexed pages** now route to neighboring directories and FINRA instead of a dead end.

### Why it helps

- **Density.** The old card grid wasted vertical space on photo placeholders most firms don't have. The list row uses that space for signal (chips, stats, description) — more advisors visible on screen at every viewport width.
- **Scannability.** Rating, fee, minimum, and count all render in Geist Mono with tabular figures. Columns align vertically across rows without being a literal table, so the eye can compare at a glance.
- **Trust signaling.** Fiduciary status moved from a gradient pill to a mono-caps `--gain`-tinted badge next to the firm name — more visible. Fee structure shown in `--warn`-tinted mono chips rather than generic pastel pills.
- **Map reads correctly on dark.** The old OSM tiles looked bright-white inside a dark shell. CartoDB Dark Matter matches the theme without adding a new dependency (tiles are free with attribution).
- **Reusable event bus.** The `smart-investor-theme-change` pattern is now available to any future page-level script that needs to react to light/dark — relevant once we add charts on blog posts or advisor pages.
- **SEO signals preserved.** Meta title, meta description, canonical URL, FinancialService JSON-LD schema on advisor pages, FAQPage schema on homepage, and every URL are unchanged. h1 copy changed to editorial voice ("Fiduciary advisors in *{{ state }}*") but the keyword-match delta is negligible for ranking purposes and more accurate for the audience we want.

### Known gaps

- `tools.html`, `category.html`, `tool.html` still Tailwind-styled.
- `blog.html`, `post.html` still Tailwind-styled.
- `about.html`, `contact.html`, `privacy.html`, `terms.html`, `success.html` still Tailwind-styled **and** still contain copy referencing the old "Financial Tools Directory" brand that predates the advisor-directory pivot. Copy refresh here is also on the AdSense-resubmission critical path.

---

## Milestone 1 — Homepage redesign (2026-04-18)

**Branch:** `redesign/homepage-finance-native` (pushed directly to `main` at Kevin's request; branch deleted)
**Commits:** `13a61fe`, `6e3ba61`, `ae284ea`, `28f7b8d`, plus `3bb9ff9` (gitignore cleanup)
**Templates rewritten:** `index.html` (14-section rebuild)
**Shell:** `base.html` — no-flash theme script, font preloads, theme toggle (desktop + mobile), inline-SVG brand mark, restyled newsletter and footer
**Assets:** `static/fonts/` (6 WOFF2 files, 220 KB total), `static/images/logo.webp` (11 KB, down from 1.1 MB), `static/css/custom.css` (37 KB, new primary style layer)
**Build:** additive — `build_homepage()` in `build.py` now passes `specialty_counts` and `max_state_count` to the template. No schema, no pipeline, no URL changes.

### What changed

- Full visual pivot from blue-gradient SaaS hero + card grid to a **finance-native, information-dense layout**.
- Homepage sections top to bottom: market ticker strip → hero (locator + 3-stat block) → credential legend (`CFP CFA CPA ChFC RICP CLU EA` chips with tooltips) → **Ad Slot A** → featured-advisors comparison table → specialty matrix with live per-specialty advisor counts → **Ad Slot B** → state heatmap grid (CSS `--intensity` from `count/max_state_count`) → tools list → blog preview → **Ad Slot C** → editorial "no paid placements" block → FAQ accordion (schema preserved).
- **Typography:** Fraunces (editorial display serif) + Geist Sans (UI) + Geist Mono (numerics). Self-hosted variable WOFF2, Latin + Latin-ext subsets only. Tabular lining figures enforced globally on numeric contexts.
- **Color tokens:** light default + dark toggle. Semantic `--gain` / `--loss` / `--warn` reserved strictly for data. Muted-navy accent on light, gold on dark.
- **Theme toggle:** inline pre-paint script avoids flash-of-wrong-theme; localStorage persists choice; `prefers-color-scheme` is the fallback.
- **Brand mark:** inline SVG (three ascending bars, gold top) in nav and footer. Zero image fetch on the critical path.
- **AdSense:** three reserved `<div class="ad-container">` placeholders at the approved positions, each with a CLS-safe `min-height`. Awaiting AdSense re-approval to populate.

### Why it helps

- **Credibility.** Finance-native register (data density, tabular figures, editorial voice) signals *this is a serious tool, not a lead-gen funnel* — better match for an audience deciding whether to trust the listings enough to click through.
- **Performance.** Self-hosted fonts = zero third-party requests on the critical path. Inline SVG brand mark = zero image fetch. 11 KB WebP logo (from 1.1 MB PNG) used only in social-share meta tags. Critical path ~216 KB total. Comfortably inside the 1.5-second FCP-on-4G budget.
- **CLS.** Ad slots have reserved heights, tabular figures keep numeric column widths stable, SVG icons don't pop in after fonts load.
- **Accessibility.** SVG icons (screen readers narrate the label, not the emoji codepoint). Tokenized color pairs tested against WCAG AA on both themes. `focus-visible` outlines use the accent token.
- **SEO signal stability.** All JSON-LD schemas preserved (`FAQPage`, `WebSite`), all canonical / OG tags unchanged, all URLs unchanged. Only the visible h1 and body copy moved to editorial voice.
- **Playground purpose fulfilled.** The component patterns established here (ticker, hero-stats, credential legend, advisors-table, specialty-tile, state-tile heatmap, tool-row, blog-card, editorial block, FAQ accordion) are now ready to port to `holisticvetdirectory.com`, `splashpadlocator.com`, `seniorhomecarefinder.com`, `doggroomerlocator.com`.

### Known gaps

- Market ticker depends on `/.netlify/functions/market-data`. On local preview it shows *"Market data unavailable"* — this is the intended graceful-degrade.
- Site is pre-AdSense-approval; three slots ship empty.

---

## Milestone 0 — Baseline inventory + planning groundwork (2026-04-18)

**No commits** — discovery + documentation.

### What happened

- Loaded the personal `smart-investor-redesign` skill plus its references (stack-conventions, adsense-constraints, finance-native-direction, directory-patterns).
- Loaded `frontend-design` and `web-design-guidelines` skills.
- Read `CLAUDE.md`, the Jinja build (`build.py`), `config.py`, `netlify.toml`, all 17 templates, the existing `custom.css`, and `ADSENSE_RESUBMISSION_PLAN.md`.
- Reproduced the existing build locally — 39 URLs output from sample data, no errors. (Noted the `venv/` contained a broken cross-machine symlink; non-blocking for the redesign.)
- **Critical audit finding:** grep for `adsbygoogle` / `data-ad-slot` returned zero active slots anywhere — only the loader script in `base.html`. Homepage had no slots to preserve, so the plan could propose reserved positions freely (flagged for approval rather than assumed).
- Produced [`REDESIGN_PLAN.md`](REDESIGN_PLAN.md) — inventory summary, proposed homepage structure, typography system, color palette, ad-slot placement proposal, dependency requests, and 10 open questions.
- Created [`REDESIGN_NOTES.md`](REDESIGN_NOTES.md) — one-line-per-decision log.

### Why it helped

- Caught the Python 3.13 + `pyairtable 2.3.3` + `pydantic` dep conflict in the local venv before it bit during implementation.
- Made every AdSense-slot decision explicit and approved, per the personal skill's hard rule.
- Captured the *design playground* framing in writing so scope didn't drift into the AdSense-resubmission content work (which has its own plan).

---

## How this file is maintained

- **One section per shipped milestone**, most recent at the top.
- Each section: date, branch, commits (short SHAs), scope, what changed, why it helps, known gaps.
- **"Why it helps" stays outcome-focused** — what the user / Google / the business gets. Technical minutiae belong in [`REDESIGN_NOTES.md`](REDESIGN_NOTES.md).
- **Past milestones are immutable.** When a known gap is later closed, note it in the milestone that closed it; do not edit earlier entries.
- When the redesign work extends from `smart-investor` to one of the other four directory sites (holistic vet, splash pad, senior home care, dog groomer), give that work its own section and note which homepage milestone's patterns it inherits.
