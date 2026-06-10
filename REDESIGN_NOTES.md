# Redesign Decision Log

One line per non-obvious design decision. Append as we go. Format: `YYYY-MM-DD — decision — rationale`.

## 2026-04-18 — Homepage redesign kickoff

- **Branch** — `redesign/homepage-finance-native` — isolates the redesign from `main`; Netlify keeps auto-deploying `main` unchanged during the work.
- **Theme default** — light, with a dark toggle — AdSense reviewers land on desktop light-mode by convention; lower-risk first impression for the resubmission. Semantic gain/loss/amber are identical across themes.
- **AdSense slot positions approved** — Slot A (above-fold between credential legend and featured advisors), Slot B (between specialty matrix and state heatmap), Slot C (between blog preview and editorial block). Ship as empty `<div class="ad-container">` with reserved `min-height` for CLS safety until AdSense resubmission is approved.
- **No site-wide sticky anchor ad** — deferred; don't edit `base.html` for anchor markup this milestone.
- **Market ticker stays homepage-only** — matches current behavior; one Netlify function call per homepage visit, not every page.
- **Skip "Use my location"** — state dropdown is sufficient; avoids geolocation permission prompts that look spammy on first visit.
- **Featured advisors render as a data table** at ≥768 px, reflowing to stacked label:value rows at <768 px — commits to the finance-native direction over card-grid safety.
- **Fonts self-hosted** in `static/fonts/` — zero third-party requests, no FOUT risk tied to CDN availability; budget ~450 KB added to repo.
- **Typography** — Fraunces (display serif) + Geist Sans (body) + Geist Mono (numerics). Variable WOFF2 only. Tabular-nums enforced globally.
- **Primary style layer** — hand-authored CSS in `static/css/custom.css` using CSS custom properties for theme tokens. Tailwind CDN kept in place so the preserved page types (tools, state, advisor, blog, etc.) don't break.
- **`base.html` is in scope** for the homepage milestone — fonts `<link>`s, theme-toggle button in nav, token declarations, footer + newsletter restyle. Other page types will inherit these shell changes, which is accepted.
- **Copy rewrite approved** — homepage microcopy moves to editorial-finance voice (confident, specific, skeptical of hype). Existing JSON-LD schemas and FAQ Q&A text preserved.
- **Logo to WebP, <50 KB** — added to milestone scope at Kevin's request since the header is being restyled; current `static/images/logo.png` is 1.1 MB. Old PNG kept as fallback only if needed, otherwise removed.
- **Performance budget** — **First Contentful Paint < 1.5s on 4G**. This constrains: font loading (preload the two most critical WOFF2s, `font-display: swap`), no blocking JS, hero markup must render without waiting for the market-ticker function, image weight (logo WebP), no large CSS payload (Tailwind CDN is the biggest unknown — measured and revisited if it blocks the budget).
- **Rollback** — branch revert. No data, URL, or schema changes in this milestone, so rollback is a `git revert` of the merge commit.

## 2026-04-18 — Homepage build-out

- **Brand mark** — inline SVG (three ascending bars, gold top bar) replaces the chart emoji in nav + footer. Zero image fetch on the critical path. The optimized `logo.webp` is wired into `og:image` / `twitter:image` for social sharing only.
- **Tickers source** — reused the existing `/.netlify/functions/market-data` endpoint; rewrote the consumer JS to emit compact ticker rows with `is-up` / `is-down` classes. Graceful degrade to "Market data unavailable" when offline or local-previewing (the function only runs on Netlify).
- **State heatmap intensity** computed in Jinja as `count / max_state_count`, clamped 0–1, passed via `style="--intensity: N"` and expressed as an opacity-layer `::before` on each tile. No JavaScript.
- **Specialty counts** required a tiny additive change to `build.py build_homepage()` — a single dict computed from `advisors[].specialties`, passed as `specialty_counts` + a `max_state_count` for the heatmap. No schema changes, no pipeline changes.
- **Tailwind still loaded** in `base.html` because `_advisor_card.html`, `state.html`, `tools.html`, `blog.html` etc. rely on it. Shell elements (`nav.bg-white`, `section.bg-primary-600`, `footer.bg-gray-900`) get overridden by tokenized selectors in `custom.css` so the shell matches the finance-native direction on every page. Body content of non-redesigned pages keeps its current Tailwind styling — expected transitional state until those page types are redesigned in subsequent milestones.
- **FAQ copy + schema preserved verbatim** (`FAQPage` JSON-LD) so the existing SERP-eligible structure stays intact. Only the accordion visual and open-state interaction were rewritten.
- **No emojis in header/nav/footer/specialty chips** — replaced with SVGs, monospace initials, or numeric counts per the finance-native direction.
- **Visual verification** — I cannot take screenshots from this CLI environment (no screen-capture permission). Kevin needs to open `http://localhost:8765/` after running `cd dist && python3 -m http.server 8765`. Golden path to test: light default → toggle → dark → reload (should remember), hero locator dropdown, specialty + state grids reflow across breakpoints, FAQ accordion.

## 2026-04-18 — Milestone 2: directory-page redesign

- **Branch** — `redesign/directory-pages`. Scope: `state.html`, `city.html`, `specialty.html`, `advisor.html`, `_advisor_card.html`, plus component additions in `custom.css` and a theme-change event dispatch in `base.html`. Photo section of `_advisor_card.html` removed per Kevin.
- **Scope includes `city.html` and `specialty.html`** — they share `_advisor_card.html` and follow state.html's structural pattern. Leaving them on Tailwind would create a jarring visual transition on state→city→specialty navigation.
- **Advisor list layout = list rows** (not table, not cards) on state/city/specialty pages. Denser than cards, scales past 50 records without choking like a single table, works at 320 px. One partial (`_advisor_card.html`) renders this row everywhere it's needed, including the "related advisors" block on advisor detail.
- **Leaflet dark-mode tiles via CartoDB** — **Positron** basemap on light, **Dark Matter** on dark. Both are free with attribution ("© OpenStreetMap contributors © CARTO"). Tile URL chosen at map init by reading `document.documentElement.getAttribute('data-theme')`, swapped on theme toggle via a new `smart-investor-theme-change` custom event dispatched from the theme toggle handler. No new CDN dependency beyond the tile URL change.
- **Marker color = `--gold`** (light: `#A67A1A`, dark: `#E8B547`) in both themes. Gold reads well on both map palettes, avoids needing marker-icon rebuilds on theme toggle.
- **Photo removed from `_advisor_card.html`** — most advisory firms don't have photos, and the gradient placeholder reads SaaS-generic. Type-first card is more finance-native and reduces LCP candidate elements on listing pages.
- **Page-head editorial voice** — h1 changes from "Investment Advisors in {{ state.name }}" to "Fiduciary advisors in {{ state.name }}" across state/city/specialty. Meta title and meta description unchanged (preserves SEO/CTR). State editorial paragraph (`state.description`) becomes the lede under the h1.
- **Specialty emoji icons dropped** — replaced with the same `--gold` accent rule used in section eyebrows and the state heatmap legend. Icons read childlike against the finance-native voice; we already dropped them in the homepage specialty matrix.

## 2026-04-18 — Milestone 3: Advisor Compare (new feature)

- **Branch** — `redesign/advisor-compare`. First non-migration milestone — net-new functionality.
- **State model: URL query string is source of truth** on `/compare.html`; `localStorage` mirrors it on listing pages for cross-page persistence of the compare list.
  - **Why:** URLs are shareable and survive refresh/back-button without localStorage dependency. localStorage handles the "I'm still browsing" case where a user adds advisors from 3 different pages before clicking Compare.
  - **How to apply:** new page hydrates columns from `?advisors=slug1,slug2,slug3` first, falls back to localStorage if query empty. Listing-page toggles only touch localStorage; the sticky footer's "Compare →" link is rebuilt from the localStorage list at click time.
- **Max 3 columns.** Four columns on the spec-sheet starts truncating at 1024px; three is the comfortable ceiling that still gives the comparison real utility.
- **Compare page noindexed** (`<meta name="robots" content="noindex, follow">`) — it's a tool, not content. Sitemap excludes it.
- **Data delivery: `/compare-data.json`** emitted at build time with the comparison-relevant fields per advisor (name, slug, city, state, credentials, fee_structure, minimum_investment, specialties, fiduciary, rating, review_count, description, firm_type). Richer than `search-index.json` (which is name/city/state only for nav search), intentionally kept as a separate file so the search index stays small for the nav autocomplete.
- **Toggle button UX** — absolute-positioned `<button>` on advisor row/card (outside the `<a>` wrapper to keep HTML valid), inline chip-style button in the advisor-detail actions row. Plus/minus icon + mono label. Selected state uses `--accent` token, unselected uses `--border` outline.
- **No server, no build-pipeline change beyond `build.py` additive.** Compare.html is rendered as a static shell; hydration is client-side JS. Fits the "everything renders at build time" rule from `stack-conventions.md`.

## 2026-04-18 — Milestone 4: Blog templates + prose tokenization

- **Branch** — `redesign/blog`. Scope: `blog.html` (listing), `post.html` (reading experience), plus an overhaul of the `.prose` styles in `custom.css`.
- **Fixed a real bug:** the `.prose` block in `custom.css` had hardcoded `#1f2937` / `#2563eb` / `#e5e7eb` / `#4b5563` / `#f9fafb` values that didn't theme — every blog post on dark was rendering nearly black-text-on-dark-background. Replaced with `--text` / `--accent` / `--border` / `--text-muted` / `--bg` tokens. This closes one of the Milestone-0 known gaps.
- **Blog listing style = magazine index, not photo cards.** Featured-image hit rate is near-zero in the content we've written so far; placeholder gradients read SaaS-generic. Stacked rows with divider lines, mono-caps meta (category · reading time · date), Fraunces title, excerpt in Geist — editorial-finance-native and more honest about what the listing actually contains.
- **Post reading experience = editorial feel.** Fraunces for h1 + section headings, Geist for body at 1.0625 rem with 1.75 line-height, ~66ch measure. Prose gets new `.pullquote` and `.data-callout` component patterns for editorial flourishes (optional per post via markdown class hints).
- **Reading time computed in Jinja** via the built-in `wordcount` filter — no `build.py` change needed. `(content | striptags | wordcount // 225) + 1` min read, clamped minimum 1.
- **Sticky share + "Back to blog" footer** retained but tokenized. Pinterest share button kept (blog posts may get pinned; listing retention is niche but real).
- **Disclaimer box** kept with tokenized `--warn`-tinted styling. Still says "informational only, not financial advice" — required by the YMYL posture.
- **Related posts as card row** (not grid of 3 photo cards) — same visual language as the homepage blog preview, ensures voice consistency.
- **Category filter on blog.html** stays client-side, but filter chips are rewritten in the tokenized chip pattern used elsewhere. URL hash deep-linking from homepage category tiles preserved.

## 2026-04-18 — Milestone 5: Tools hub + category + tool detail

- **Branch** — `redesign/tools`. Scope: `tools.html` (hub), `category.html` (single-category listing), `tool.html` (detail).
- **`.ad-container` placements preserved.** tools.html (2 slots), category.html (1 slot), tool.html (3 slots: after header, sidebar, before related). Each wrapped with our `.ad-slot ad-slot--leaderboard` / `.ad-slot ad-slot--in-content` CLS-safe containers so the empty `<div class="ad-container">` still reserves vertical space consistent with the finance-native direction. Slot IDs unchanged (none were ever defined — pre-resubmission, same posture as the rest of the site).
- **Tools get their own list-row pattern, `.tool-card`** — conceptually parallel to `.advisor-row` but with logo/fallback at left, `.bool-chip` for API / Mobile flags (a mono-caps pill with `--gain`-tint when true, `--text-faint` outline when false), rating + pricing in mono, and a right-aligned CTA to the detail page and external site.
- **Tool detail page head** — `.tool-head` extends the `.page-head` pattern with a logo block and inline rating/pricing/category tags. Uses the existing `.btn btn--primary` / `.btn btn--ghost` pair for the "Visit site" + "Learn more" actions.
- **Features rendered as a typographic checklist** — clean single-column list with tokenized check glyph. No decorative backgrounds, just the data.
- **Sidebar spec-sheet** reuses the `.spec-sheet` pattern from advisor detail. Quick-info `<dl>` items: pricing, price range, API availability (gain-tinted when Yes), mobile app, data sources. Consistent voice with the advisor spec-sheet.
- **"Other categories" chip row** at the foot of category.html reuses the `.specialty-chip-row` component from the specialty page. Same design, different content slot.
- **Related tools on the detail page** render as a compact 4-column card row at desktop, stack on mobile. Shares the `.related-post` pattern from the blog post template.

## 2026-04-18 — Mailchimp newsletter integration

- **Branch** — `redesign/mailchimp-newsletter`. Scope: `base.html` only (newsletter form + submit JS).
- **Migrated from Netlify Forms to Mailchimp.** The site-wide newsletter now posts directly to `https://doggroomerlocator.us12.list-manage.com/subscribe/post?u=…&id=…&f_id=…`. Contact form on `contact.html` still uses Netlify Forms — only the newsletter changed.
- **Shared Mailchimp audience across all five of Kevin's directory sites** (confirmed with Kevin: one audience, tagged by source). Added a hidden `<input type="hidden" name="SITE" value="smart-investor">` so Mailchimp can segment by source once a `SITE` merge field is added to the audience. Safe no-op until the field is configured — Mailchimp silently drops unknown fields.
- **`target="_blank"` + native form submit**, not AJAX/JSONP. Simplest reliable approach: browser submits to Mailchimp, Mailchimp's confirmation page opens in a new tab, our side optimistically swaps to "Subscribed. Check your inbox to confirm." via a 50 ms setTimeout. Double opt-in is Mailchimp's default for the list so the inbox-confirmation language stays accurate.
- **Did not import** Mailchimp's `classic-061523.css`, jQuery, `mc-validate.js`, or the ~400-line SMS-phone country dropdown script. Our existing tokenized form styling survives intact; bytes added to the critical path: zero.
- **Bot honeypot preserved verbatim** (`name="b_21343a587fbb950d8b649ee6d_970ba04869"`) — Mailchimp expects that exact list-specific honeypot name. The field lives inside a `position: absolute; left: -5000px;` div with `aria-hidden="true"` and `tabindex="-1"` so assistive tech and keyboard users skip it.
- **Submit-button `name="subscribe" value="Subscribe"`** is preserved from the Mailchimp embed — their server expects it.
- **`rel="noopener"`** added to the form element alongside `target="_blank"` for the usual new-tab security posture. The `novalidate` attribute is intentionally **not** added — we keep the browser's HTML5 email validation on.

## 2026-04-18 — Milestone 6: Static pages + copy pivot

- **Branch** — `redesign/static-pages`. Scope: `about.html`, `contact.html`, `privacy.html`, `terms.html`, `success.html`.
- **Dual-purpose milestone.** Every page gets the finance-native style refresh **and** a copy rewrite dropping the obsolete "Financial Tools Directory" framing. Closes a Milestone-0 known gap explicitly flagged on the AdSense-resubmission critical path (`ADSENSE_RESUBMISSION_PLAN.md` Action 4).
- **Voice consistency.** All five pages move to the same editorial-finance register the rest of the site uses — confident, numeric where appropriate, skeptical of hype, specific. No "we'd love to hear from you!" SaaS copy.
- **Contact form kept on Netlify Forms** — do not change the form attributes (`data-netlify="true"`, `netlify-honeypot="bot-field"`, form-name hidden). Only the visual tokens change. This is where Kevin receives contact inquiries.
- **Subject dropdown options updated** from tool-centric ("Submit a Tool", "Report an Issue about a tool") to advisor-centric ("Suggest an advisor", "Report incorrect info", "Business inquiry"). Keeps the directory-pivot narrative consistent end-to-end.
- **Privacy policy updated** to reflect the current stack: adds Mailchimp (newsletter provider) and Airtable (CMS for advisor and blog content — stored separately from user data), updates the "Information We Collect" section to describe how advisor data is sourced from public records (BrokerCheck / SEC IAPD), adds a removal-request pathway for listed advisors.
- **Terms of service updated** to drop the "we list tools" primary framing (tools now a sub-section), reframe affiliate disclosure around the tools section only, add a clear "we are not a registered investment advisor" and "directory entries are not endorsements" clause — required for the YMYL posture.
- **Success page** tokenized and the response-time copy updated to "within one business day" (tighter than the previous "2-3 business days") to signal a small, attentive operation.
- **New CSS component: `.form-field` / `.form-label` / `.form-input` / `.form-textarea` / `.form-select`** — tokenized form controls that also benefit any future form work (e.g., the "submit an advisor" form in the AdSense plan). First use is the contact form; these replace the Tailwind `border-gray-300 focus:ring-blue-500` utility stack with `--border` / `--accent` tokens.
- **Static-page layout.** Privacy and Terms use a tight `.prose` column (65ch) on a normal `.wrap`. About and Contact use richer per-section composition with `.detail-card` stacks so the content breathes.

## 2026-04-18 — Milestone 7: Calculator suite foundation + first 3 calculators

- **Branch** — `redesign/calculators-m7`. First three of six planned calculators plus the shared infrastructure. Second three (SS, RMD, 4% Rule) ship in Milestone 8.
- **Nav placement: top-level** — "Calculators" sits next to Tools and Blog in `base.html`. Pillar, not a sub-feature.
- **URL pattern follows existing conventions** — `/calculators.html` (plural hub) + `/calculator/<slug>.html` (singular per-item folder). Same shape as tools/tool, advisor/state, blog/post.
- **One Jinja template per calculator** (`calc_compound_interest.html`, `calc_retirement.html`, `calc_savings_goal.html`). Different math, different input shapes — reaching for a shared base gives inheritance hell for marginal DRY benefit.
- **Config: `CALCULATORS` list in `config.py`** — slug, name, short-question, description, tagline, template filename, category. Drives both the hub and the per-calc build loop.
- **Live calculation, no "Calculate" button.** All outputs recompute on every `input`/`change` event. Substantially better UX than the SEC example.
- **Progressive: the form and disclaimer render at build time** so the page indexes with meaningful content. JS enhances with live results, inline SVG charts, and formatted outputs. No JS frameworks; every calculator is ~100–150 lines of vanilla JS inline in its template.
- **SVG line chart built inline** — no Chart.js dependency. Path generated from the computed year-by-year balance series; ~60 lines of JS per calculator. Axis ticks, area fill under the line, last-point dot.
- **Closing CTA on every calculator** — *"These are estimates. A fiduciary advisor can model this against your actual tax situation, Social Security timing, and risk tolerance."* → button to the advisor directory homepage. Natural conversion funnel.
- **Math decisions to flag:**
  - Compound Interest: supports negative monthly contribution (withdrawal) and configurable compounding frequency (monthly / quarterly / annually). Displays nominal balance — inflation adjustment is a separate concern shown in the retirement calc.
  - Retirement: uses the 25× annual expenses rule as the target, adjusted for inflation between today and retirement. Deliberately conservative. Surplus/gap shown against the projected nest egg.
  - Savings Goal: solves PMT given target, current savings, time horizon, expected return. Annuity-due math with monthly compounding (i.e., contributions at start of period — matches most brokerages' auto-invest).
- **YMYL posture preserved.** Every calculator page has a tokenized `.disclaimer-box` warning the results are estimates, not financial advice, and that real planning involves tax / SS / risk considerations a calculator can't capture.
- **Sitemap: calculator pages included** so they're discoverable. Calculator URLs are indexable (not noindex).

## 2026-05-29 — AdSense "Low Value Content" remediation: fact-grounded descriptions + per-listing gate

- **Root cause (settled, not re-litigated):** listing descriptions were spun/templated synthetic content (`enrich_descriptions.py`: MD5-of-slug → bit-shifted sentence pools) — Google's March-2024 "scaled content abuse." Fix is *original per-page value*, not more HTML hygiene or a bigger spintax bank.
- **Fact-grounded generator (`generate_fact_descriptions.py`)** replaces the spinner. Each description is composed only from clauses that are *true for that specific firm* (firm type, year established, fiduciary/SEC status, services, specialties [deduped vs services], credentials, fee basis, minimum investment, non-English languages, Outscraper `about` attributes, hours, rating/reviews as prose). Variation comes from real differing facts, never synonym shuffling.
  - **Why:** that's the only thing that removes the scaled-content signal — honest framing is "better odds, not a guarantee." Phase 2 (website-crawl enrichment) is what adds value beyond the GBP, deferred until Phase 1 ships.
  - **How to apply:** dry-run by default; `--apply` required to write; backs up existing descriptions to `data/description_backup_<ts>.json` keyed by record id before the first write; **only updates existing records, never inserts**.
- **Per-listing indexing gate in `build.py`** (`description_is_indexable` + `advisor_is_indexable`): a listing indexes only if it has contact info **and** a description ≥ `MIN_DESCRIPTION_LENGTH` that isn't a JSON blob, isn't scraped regulatory boilerplate (`_BOILERPLATE_RE`), and has ≥ 20 distinct words. Sitemap emits indexed advisor slugs only.
- **Gate = 250 chars** (`config.MIN_DESCRIPTION_LENGTH`) — Kevin's call. **No length padding:** descriptions that land under 250 stay short and get noindexed on purpose, deliberately shrinking the synthetic indexed surface to genuinely fact-rich pages.
- **AdSense suppressed on noindex pages** (`base.html`: loader wrapped in `{% if not noindex %}`) — Kevin's call. No ads on thin/noindexed content; reduces the "ads on low-value pages" signal a reviewer reacts to.
- **Removed scraped `aggregateRating` JSON-LD** from `advisor.html` — emitting review structured data from scraped ratings is a structured-data-spam manual-action risk. Ratings still appear as prose in the body, never as markup.
- **`enrich_descriptions.py` retired** — docstring DEPRECATED banner + `main()` hard-stops unless `--force-deprecated-spinner` is passed, so it can't silently re-spin and undo the fix. `build.py` imports neither generator (it gates the stored Airtable field).
- **Protected-URLs mechanism** (`extract_protected_urls.py` → `protected_urls.txt`, read by `build.py:_load_protected_slugs`): grandfathers pages already earning Search traffic past the gate so a ranking page can't get noindexed on the next build. Reads a GSC "Pages" export; default rule clicks ≥ 1. **Fail-open** everywhere — missing export/file = no protections = gate applies to everything (the correct posture for a site with little current traffic). `protected_urls.txt` should be **committed** when generated (Netlify build input); `FACT_DESCRIPTIONS_SAMPLE.md` is a regenerated review artifact and is gitignored.
- **Dry-run projection (pre-apply):** 96.6% Outscraper `about` join coverage; composed lengths min 65 / median 277 / max 622; **64.4% would index (3099), 35.6% noindex (1711)** at the 250 gate. Building from the *current spun* field instead yields only 1727 indexed / 3083 noindexed — i.e. applying Phase 1 *replaces* 1727 spun-indexed pages with ~3099 fact-grounded ones rather than merely trimming.
- **Rollback:** descriptions restore from the timestamped backup JSON; gate/template/schema changes revert with the commit. `--apply` (the 4810-record Airtable write) is gated on Kevin's explicit go; Kevin drives the git push / Netlify deploy.

## 2026-05-29 — Phase 2: website-crawl enrichment

- **Branch** — `seo/phase2-website-enrichment`. Builds on Phase 1: same `Description` field, same 250-char `build.py` gate, same write discipline (dry-run default, `--apply` backs up first, **existing records only, never inserts**). New artifact: `website_descriptions.py`.
- **What Phase 2 adds** — for each advisor with a website, crawl the firm's *own* site (homepage + ≤2 about/services pages via trafilatura main-content extraction), have Claude Haiku extract firm-specific facts and write an **original** 2–4 sentence description, and fall back to the Phase 1 GBP description whenever the site yields nothing usable. Phase 1 removed the spam signal; Phase 2 adds value beyond the Google Business Profile — the distinctiveness gap called out in Milestone 11's known-gaps.
- **Model: Claude Haiku 4.5** (`claude-haiku-4-5-20251001`), `max_tokens=600`, strict JSON `{sufficient, description}`.
  - **Why:** fact extraction + short composition doesn't need a frontier model, and it has to run across thousands of sites — Haiku keeps the full run in single-digit dollars (pilot: ~$0.07 / 100 advisors).
- **Franchise / shared-host guard — route to GBP fallback, never to the LLM.** A host shared by ≥ `SHARED_HOST_MIN` (8) advisors is treated as corporate/shared and served the Phase 1 fallback (`gbp-shared-host`); the crawler+LLM never touch it.
  - **Why:** empirically proven duplicate content — two `advisor.ml.com` pages scored a **6-gram Jaccard of 1.0** (100% identical Merrill boilerplate). Crawling shared hosts would *manufacture* near-duplicate descriptions, the exact signal Phase 1 set out to kill. 23 hosts qualify (ml.com 209, raymondjames.com 182, northwesternmutual.com 179, wealthenhancement.com 115, …).
  - **How to apply:** the guard matches **any** URL on a shared host, not just bare-root paths — an advisor-specific deep link on a franchise domain still routes to fallback.
- **Originality guard — `MAX_VERBATIM_WORDS = 10`.** A website-derived description that copies ≥ 10 consecutive words from the crawled source text is rejected to fallback (`gbp-verbatim`). Measured via `difflib.SequenceMatcher.find_longest_match` on word lists.
  - **Why:** a measurable no-verbatim-copying guarantee for YMYL/copyright safety. Short branded labels (8–9 words, e.g. "On Track, Off Track, or Ahead of Track") pass; copied marketing sentences don't. Max shipped verbatim run in the pilot was 9 words.
- **YMYL prompt discipline** — extract only firm-specific facts (services, fiduciary status, fee model, CFP/CFA/CPA/ChFC credentials, SEC/state registration, founding year, principals, niches, minimum); write original prose; **never** invent facts; **never** promise returns/performance/outcomes/tax savings/"peace of mind"; ban marketing filler ("nestled", "boasting", "dedicated team", "comprehensive suite", "trusted partner", "tailored solutions"); no "top-rated/leading/premier/award-winning" unless present in the data. `sufficient=false` only for nav/cookie/error/parked pages.
- **Polite, robots-aware crawling** — per-host `robots.txt` honored (cached, **fail-open**), a UA that identifies the bot + links the about page, `CRAWL_DELAY` 0.5s between same-host hits, and `socket.setdefaulttimeout(8)` to bound `robotparser.read()` hangs across thousands of hosts. A social/aggregator skip-list (Facebook, LinkedIn, Yelp, BrokerCheck, SmartAsset, …) keeps the crawl on the firm's own site, not its profiles.
- **Caching** — crawl HTML and LLM responses cached MD5-keyed under `data/site_cache/` so re-runs are cheap and idempotent. It's an offline working artifact, **gitignored, not a Netlify build input** (the build still reads only the stored Airtable field).
- **Cost metering** — each LLM call captures `usage.input_tokens`/`output_tokens`; the run prints actual spend + a full-run projection. Pilot (100 advisors, 34 LLM calls): $0.0697; projected full-run upper bound ~$7.63 (realistically lower — shared-host and thin-site records skip the LLM).
- **Rollback:** identical to Phase 1 — descriptions restore from the timestamped `data/description_backup_<ts>.json`; `website_descriptions.py` is additive (build reads neither generator). `--apply` is gated on Kevin's explicit go; Kevin drives the git push / Netlify deploy.

## 2026-06-09 — Pre-resubmission audit fixes

- **Branch** — `fix/adsense-audit-findings`. Five fixes from the full-corpus audit (Dog Groomer rejection as benchmark); audit details in `ADSENSE_RESUBMISSION_PLAN.md` 2026-06-09 snapshot.
- **`.env` override removed** — `AIRTABLE_TABLE_NAME=Advisors` made local builds render all advisors as `/tool/` pages; root cause of the 2026-05-29 tools-removal confusion. Removal verified safe (`validate_listings.py` self-defaults to "Advisors"; importer doesn't read the var). **Rollback:** re-add the line to `.env` (not in git).
- **Tool-fetch sanity guard** — `fetch_tools_from_airtable` raises `SystemExit` (escapes the fallback `except Exception`) if >50% of sampled records look advisor-shaped. Fail-loud beats fail-into-sample-data: a polluted/misdirected table now kills the build instead of shipping a duplicate directory.
- **Tool gate parity** — `build_tool_pages` applies `description_is_indexable`, returns indexed slugs; sitemap emits indexed tools only (same None=all/[]=none semantics as advisors). All 35 current tools pass.
- **Near-dup rule = 6-gram Jaccard > 0.5 within same-firm-name groups** — survivor preference: protected > longest description > slug (deterministic). 615 noindexed (Merrill 209→14 indexed); indexed advisors 4,099→3,607. Magnitude is deliberate: one canonical page per shared corporate blurb. Threshold and survivor policy live in `_near_duplicate_slugs`.
- **Methodology page** — `/methodology.html`, indexed, in sitemap, footer link site-wide + about-page link; copy is fact-grounded against the real pipeline (says "roughly one in four" listings noindexed, matching 1,203/4,810). Pretty URL via netlify.toml 200 rewrite.
- **Sitemap dedup** — `urls = list(dict.fromkeys(urls))` before write; order-preserving.
- **Flagged, not changed** — about.html says firms are "added from public regulatory sources"; actual source is GBP/Outscraper. Kevin's copy call.

## 2026-06-07 — Block Singapore bot traffic (Netlify Edge Function)

- **Branch** — `infra/block-sg-bot`. New file `netlify/edge-functions/block-bot-traffic.js` + an `[[edge_functions]] path = "/*"` block in `netlify.toml`. First edge function on the site (the existing `netlify/functions/market-data.js` is a regular serverless function).
- **Why** — GA4 showed a bot flood: in 2026-05-10 → 06-06, **1,002 of 1,064 users (94%) were from Singapore** with a 0.2% engagement rate, **0.022s** average engagement time, 0 key events, $0 revenue — spiking ~976 new users on a single day (Jun 5). A JS-executing bot polluting analytics, not real traffic. Audience is US-only, so a country block has ~0 collateral.
- **Mechanism** — the edge function reads `context.geo.country.code` and returns **403** for any blocked country before the request reaches the page (so the bot never loads the GA snippet). Default blocklist `["SG"]`.
- **Crawler safety** — a user-agent allowlist (Googlebot, Mediapartners-Google/AdSense, AdsBot, Bingbot, …) is checked **first**, so legit Search/ad crawlers are never blocked even from a blocked country. Matters because Google runs infra in Singapore.
- **Ops controls (no redeploy needed)** — env `EDGE_BLOCK_ENABLED=false` kills the block instantly from the Netlify UI; env `EDGE_BLOCKED_COUNTRIES` (comma-separated ISO codes, default `SG`) changes the list. Default-on: with both env vars unset, it blocks SG out of the box.
- **Known limits** — (1) edge geo is IP-based, so a bot that switches to a US/residential proxy would dodge it; add behavioral signals (UA/rate) then. (2) Does **not** retroactively clean existing GA history — pair with a GA4 country data-filter for that (no code).
- **Rollback** — `git revert` the commit (removes the function + the `netlify.toml` block), or just set `EDGE_BLOCK_ENABLED=false`. Kevin drives the git push / Netlify deploy.
