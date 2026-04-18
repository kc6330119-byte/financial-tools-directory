# Redesign Changelog

Narrative log of the Smart Investor redesign work. **Most recent milestone at the top.** Each entry captures what shipped, what it changed for users / Google / the business, and what's still open.

This file is the "release notes" view of the redesign. For the terse one-line-per-decision log, see [`REDESIGN_NOTES.md`](REDESIGN_NOTES.md). For the original homepage plan, see [`REDESIGN_PLAN.md`](REDESIGN_PLAN.md). For the AdSense-resubmission critical path, see [`ADSENSE_RESUBMISSION_PLAN.md`](ADSENSE_RESUBMISSION_PLAN.md).

---

## Side-milestone — Removed fabricated tool ratings (2026-04-18)

**Branch:** `fix/remove-fabricated-tool-ratings`
**Type:** Integrity fix — not a design or feature change

### What changed

Kevin flagged that the star ratings and review counts displayed on the tool directory (TradingView 4.8/892 reviews, Alpha Vantage 4.5/127, Yahoo Finance 4.2/456, etc.) were fabricated placeholder data, not real user reviews. Removed all display and all structured-data emission of those values:

- **`tool.html` SoftwareApplication schema:** `aggregateRating` block removed from the JSON-LD. This was the highest-severity item — fabricated `aggregateRating` markup is explicitly prohibited by Google's [structured data policy](https://developers.google.com/search/docs/appearance/structured-data/sd-policies) and triggers manual-action penalties in Search Console.
- **`tool.html` header:** rating + review-count display removed from the tool-meta-line. Pricing model, price range, and Featured badge remain.
- **`tool.html` related-tools block:** star rating removed; the meta line now shows pricing model and primary category instead.
- **`tools.html` and `category.html` tool-cards:** star + review-count display removed from the row-top-meta. Featured badge remains.
- **Homepage tool-row:** star rating removed; pricing model stays as the single numeric meta.

### What did NOT change

- **Advisor ratings and review counts are untouched.** Those come from Outscraper pulling real Google Maps data — legitimate, unlike the hand-authored tool values. `advisor.html` still emits `aggregateRating` in its `FinancialService` schema.
- **Data model preserved.** The `rating` and `review_count` fields remain in `config.py` sample data, Airtable, and build-time dicts. Templates just don't render them. If Kevin ever wants to add a real editorial scoring system (1–5 with disclosed criteria), the field scaffolding is ready.
- **Featured status, category tags, API/Mobile bool-chips, pricing, features, target audience** — all stay.

### Why it matters

- **Google manual-action risk.** Schema-level fake reviews are one of the specific things that get sites penalized. Shipped before Google first-crawled the new schema, so there's no record of the fabricated markup.
- **AdSense deceptive-content risk.** Review-style pages with fabricated ratings are the kind of thing AdSense denies for in the YMYL-finance category. Critical to clean up pre-resubmission.
- **Editorial consistency.** The rest of the site is built around a "no paid placements, disclosure-driven, skeptical-of-hype" posture. Fake ratings contradicted that directly.

### Known gaps

- Tool directory has no social proof left. If Kevin wants that back, an honest path is: editorial ratings (our own 1–5 with a published rubric like "data quality / pricing transparency / UX / API quality") applied consistently by a human. That's a real content project, not a placeholder.

---

## Side-milestone — Google Search Console verification (2026-04-18)

**Branch:** `chore/gsc-verification`
**Commit:** `3a5bbeb`
**Type:** Infrastructure chore — not a design or content milestone

### What changed

- Registered a **URL Prefix** property in Google Search Console for `https://smart-investor-financial-tools.com/` and verified ownership via the **HTML file** method (not DNS TXT — chosen for consistency with Kevin's other four directory sites and because it's faster than waiting on DNS propagation).
- Token file `google981a97c130472a18.html` lives at the project root. It's a one-liner: `google-site-verification: google981a97c130472a18.html`.
- `build.py` gets a new `copy_verification_files()` helper that copies any root-level `google*.html` or `BingSiteAuth.xml` into `dist/` on every build. Generic pattern so adding future search-engine verifications is "drop the file at the project root and rebuild."
- Sitemap submitted in Search Console immediately after verification. Google starts crawling on its own cadence from there; manual "Request indexing" batch ran on the top 10 high-value pages.

### Why it helps

- **Closes AdSense-resubmission Action 6** (Verify Google Search Console + submit sitemap). That was blocking post-resubmission measurement of whether the Outscraper imports and blog posts are actually getting indexed.
- **Structured-data validation pipeline.** Over the next 1–2 weeks the Enhancements section in GSC will populate with BreadcrumbList / Article / FinancialService / SoftwareApplication / FAQPage status. If anything's malformed in what Milestone 7b shipped, GSC will flag it by schema type with the affected URLs.
- **Core Web Vitals data.** Once the site has real Chrome user traffic, GSC pulls CrUX data and shows LCP / INP / CLS for the page. That's the ground-truth view of the performance budget we targeted during the redesign (FCP < 1.5 s on 4G), versus the synthetic Lighthouse numbers.
- **Verification is file-based and survives rebuilds.** Because the build copies the token file on every run, `setup_output_directory`'s wipe of `dist/` can't break verification. Previously a manual-upload approach would be brittle.

### Known gaps

- Yandex, Pinterest, and other verification providers aren't set up yet — only Google and Bing. The `copy_verification_files()` helper and the "Site verification" meta-tag block in `base.html` are ready for additions when/if needed.

### Follow-up adds (same day)

- **Bing Webmaster Tools verified via HTML meta tag** (`msvalidate.01`). The `<meta>` lives in the "Site verification" comment block in `base.html` so it lands on every rendered page. Bing will accept verification from any crawlable URL, so template-inherited placement is the right approach.
- **Google Search Console HTML-tag backup verification added** (`google-site-verification`). Now two active ownership methods for Google: the HTML file at the project root (primary) and the meta tag site-wide (backup). Google considers the property verified as long as *any* active method holds — losing one no longer un-verifies the property.
- Both tokens sit side-by-side in `base.html`. Future additions (Yandex, Pinterest, Ahrefs, etc.) land in the same block with their own `<meta>` line.

---

## Milestone 7b — SEO hardening (2026-04-18)

**Branch:** `redesign/seo-hardening-m7b`
**Commits:** single scoped commit
**Files touched:** `build.py`, `templates/base.html`, new `templates/_breadcrumb_schema.html` macro, plus `extra_head` additions across 15 templates
**Type:** Technical-SEO hardening pass — not a design milestone

### What changed

- **Fixed sitemap emitting noindex URLs.** `build.py`'s `build_sitemap` used `if indexed_states:` / `if indexed_cities:` truthy checks that silently treated "empty list" the same as "caller didn't filter at all," falling back to listing every state/city even when most were noindexed. Changed to `is not None` so an explicit empty list is honored. With sample data, five Texas/Illinois/Florida cities (1 advisor each, below the 3-advisor threshold) are no longer polluting the sitemap.
- **`success.html` now noindex.** Added `"noindex": True` to its `STATIC_PAGES` entry — same pattern already used for `compare.html`. The contact-form thank-you page has no value for search to surface.
- **New universal schema on every page.** `base.html` now emits an `@graph` JSON-LD block with both `WebSite` and `Organization` types, cross-referenced via `@id`. Organization schema is site-wide E-E-A-T signal that previously wasn't anywhere.
- **BreadcrumbList schema site-wide.** New `_breadcrumb_schema.html` macro (imported and called from each template with breadcrumbs). Emits proper `ListItem` elements with `position` and `item` URL. Landed on 15 template types — state, city, advisor, specialty, all 6 calculators, tools/category/tool detail, blog/post, about/contact/privacy/terms, compare. Google shows breadcrumbs in SERPs when this is present; they're also AI-Overview signal.
- **Article schema on `post.html`.** Proper `headline`, `datePublished`, `author`, `publisher` (with logo ImageObject), `image`, `mainEntityOfPage`. Required for Google News / Discover candidacy and AI Overview eligibility for editorial content.
- **SoftwareApplication schema on `tool.html`.** Proper `applicationCategory: "FinanceApplication"`, `operatingSystem: "Web"`, conditional `offers` for Free/Freemium tools, `aggregateRating` when rating + review count are present.
- **Specialty chips on advisor detail now link to specialty pages.** Internal-link flow from high-intent advisor pages into specialty-hub pages, which were previously reached only via nav or sidebar. CSS updated with hover states on `a.chip` (border and text shift to accent on hover).
- **Descriptive alt text on tool logos.** Changed `alt=""` to `alt="{{ tool.name }} logo"` in `tools.html`, `category.html`, `index.html` (homepage tools-row), and `tool.html` (related-tools block). Zero empty-alt images remain on the listing surfaces per grep audit.

### Why it helps

- **Rich SERP results.** BreadcrumbList → breadcrumbs in search results instead of raw URLs. Article on blog posts → "By Author · Date" byline treatment. SoftwareApplication on tools → star rating and app-card rich result eligibility.
- **AI Overview candidacy.** Structured data is now one of the strongest inputs into whether Google Gemini / SGE pulls a page into its AI Overview response. Every major content type has proper schema.
- **Clean Search Console.** Noindexed URLs in the sitemap previously would have surfaced in Search Console as "Excluded → Submitted URL not selected as canonical" or similar warnings. Removed.
- **Internal-link juice toward specialty pages.** Advisor detail pages are the highest-authority type we generate (most backlinks, most traffic once AdSense is approved). Linking specialty chips passes that juice into specialty hub pages that otherwise are only reachable from nav.
- **Accessibility + image search.** Named alt text on tool logos helps screen readers and Google Image Search rank tool identities correctly.
- **Macro pattern is reusable.** Any future template with breadcrumbs (when we add them) gets a 5-line import + 3-line call, with no duplication of the JSON-LD boilerplate.

### Known gaps

- No `WebApplication` / `FAQPage` schema on calculator pages yet. Calculators could emit `WebApplication` with their description and benefit — deferred, lower priority than getting the universal schema in place.
- Hub page titles (`blog.html`, `tools.html`, `about.html`) are still shorter than ideal. Captured in the audit as a quick win; one-line edits in `build.py STATIC_PAGES` / page heads. Deferred to a later polish pass.
- About page still lacks a founder bio (already flagged in the AdSense resubmission plan).
- Homepage tool-row `loading="lazy"` is applied but the 4 images are above-the-fold on some viewports; consider removing `loading="lazy"` from those specifically or using `fetchpriority="high"` if they end up in the LCP candidate set.

---

## Milestone 8 — Three more calculators: Social Security, RMD, Safe Withdrawal (2026-04-18)

**Branch:** `redesign/calculators-m8`
**Commits:** single scoped commit (config + three templates + changelog)
**Calculators shipped:** Social Security Claim Age, Required Minimum Distribution, Safe Withdrawal Rate (4% Rule)
**Completes:** the calculator suite started in Milestone 7. Six total.

### What changed

- **`/calculator/social-security.html`** — claim-age comparison between 62, FRA (67), and 70. Uses the post-1960 birth cohort benefit-adjustment factors (0.70 / 1.00 / 1.24 at the three benchmark ages, interpolated in between). Results show monthly benefit at the chosen age, all three benchmark ages side-by-side, and a three-line chart of cumulative lifetime benefit that visually surfaces the break-even points (typically ~78 for 62-vs-FRA, ~83 for FRA-vs-70). CTA goes directly to the specialty/social-security page instead of the generic homepage, since this calculator converts specifically.
- **`/calculator/rmd.html`** — Required Minimum Distribution using the IRS Uniform Lifetime Table (ages 73–110 embedded inline). Shows current-year RMD, distribution-period factor, monthly equivalent, percentage of balance. Multi-year chart projects RMDs through age 95 given an assumed return, so the user can see how the percentage climbs each year as the table factor shrinks. Editorial explains the 25% SECURE 2.0 penalty and the qualified-charitable-distribution workaround — both commonly under-used by retirees.
- **`/calculator/safe-withdrawal.html`** — classic 4% rule (Bengen 1994) with adjustable withdrawal rate, real return, and horizon. Simulates year-by-year balance, reports whether the portfolio survives the horizon, and if not, in what year it depletes. Gold dashed horizon line on the chart. Gain-tinted when surplus, loss-tinted when depleted. CTA goes to the retirement-planning specialty page.
- **Multi-line chart helper** added inline on the Social Security calculator — extends the existing single-line SVG pattern to render three stroked paths with a color legend. Reusable pattern for any future multi-scenario comparison (Roth conversion breakeven, pension-vs-lump-sum, etc.).
- **Hub** (`/calculators.html`) now displays all 6 calculators in its grid. Sitemap updated automatically (calculator URLs are emitted from `config.CALCULATORS`).

### Why it helps

- **Highest-intent calculator in the set.** "Social Security calculator" and "when should I claim Social Security" are enormous-volume queries from an audience with specific buying intent (pre-retirement, affluent enough to care, often in the window where an advisor fee pays for itself). The calculator directly demonstrates the value of the Social Security specialist page we already maintain.
- **RMD is the most niche but most lucrative.** Anyone searching "RMD calculator" is 72+ and has real money in tax-deferred accounts. The conversion-to-advisor rate on that audience is meaningfully higher than general retirement traffic.
- **4% Rule rounds out the distribution-phase suite.** Together with Social Security (income) and RMD (forced distributions), retirees now have three connected tools on the site covering the three main moving parts of retirement income.
- **Editorial depth matters more here than on the accumulation calculators.** Distribution-phase planning is where people actually get hurt by bad advice (sequence-of-returns risk, forced selling in drawdowns, missed RMDs). Each calculator's explain section acknowledges what the math can't capture and points to the specialists — strong YMYL signal.
- **Reuses everything from Milestone 7.** CSS components, SVG chart helpers, form controls, page layout, disclaimer box, CTA pattern, "other calculators" chip row. ~60% less code per calculator than M7 took.

### Known gaps

- Social Security calc assumes FRA = 67. For anyone born before 1960 (roughly 65+ today), FRA is younger (65 to 66-and-10-months); the benefit-factor lookup needs adjustment. Most near-term users will be post-1960 so the current simplification is fine, but a birth-year selector would make the tool bulletproof.
- RMD table is for single owners whose spouse is not more than 10 years younger. The Joint Life and Last Survivor Expectancy Table isn't modeled. Disclaimer box calls this out.
- Safe Withdrawal uses constant-rate arithmetic, not Monte Carlo. A real retirement plan uses 10,000+ simulations with varying return sequences; that's beyond what vanilla JS should attempt in a browser. Disclaimer notes this.
- None of the three calculators model taxes directly. Taxable vs. Roth vs. traditional withdrawal ordering dramatically affects real outcomes; it'd need a much more sophisticated UI. Out of scope for v1.

---

## Milestone 7 — Calculator suite foundation + first 3 calculators (2026-04-18)

**Branch:** `redesign/calculators-m7`
**Commits:** three scoped commits
**New top-level section:** `/calculators.html` + `/calculator/<slug>.html`
**Calculators shipped:** Compound Interest, Retirement, Savings Goal
**Coming in Milestone 8:** Social Security, RMD, 4% Rule / Safe Withdrawal

### What changed

- **New top-level nav item: Calculators.** Added to the desktop nav (between Tools and Blog) and the mobile menu. Calculator list also populates the "Calculators" column in the footer on every page.
- **Hub at `/calculators.html`** — page head with confident positioning ("Answer the numeric questions that drive the planning questions"), three-column grid of calculator cards (category + name + short question as the Fraunces headline + description + open-link arrow), editorial intro explaining why these specific calculators.
- **Three calculator pages**, each with the same shape: breadcrumb + page-head → two-column `.calc-shell` (form + live results) → SVG line chart of balance-over-time → editorial explanation of the math and its limits → closing advisor CTA → other-calculators chip row → YMYL disclaimer box.
- **Live calculation, no "Calculate" button** — every input and select fires `input`/`change` handlers that immediately recompute results and re-render the chart. Dramatically better UX than the SEC's step-based form.
- **Inline SVG charts** — ~60 lines of vanilla JS per calculator, no library. Axis grid, y-axis money labels (auto-formatted to `$K` / `$M`), area fill, line path, endpoint dot, optional dashed "target" line where applicable (retirement target nest egg, savings goal).
- **Big Fraunces figures for the result headline** using the `opsz 144, SOFT 20` variable-font axes. Theme-aware `.is-gain` / `.is-loss` color on the headline when the result is a surplus or shortfall (retirement calculator).
- **Three-column breakdown grid** under each headline shows sub-figures in Geist Mono with tabular figures.
- **Tokenized form controls** — reuses the `.form-field` / `.form-input` / `.form-select` components shipped with Milestone 6. New `.input-with-prefix` and `.input-with-suffix` wrappers for the `$` / `%` / `yrs` adornments.
- **Infrastructure** — `CALCULATORS` list in `config.py` (slug, name, short-question, description, category, template). New `build_calculators_hub()` + `build_calculator_pages()` in `build.py`. Sitemap includes calculator URLs. `dist/calculator/` directory created in `setup_output_directory()`.
- **Every calculator page links back to the advisor directory** at the bottom with the editorial CTA copy we agreed on — "These are estimates. A fiduciary advisor can model this against your actual tax situation, Social Security timing, and risk tolerance — things a single-input calculator can't capture." → primary button to `/`.

### Why it helps

- **High-intent SEO traffic.** "Compound interest calculator," "retirement calculator," and "savings goal calculator" are high-volume US search queries. Each page is a standalone ranking target with genuine utility — not the thin affiliate-filler that dominates the niche.
- **AdSense-amplifying behavior.** Calculator pages have strong dwell time and scroll depth (user types, sees results, reads the explanation below). That's exactly the signal AdSense rewards with higher CPMs post-approval.
- **Differentiation vs. every other advisor directory.** No competitor in this space has functioning calculators. A visitor who lands on a calculator and then sees a "find a fiduciary advisor" CTA below it is a much warmer lead than someone browsing the directory directly.
- **Progressive enhancement.** The form, explanation, disclaimer, and chart wrapper all render server-side, so the page indexes cleanly. JS turns the form into a live calculator. No frameworks, no Chart.js, no jQuery — zero new dependencies.
- **Reusable chart + form patterns.** Milestone 8 (three more calculators) will be ~60% the work of this milestone because the CSS + SVG-chart pattern is already in place.
- **Editorial explanations raise quality signal.** Each calculator page has ~300 words of real prose explaining what the math does, what assumptions it bakes in, and where it breaks down. That's unusual for calculator pages and reads as human-written, not AI-generated.

### Known gaps

- SVG charts are single-series. Milestone 8's Social Security calculator will likely need a two-series chart (claim at 62 vs. claim at 70); that's a small extension to the existing chart helper.
- Retirement calculator uses real return + today's-dollar framing (simpler), not nominal return + explicit inflation input (more accurate). Tradeoff chosen for clarity; noted in the editorial explanation.
- No print stylesheet variant for the calculator pages. Users who want to print their results see a reasonable default but the chart's SVG doesn't always render identically.
- The `Intl.NumberFormat` calls don't handle a zero-rate division-by-zero edge case cleanly on the compound-interest calculator when both rate and principal are zero (it displays `$0`, which is correct, but through a defensive path). Not worth more code for the edge case.

---

## Milestone 6 — Static pages + copy pivot (2026-04-18)

**Branch:** `redesign/static-pages`
**Commits:** two scoped commits
**Templates rewritten:** `about.html`, `contact.html`, `privacy.html`, `terms.html`, `success.html`
**CSS:** new `.static-page`, `.legal-prose`, `.form-field` / `.form-label` / `.form-input` / `.form-textarea` / `.form-select`, `.contact-grid` + `.contact-info-card`, `.success-page`, `.positioning-list`

### What changed

- **Dual-purpose milestone.** Every static page gets the finance-native style refresh **and** a copy rewrite. Drops every trace of the obsolete "Financial Tools Directory" brand (verified by grep after the build — zero remaining references across the five templates). Closes the final Milestone-0 known gap and closes Action 4 in the AdSense resubmission plan.
- **About page rewritten top to bottom.** New mission statement ("A directory of fiduciary advisors, built the way we'd want one for ourselves"), a "Why this exists" editorial explaining the gap we're filling, a "What you'll find here" three-section `.positioning-list` for directory + guides + tools, a "What we don't do" list with red × marks against each anti-position (no placement fees, no referrals, no AI reviews, no financial advice), a "How listings get added and removed" operations note, and a final Disclosure section that cleanly separates advisor-directory (zero affiliate) from tools (some affiliate).
- **Contact page.** New page head with editorial invitation, a left-column `.detail-card` hosting the Netlify Forms form (attributes preserved verbatim), a right-column `.contact-info` sidebar with four tokenized info cards (Response time, Before you write, Verifying an advisor, Are you an advisor?). Subject dropdown options updated for the advisor-directory era: "Suggest an advisor," "Report a listing correction," "Remove my firm from the directory," "Suggest a tool," "Business inquiry," "Feedback." Form fields moved to tokenized `.form-field` / `.form-input` / `.form-textarea` / `.form-select` components.
- **Privacy policy.** Updated to the current stack: Netlify, Airtable, Mailchimp, Google Analytics, Google AdSense, FINRA BrokerCheck, SEC IAPD. New section on how advisor listings are sourced from public regulatory records (not from user data), with a clear removal-request pathway. Data-retention window specified (14 months for analytics, indefinite for form submissions until deletion requested). Jurisdiction-agnostic data rights language ("we don't treat it as a GDPR-specific right, just the right thing to do").
- **Terms of service.** Dropped the tools-first framing. Added a "What this site is — and isn't" section making explicit that Smart Investor is not a registered investment advisor. Reframed the affiliate disclosure: advisor directory has **zero** affiliates, tools section has a small number. Added explicit "listings are not endorsements" and "a firm's presence is not a recommendation" clauses — required YMYL posture.
- **Success page.** Editorial voice ("Message received"), tokenized success checkmark in `--gain`-tinted circle, back-to-home + browse-guides CTAs. Response-time copy tightened to "within one business day."
- **New CSS components** — `.form-field` and siblings replace all of the Tailwind `border-gray-300 focus:ring-blue-500` utility stacks on the contact form. Tokenized focus state uses `color-mix(in srgb, var(--accent) 18%, transparent)` for the ring, which themes cleanly across light and dark.

### Why it helps

- **AdSense resubmission unblocker.** The resubmission plan's Action 4 specifically called out that static pages still described the old tools-directory brand. That's now closed. Legal pages (privacy, terms) now accurately describe the current product, which matters for YMYL content review.
- **Voice consistency end-to-end.** Every surface — homepage, directory, tools, blog, newsletter, about, legal — now speaks in the same editorial-finance register. No more tonal whiplash navigating between sections.
- **Reusable form-field components.** First use is the contact form. When the "submit an advisor" form ships (also in the AdSense plan), the fields will inherit the same tokenized styling automatically.
- **Stronger trust signals for a YMYL site.** The explicit anti-positioning on the About page ("we don't take placement fees," "we are not financial advisors") and the Terms clarity ("listings are not endorsements") matter more on a financial-services site than on a typical directory — both for user trust and AdSense review.
- **Founder-voice authenticity.** The About copy's plain-English phrasing ("Most advisor directories run on paid placements. We don't.") reads as human and opinionated, not AI-generated. That's a meaningful differentiator right now.

### Known gaps

- About page doesn't yet include a founder bio or team section. Kevin can add that at any point — the existing detail-card layout accommodates one more section cleanly.
- No "submit an advisor" dedicated form yet (separate from the contact-form topic). Flagged in the AdSense plan as an optional add.
- Governing-law clause in Terms is intentionally vague ("laws of the United States and, where applicable, the state in which the site operator resides"). If Kevin wants to pin a specific state, that's a one-line edit.

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
