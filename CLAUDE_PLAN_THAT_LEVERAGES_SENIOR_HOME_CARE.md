# Investment Advisor Directory — Pivot Plan

## Prompt to Initiate New Claude Code Session

Copy and paste this prompt when you start a new Claude Code session from this project directory:

---

**START OF PROMPT**

I'm pivoting this project from a financial tools directory to a national investment advisor directory. The site URL will remain smart-investor-financial-tools.com (or we may change the domain later).

I have a sister project at `/Users/kevincollins/GitHub/senior-home-care-directory/` that is a fully built national directory site (seniorhomecarefinder.com) with architecture we want to replicate. That project has:
- Python/Jinja2 static site generator with Airtable CMS
- State-level and city-level pages (the SEO money pages)
- Interactive Leaflet/OSM maps on state pages with marker clustering
- Sidebar layout with city list + list-style listing cards
- Blog system loading from local markdown files + Airtable
- Newsletter signup, social sharing, weather links
- Noindex logic for thin state/city pages (< 3 listings)
- Paginated Airtable fetch (100/page to avoid gateway timeouts)
- Description enrichment pipeline (deterministic MD5 templates, $0 cost)
- Outscraper data pipeline for Google Maps scraping
- Services backfill from keyword matching
- Listing validation script to remove non-relevant businesses
- 25 blog posts (~56,000 words)
- AdSense presubmission plan with all lessons learned

Please read the plan file at `/Users/kevincollins/GitHub/financial-tools-directory/CLAUDE_PLAN_THAT_LEVERAGES_SENIOR_HOME_CARE.md` for the full pivot strategy, architecture decisions, and implementation steps. Also read `/Users/kevincollins/GitHub/senior-home-care-directory/CLAUDE.md` for the reference project's architecture.

The existing financial tools (34 stock screeners, portfolio trackers, etc.) should be preserved as an "Investor Tools" section in the nav — this is unique content that differentiates us from other advisor directories.

Let's start by reviewing both projects and building the implementation plan together.

**END OF PROMPT**

---

## Background

### What This Project Is Today
- A financial tools directory at smart-investor-financial-tools.com
- 34 investment tools across 8 categories (Stock Screeners, Portfolio Trackers, etc.)
- Python/Jinja2 static site generator, Airtable CMS, Netlify hosting
- Same AdSense publisher ID as sibling sites (ca-pub-9265762311868507)
- Market data widget (live S&P, DOW, NASDAQ quotes)
- YouTube weekly market update embed
- 46 generated pages total
- No state/city pages, no blog, no maps

### What It Will Become
- A national investment advisor directory
- Advisors searchable by state, city, and specialty
- Existing tools preserved as an "Investor Tools" resource section
- Blog with original content on investing, retirement, choosing an advisor
- Same architecture as seniorhomecarefinder.com but adapted for financial services

### Why the Pivot
- 34 tools is too thin for AdSense approval — Google sees it as a small catalog/affiliate site
- Investment advisors are a geographically distributed dataset (~300,000+ registered in the US) — perfect for the directory pattern
- City-level pages ("financial advisor in [city]") are high-intent, high-value search queries
- Financial services advertising pays significantly higher CPC than other niches
- The directory factory pattern (proven with holistic vet, splash pad, senior home care) transfers directly

---

## Reference Project: Senior Home Care Directory

**Location:** `/Users/kevincollins/GitHub/senior-home-care-directory/`

### Key Files to Reference
| File | What to Learn From It |
|------|----------------------|
| `build.py` | State/city page generation, noindex logic, paginated Airtable fetch, blog loading from markdown, `_to_list()` helper |
| `config.py` | US_STATES list with editorial descriptions, SERVICES with expanded intros, site configuration |
| `templates/state.html` | Sidebar layout with Leaflet map + city list + list-style cards |
| `templates/city.html` | City-level SEO page template |
| `templates/agency.html` | Detail page with JSON-LD schema, sidebar contact card, weather link, social sharing |
| `templates/base.html` | Newsletter signup, dynamic og:image, noindex meta tag, Chart.js support |
| `templates/blog.html` | Blog with category filter buttons and hash-based deep linking |
| `templates/post.html` | Blog post with disclaimer, social sharing (FB, X, Pinterest, Email) |
| `templates/index.html` | Homepage with Resources & Guides category cards section |
| `outscraper_to_airtable.py` | Outscraper data processing pipeline |
| `backfill_services.py` | Keyword-based service field backfill |
| `enrich_descriptions.py` | Deterministic MD5 hash description enrichment ($0 cost) |
| `validate_listings.py` | Listing validation with word-boundary matching |
| `validate_from_csv.py` | Pre-enrichment CSV validation (avoids enriched descriptions masking bad data) |
| `auto_descriptions.py` | AI description generation with Claude Haiku |
| `ADSENSE_PRESUBMISSION_PLAN_SENIOR.md` | Complete AdSense preparation playbook |

### Patterns to Replicate Exactly
1. **State + city page structure** with noindex for thin pages (< 3 listings)
2. **Sitemap filtering** — exclude noindexed pages
3. **Paginated Airtable fetch** (100/page with 0.2s delay) — prevents gateway timeouts on Netlify
4. **Interactive Leaflet maps** on state pages with marker clustering
5. **List-style cards** on state pages (not grid cards — shows more info per listing)
6. **Blog system** with local markdown loading + Airtable, category filtering with hash deep-linking
7. **Newsletter signup** on every page (Netlify Forms)
8. **Social sharing** on detail + blog pages (Facebook, X, Pinterest, Email — URL-based, zero JS)
9. **Disclaimer** on blog posts (medical/financial/legal)
10. **Description enrichment pipeline** — validate BEFORE enriching (order matters)
11. **Dynamic og:image** — use listing photo for detail pages, post featured image for blog, fallback for others

---

## Architecture for Investment Advisor Directory

### URL Structure
```
/                                        → Homepage
/state/texas.html                        → State listing (with map + city sidebar)
/state/texas/houston.html                → City listing (money page)
/advisor/john-smith-houston-tx.html      → Advisor detail page
/specialty/retirement-planning.html      → Specialty filter page
/tools.html                              → Investor Tools hub (existing tools)
/tools/{slug}.html                       → Individual tool pages (existing)
/blog.html                               → Blog listing with category filters
/blog/{slug}.html                        → Blog post
/about.html                              → About (include founder story)
/contact.html                            → Contact form
/submit.html                             → Submit an advisor
/privacy.html                            → Privacy policy
/terms.html                              → Terms of service
```

### Airtable Schema: Advisors Table

| Field | Type | Notes |
|-------|------|-------|
| Name | Text | Advisor or firm name |
| Slug | Text | URL-friendly identifier |
| Description | Long text | About the advisor/firm |
| Address | Text | Street address |
| City | Text | City name |
| State | Text | Full state name (not abbreviation) |
| Zip | Text | ZIP code |
| Phone | Text | Contact phone |
| Website URL | URL | Advisor/firm website |
| Google Maps URL | URL | Google Maps link |
| Photo URL | URL | Headshot or firm logo |
| Hours | Text | Office hours |
| Specialties | Multi-select | Retirement Planning, Tax Strategy, Estate Planning, etc. |
| Credentials | Multi-select | CFP, CFA, CPA, ChFC, RICP, etc. |
| Services | Multi-select | Financial Planning, Investment Management, Tax Planning, etc. |
| Firm Type | Single select | Independent RIA, Wirehouse, Insurance-Based, Robo-Advisor, etc. |
| Minimum Investment | Text | e.g., "$250,000", "No minimum" |
| Fee Structure | Multi-select | Fee-Only, Fee-Based, Commission, Flat Fee, Hourly |
| Fiduciary | Checkbox | Is the advisor a fiduciary? |
| SEC Registered | Checkbox | SEC vs state registered |
| Rating | Number | Google rating |
| Review Count | Number | Google review count |
| Status | Single select | Active, Featured, Draft |
| Date Added | Date | When added to directory |
| Latitude | Number | For map display |
| Longitude | Number | For map display |
| Year Established | Number | Firm founding year |
| Languages | Multi-select | Languages spoken |

### Airtable Schema: Blog Posts Table
Same as senior home care project — Title, Slug, Content, Excerpt, Author, Publish Date, Featured Image, Meta Description, Status, Featured, Category

### Airtable Schema: Tools Table (Keep Existing)
No changes needed — the existing tools table stays as-is

### Specialties (replaces Services/Care Types)
```python
SPECIALTIES = [
    {"name": "Retirement Planning", "slug": "retirement-planning", "icon": "🏖️", ...},
    {"name": "Investment Management", "slug": "investment-management", "icon": "📈", ...},
    {"name": "Tax Strategy", "slug": "tax-strategy", "icon": "📋", ...},
    {"name": "Estate Planning", "slug": "estate-planning", "icon": "🏛️", ...},
    {"name": "College Savings", "slug": "college-savings", "icon": "🎓", ...},
    {"name": "Insurance Planning", "slug": "insurance-planning", "icon": "🛡️", ...},
    {"name": "Small Business", "slug": "small-business", "icon": "🏢", ...},
    {"name": "Wealth Management", "slug": "wealth-management", "icon": "💎", ...},
    {"name": "Debt Management", "slug": "debt-management", "icon": "📉", ...},
    {"name": "Social Security Planning", "slug": "social-security", "icon": "🏛️", ...},
]
```

### Credentials (new concept — important for trust)
```python
CREDENTIALS = [
    "CFP (Certified Financial Planner)",
    "CFA (Chartered Financial Analyst)",
    "CPA (Certified Public Accountant)",
    "ChFC (Chartered Financial Consultant)",
    "RICP (Retirement Income Certified Professional)",
    "CLU (Chartered Life Underwriter)",
    "EA (Enrolled Agent)",
]
```

### Fee Structures (important for user filtering)
```python
FEE_STRUCTURES = [
    "Fee-Only",        # No commissions — fiduciary standard
    "Fee-Based",       # Fees + some commissions
    "Commission",      # Commission-based
    "Flat Fee",        # Fixed fee per plan
    "Hourly",          # Hourly consulting rate
]
```

---

## Implementation Steps

### Phase 1: Core Directory (Days 1-2)
1. **Update CLAUDE.md** with new project context
2. **Rewrite config.py** — new site name, specialties, credentials, fee structures, US_STATES with financial editorial
3. **Rewrite build.py** — adapt from senior home care:
   - Keep existing tool page generation (tools stay)
   - Add advisor data model, state pages, city pages, advisor detail pages
   - Add specialty filter pages (like service pages)
   - Add blog infrastructure
   - Add noindex logic, paginated fetch, sitemap filtering
4. **Create new templates** — adapt from senior home care:
   - `state.html` — sidebar map + city list + list-style advisor cards
   - `city.html` — city-level advisor listing
   - `advisor.html` — detail page with JSON-LD (FinancialService schema), credentials display, fee structure, fiduciary badge
   - `specialty.html` — filter by specialty
   - `tools.html` — hub page linking to existing tool pages (preserve current tool.html)
   - `blog.html` — with category filtering
   - `post.html` — with disclaimer and social sharing
   - Update `base.html` — newsletter, dynamic og:image, noindex support
   - Update `index.html` — hero, state browser, specialty browser, resources section
5. **Update static pages** — about (include founder story), contact, submit, privacy, terms
6. **Create sample data** — 5-10 sample advisors for testing without Airtable
7. **Update netlify.toml** — add state/city/advisor/specialty/blog redirects

### Phase 2: Data Pipeline (Days 2-3)
8. **Set up Airtable** — create Advisors table with schema above, create Blog Posts table
9. **Create outscraper_to_airtable.py** — adapt for "financial advisor" / "investment advisor" Google Maps data
10. **Create backfill_specialties.py** — keyword matching for advisor specialties
11. **Create enrich_descriptions.py** — deterministic templates for advisor descriptions
12. **Create validate_listings.py** — flag non-advisor businesses (insurance-only agents, tax prep chains, banks, etc.)
13. **Run Outscraper** — start with top 5 states by population (CA, TX, FL, NY, PA)
14. **Process pipeline** — validate → backfill → enrich → import

### Phase 3: Content & SEO (Days 3-5)
15. **Write 25 blog posts** covering:
    - **Guides:** How to Choose a Financial Advisor, Questions to Ask Before Hiring, Fee-Only vs Fee-Based Explained
    - **Retirement:** When to Start Working with an Advisor, Social Security Optimization, 401k to IRA Rollover Guide
    - **Financial Planning:** How Much Does a Financial Advisor Cost, Is a Fiduciary Important, Understanding Robo-Advisors
    - **Tips:** Tax-Loss Harvesting Explained, Rebalancing Your Portfolio, Emergency Fund Guide
    - **Resources:** Understanding CFP Designation, SEC vs State Registration, How to Check an Advisor's Record (BrokerCheck)
16. **Add unique state editorial** — each state's financial landscape, retirement statistics, state tax implications
17. **Add expanded specialty intros** — what each specialty covers, who needs it, questions to ask
18. **Submit to Google Search Console** — verify and submit sitemap

### Phase 4: AdSense Prep (Days 5-7)
19. **Run full AdSense presubmission checklist** (from senior home care plan)
20. **Verify noindex pages working** — thin states/cities excluded
21. **Audit descriptions** — run validate_from_csv.py before enrichment
22. **Check Lighthouse scores** — target > 90
23. **Test mobile responsiveness**
24. **Verify schema markup** — Google Rich Results Test
25. **Wait 2-3 weeks for Google to crawl**
26. **Submit to AdSense**

---

## Key Differences from Senior Home Care

| Aspect | Senior Home Care | Investment Advisor |
|--------|-----------------|-------------------|
| JSON-LD schema | HomeHealthCareService | FinancialService |
| Key trust signal | Accreditations (CHAP, JC) | Credentials (CFP, CFA) + Fiduciary status |
| Fee display | Payment options (Medicare, Medicaid) | Fee structure (Fee-Only, Commission) |
| Unique feature | Weather link | Investor Tools section |
| Regulatory check | State licensing | SEC/FINRA BrokerCheck link |
| Disclaimer | Medical/financial/legal | Financial/legal (no medical) |
| Blog categories | Guides, Family Caregiving, Care Types, Financial Planning, Tips, Resources | Guides, Retirement, Financial Planning, Investing, Tax Strategy, Resources |
| Data source | Outscraper "home care agency" | Outscraper "financial advisor" + "investment advisor" |

---

## Design Notes

- **Colors:** Keep the blue gradient theme (works well for financial/trust) — can refine shades
- **Fiduciary badge:** Prominent green badge on advisor cards and detail pages — this is the #1 trust signal for consumers
- **Credentials display:** Show CFP, CFA, etc. as badges (like we show services on home care cards)
- **Fee transparency:** Display fee structure clearly on cards — consumers care about this
- **BrokerCheck link:** Add "Verify on BrokerCheck" link to advisor detail sidebar (links to FINRA BrokerCheck)
- **Existing tools:** Nav item "Investor Tools" with dropdown linking to tool categories, separate from the advisor directory

---

## Files to Create/Modify Summary

### New Files
- `templates/state.html` — from senior home care
- `templates/city.html` — from senior home care
- `templates/advisor.html` — adapted from agency.html
- `templates/specialty.html` — adapted from service.html
- `templates/tools.html` — new hub page for existing tools
- `templates/blog.html` — from senior home care
- `templates/post.html` — from senior home care
- `templates/_advisor_card.html` — adapted from _agency_card.html
- `templates/submit.html` — submit an advisor form
- `outscraper_to_airtable.py` — adapted for financial advisors
- `backfill_specialties.py` — keyword matching
- `enrich_descriptions.py` — deterministic templates
- `validate_listings.py` — non-advisor detection
- `auto_descriptions.py` — AI fallback
- `content/blogposts/*.md` — 25 blog posts
- `ADSENSE_PRESUBMISSION_PLAN_ADVISOR.md` — AdSense prep plan

### Files to Modify
- `config.py` — complete rewrite (keep US_STATES pattern)
- `build.py` — major additions (state/city/advisor/blog pages), keep tool page generation
- `templates/base.html` — newsletter, og:image, noindex, nav updates
- `templates/index.html` — new homepage layout
- `templates/about.html` — updated mission + founder story
- `templates/contact.html` — minor updates
- `templates/privacy.html` — update for advisor data
- `templates/terms.html` — update for advisor directory
- `netlify.toml` — add redirects for new URL patterns
- `requirements.txt` — add any missing deps

### Files to Keep Unchanged
- `templates/tool.html` — existing tool detail pages
- `templates/category.html` — existing tool category pages
- `static/css/custom.css` — extend as needed
- `ads.txt` — same publisher ID
- `smart-investor-logo.png` — keep or update later

---

## Outscraper Search Tags

For scraping financial advisors from Google Maps:
```
financial advisor
investment advisor
certified financial planner
wealth management
financial planner
retirement planning advisor
```

**Important:** Run validation BEFORE description enrichment. Financial advisor scrapes will include insurance agents, tax prep chains (H&R Block, Jackson Hewitt), banks, mortgage brokers, and other non-advisor businesses.

### Non-Advisor Keywords for Validation Script
```python
NEGATIVE_KEYWORDS = [
    "h&r block", "jackson hewitt", "liberty tax",
    "insurance", "allstate", "state farm", "geico", "progressive",
    "mortgage", "lending", "loan",
    "bank", "credit union", "atm",
    "accounting", "bookkeeping", "payroll",
    "tax prep", "tax preparation",
    "real estate", "realty", "realtor",
    "auto", "car", "restaurant", "hotel",
    # ... expand from senior home care pattern
]
```

---

## Lessons Learned (from 3 Directory Projects)

1. **Validate data BEFORE enriching descriptions** — enriched descriptions mask bad data
2. **Noindex thin pages from day one** — don't let Google index empty state/city pages
3. **Blog posts are critical for AdSense** — 25+ posts, 1,500-2,500 words each, original content
4. **State pages need unique editorial** — not just template text with state name injected
5. **Paginate Airtable fetches** — 100/page with delay prevents Netlify gateway timeouts
6. **Use multi-select fields in Airtable** — not comma-separated text
7. **Match field names exactly** between config, build script, and Airtable
8. **Interactive maps add unique content** — Leaflet/OSM is free and Google values interactive elements
9. **Category filter on blog page** — use hash-based deep linking from homepage cards
10. **Personal founder story** — adds authenticity that no AI content can replicate
11. **Disclaimer on all blog posts** — especially important for financial content
12. **Don't submit to AdSense until Google has crawled** — wait 2-3 weeks after deploy
