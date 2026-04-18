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
