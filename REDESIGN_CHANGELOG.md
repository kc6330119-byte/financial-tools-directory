# Redesign Changelog

Narrative log of the Smart Investor redesign work. **Most recent milestone at the top.** Each entry captures what shipped, what it changed for users / Google / the business, and what's still open.

This file is the "release notes" view of the redesign. For the terse one-line-per-decision log, see [`REDESIGN_NOTES.md`](REDESIGN_NOTES.md). For the original homepage plan, see [`REDESIGN_PLAN.md`](REDESIGN_PLAN.md). For the AdSense-resubmission critical path, see [`ADSENSE_RESUBMISSION_PLAN.md`](ADSENSE_RESUBMISSION_PLAN.md).

---

## Side-milestone — Mailchimp newsletter integration (2026-04-18)

**Branch:** `redesign/mailchimp-newsletter`
**Commits:** single commit
**Files:** `templates/base.html` only
**Type:** Infrastructure migration, not a design milestone — kept separate from the redesign numbering.

### What changed

- The site-wide newsletter form (in `base.html`, visible above the footer on every page) now posts directly to Mailchimp instead of Netlify Forms. Form action: `https://doggroomerlocator.us12.list-manage.com/subscribe/post?u=…&id=…&f_id=…`.
- `target="_blank"` opens Mailchimp's double-opt-in confirmation page in a new tab. Our side optimistically swaps to "Subscribed. Check your inbox to confirm." after the native submit fires.
- Mailchimp's list-specific bot honeypot (`b_21343a587fbb950d8b649ee6d_970ba04869`) preserved verbatim, kept offscreen with `aria-hidden="true"` and `tabindex="-1"`.
- Hidden `<input name="SITE" value="smart-investor">` tags every subscription with its source site. Mailchimp silently drops unknown merge fields, so this is a no-op until Kevin adds a `SITE` merge field to the shared audience — at which point source segmentation starts working retroactively.
- **Contact form on `contact.html` unchanged** — still routes through Netlify Forms, which is where Kevin wants those specific submissions to land.

### Why it helps

- **Real list, not a dashboard.** Netlify Forms collects subscriptions but doesn't actually email anyone. Mailchimp puts subscribers into the shared audience Kevin uses across all five directory sites, making the newsletter operational instead of theoretical.
- **Zero dependency cost.** None of Mailchimp's embed bloat imported: no jQuery, no `mc-validate.js`, no `classic-061523.css`, no 400-line SMS-phone country dropdown. Critical-path byte count unchanged.
- **Cross-site source attribution** via the SITE tag — the shared audience can segment subscribers by which of the five sites brought them in, so newsletter content can be targeted later if Kevin wants.
- **Browser-native email validation** retained (no `novalidate` attribute). Invalid emails don't trigger the optimistic UI swap.

### Known gaps

- The `SITE` merge field isn't configured in the Mailchimp audience yet. Until Kevin adds it, source tagging drops silently — subscribers still get added, just without the `smart-investor` tag.
- Opening Mailchimp's confirmation page in a new tab is slightly less elegant than an inline thank-you state. The alternative (JSONP to `/subscribe/post-json?&c=?`) adds a small amount of JS complexity for a marginal UX gain. Revisit if subscriber drop-off turns out to be a problem.

---

## Milestone 5 — Tools hub, category, tool detail (2026-04-18)

**Branch:** `redesign/tools`
**Commits:** (two scoped commits — see git log)
**Templates rewritten:** `tools.html`, `category.html`, `tool.html`
**CSS:** new `.tool-list`, `.tool-card`, `.category-section`, `.tool-head`, `.feature-list`, `.audience-chips`, `.tool-cta`, `.related-tools` blocks

### What changed

- **Tools hub (`/tools.html`)** replaces its blue-gradient hero with an editorial page head and editorial-voice positioning copy ("A reference library of tools we've used and reviewed"). Each `config.CATEGORIES` entry renders as a category section with a tokenized header row (name · description · count · "View all →") and a stacked list of `.tool-card` rows for that category.
- **Category listing (`/category/*.html`)** uses the same `.tool-card` row pattern, surfaces the category description from `config.CATEGORIES` as the page-head lede, and closes with a reusable `.specialty-chip-row` pointing to every other category.
- **Tool detail (`/tool/*.html`)** now opens with a `.tool-head` block — big logo + Fraunces name + mono-caps meta line (rating · pricing model · price range · featured pill if applicable) + tokenized category tags + a primary "Visit vendor" button. Body runs in the shared `.content-grid content-grid--right` layout with detail-cards for About, Features (clean typographic checklist), and "Best for" (audience chip row). Sticky right sidebar holds a spec-sheet `<dl>` (pricing, price range, API, Mobile, data sources with `.is-gain` tokens on the Yes values) and a gradient-accent `.tool-cta` card.
- **Each `.tool-card` row includes `.bool-chip` pills** for API availability and Mobile app, rendered in `--gain`-tinted mono-caps when true. At-a-glance comparison of booleans without fake stars or icons.
- **AdSense slot placements preserved.** tools.html has two slots (`tools-hub-a` above content, `tools-hub-b` below). category.html has one (`category-a`). tool.html has three (`tool-detail-a` above body, `tool-detail-sidebar` inside the aside, `tool-detail-b` before related). All CLS-safe with `.ad-slot--leaderboard` (min-height 100) or `.ad-slot--in-content` (min-height 250). `data-slot` attributes name each position so Kevin can populate with unique AdSense slot IDs after resubmission approval.
- **Related tools** render as a horizontal 4-column card row at desktop, stacking to 1 col on mobile. Shares DNA with the blog's `.related-post` pattern.

### Why it helps

- **Preserves the site's unique differentiator.** Every other advisor directory is just advisors. The Tools section is what makes smart-investor stand out; now it looks like a proper finance-native product directory instead of generic SaaS pricing-comparison boilerplate.
- **Comparison-ready design.** The API / Mobile boolean chips and sidebar spec-sheet make side-by-side comparison easy even without visiting multiple detail pages. Consistent with the finance-native "show me the data" posture.
- **Category-tag navigation.** Tools are often multi-category (TradingView: Technical Analysis + Trading Platforms). Clicking any tag jumps to the relevant category page — better browse than "one category per tool" would allow.
- **Ad placements now visually consistent** across homepage, directory, tools — same CLS-safe reserved space with a subtle "Advertisement" placeholder, so whatever AdSense decides to serve post-approval will land predictably.
- **Tools section inherits the BrokerCheck / fee-disclosure editorial voice** from the advisor directory, so the whole site reads as one product rather than two.

### Known gaps

- Empty `related_tools` is common in the current sample data because the three seed tools are each in mutually-disjoint categories. Once Airtable has the full 34 tools, the "related tools" row will populate properly.
- The `.tool-cta` gradient block uses the accent as its background. On dark theme, gold-on-near-black is legible but the accent-ink contrast is intentional; evaluate in production and retune if needed.

---

## Milestone 4 — Blog templates + prose tokenization (2026-04-18)

**Branch:** `redesign/blog`
**Commits:** (landed as three scoped commits — see git log)
**Templates rewritten:** `blog.html` (listing), `post.html` (reading experience)
**CSS:** `.prose` block fully tokenized; new `.filter-pills`, `.post-index`, `.article-*`, `.disclaimer-box`, `.related-posts`, `.pullquote`, `.data-callout` blocks

### What changed

- **Fixed a real dark-mode bug.** The old `.prose` styles had hardcoded `#1f2937` / `#2563eb` / `#e5e7eb` / `#4b5563` / `#f9fafb` values. Every blog post on dark was rendering near-black headings and table-header text on a near-black background. All replaced with `--text` / `--accent` / `--border` / `--text-muted` / `--bg` tokens. Closes a Milestone-0 known gap.
- **Blog listing is now a magazine index** — stacked rows with divider lines, mono-caps meta row (category · reading time · date · author), Fraunces title, Geist excerpt. No photo cards. Category-filter pills in the new tokenized chip style; URL-hash deep-linking from the homepage category chips preserved.
- **Post reading experience rebuilt** as an editorial page head + long-form prose. Large Fraunces h1 with `SOFT` axis for editorial warmth, deck paragraph in Geist 1.2rem, byline + category + reading-time + date in mono-caps. Prose body runs at 1.0625rem / 1.75 line-height / 66ch measure — proper reading typography.
- **New prose component patterns:** `.pullquote` (Fraunces italic with gold accent rule) and `.data-callout` (big Fraunces numeric figure + mono label + Geist note, gold-accented left border) — optional editorial touches authors can use in markdown via raw HTML.
- **Reading time** computed in Jinja using the built-in `wordcount` filter — no `build.py` change required. Formula: `(content | striptags | wordcount // 225) + 1`, minimum 1.
- **Disclaimer box tokenized** — `--warn`-tinted left border and background, mono-caps "Disclaimer" label. Content unchanged (legally load-bearing).
- **Related posts as a 3-column card row** at desktop, single-column stack at mobile. Uses Jinja's `rejectattr` + list slice pattern (instead of `{% break %}`) to pick the three most recent non-self posts.

### Why it helps

- **Serious long-form reading surface.** Blog posts are the highest-value surface for converting skeptical visitors into trust — finance readers expect editorial typography (not SaaS sans-serif blocks). Fraunces + Geist at this measure and leading reads more like a financial newsletter than a marketing page.
- **Dark-mode reading actually works now.** The prose bug meant every blog post was effectively broken in dark mode — a real quality leak. AdSense resubmission can't proceed with broken content surfaces.
- **Reading-time signal for scanning.** Mono-caps "12 min read" meta helps users decide whether to commit. Small thing, real behavioral impact.
- **Magazine-index listing scales past photo availability.** The 22 more posts on the AdSense critical path don't all need featured images; the listing doesn't pretend they do.
- **Editorial components are optional opt-in.** Pullquote and data-callout only render if the author uses them in markdown. Nothing forces them on every post; they're available when the content benefits.
- **Consistent voice across the redesign.** Mono-caps meta, Fraunces headlines, Geist body, tokenized colors — blog reads like it belongs to the same site as the homepage and advisor directory.

### Known gaps

- Can't verify the full blog in local preview because the site's blog posts live in Airtable (per the documented workflow) and we don't have Airtable creds in this session. Template rendering was verified via a direct Jinja render with a mock post — 13/13 structural checks pass. Real Airtable-driven build will run on Netlify.
- Per-post social-share is preserved (Facebook, X, Pinterest, email). Pinterest is kept since long-form guides can pin well.
- No table of contents or reading-progress bar this milestone (deferred).
- Prose image styles tokenized but no lazy-loading or width-intrinsic defaults added — whatever the markdown emits is what renders.

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
