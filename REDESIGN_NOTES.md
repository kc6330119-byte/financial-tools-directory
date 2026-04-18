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
