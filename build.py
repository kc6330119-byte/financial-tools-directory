#!/usr/bin/env python3
"""
Smart Investor - Static Site Generator

Generates a national investment advisor directory with state/city pages,
advisor detail pages, specialty filter pages, blog, and investor tools section.
Fetches data from Airtable with fallback to sample data.
"""
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

import markdown as md_lib
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
from slugify import slugify

import config


# =============================================================================
# HELPERS
# =============================================================================

def _to_list(val):
    """Convert a value to a list — handles comma-separated strings from Airtable text fields."""
    if isinstance(val, list):
        return val
    if isinstance(val, str) and val.strip():
        return [s.strip() for s in val.split(",") if s.strip()]
    return []


# =============================================================================
# TOOL DATA (existing — preserved from original site)
# =============================================================================

def get_sample_tool_data():
    """Return sample tools for testing without Airtable."""
    return [
        {
            "name": "Alpha Vantage",
            "slug": "alpha-vantage",
            "description": "Free APIs for realtime and historical stock data, forex, and cryptocurrency. "
                           "Offers both free and premium tiers with extensive documentation.",
            "category": ["Data Providers"],
            "pricing_model": "Freemium",
            "price_range": "Free - $49.99/mo",
            "website_url": "https://www.alphavantage.co/",
            "logo_url": "https://www.alphavantage.co/static/img/favicon.ico",
            "features": ["Real-time Data", "Historical Data", "REST API", "Technical Indicators"],
            "rating": 4.5,
            "review_count": 127,
            "api_available": True,
            "mobile_app": False,
            "data_sources": ["Real-time", "Historical"],
            "target_audience": ["Developers", "Traders", "Analysts"],
            "status": "Featured",
            "date_added": "2024-01-15",
        },
        {
            "name": "TradingView",
            "slug": "tradingview",
            "description": "Advanced charting platform with social features. Create, share, and discover "
                           "trading ideas with a community of traders worldwide.",
            "category": ["Technical Analysis", "Trading Platforms"],
            "pricing_model": "Freemium",
            "price_range": "Free - $59.95/mo",
            "website_url": "https://www.tradingview.com/",
            "logo_url": "https://www.tradingview.com/static/images/favicon.ico",
            "features": ["Advanced Charts", "Social Trading", "Alerts", "Screener"],
            "rating": 4.8,
            "review_count": 892,
            "api_available": True,
            "mobile_app": True,
            "data_sources": ["Real-time", "Delayed"],
            "target_audience": ["Active Traders", "Technical Analysts"],
            "status": "Featured",
            "date_added": "2024-01-10",
        },
        {
            "name": "Yahoo Finance",
            "slug": "yahoo-finance",
            "description": "Comprehensive financial news, data, and portfolio tracking. One of the most "
                           "popular free financial platforms available.",
            "category": ["Portfolio Trackers", "News & Alerts", "Research Tools"],
            "pricing_model": "Freemium",
            "price_range": "Free - $34.99/mo",
            "website_url": "https://finance.yahoo.com/",
            "logo_url": "https://s.yimg.com/rz/l/favicon.ico",
            "features": ["Portfolio Tracking", "News", "Screener", "Watchlists"],
            "rating": 4.2,
            "review_count": 456,
            "api_available": False,
            "mobile_app": True,
            "data_sources": ["Real-time", "Delayed", "EOD"],
            "target_audience": ["Beginners", "Casual Investors"],
            "status": "Active",
            "date_added": "2024-01-05",
        },
    ]


def fetch_tools_from_airtable():
    """Fetch tools from Airtable API."""
    if not config.AIRTABLE_API_KEY or not config.AIRTABLE_BASE_ID:
        return None

    try:
        from pyairtable import Api

        api = Api(config.AIRTABLE_API_KEY)
        table = api.table(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME)
        records = table.all()

        tools = []
        for record in records:
            fields = record.get("fields", {})
            if fields.get("Status") == "Draft":
                continue

            tool = {
                "name": fields.get("Name", ""),
                "slug": slugify(fields.get("Name", "")),
                "description": fields.get("Description", ""),
                "category": fields.get("Category", []),
                "pricing_model": fields.get("Pricing Model", ""),
                "price_range": fields.get("Price Range", ""),
                "website_url": fields.get("Website URL", ""),
                "logo_url": fields.get("Logo URL", ""),
                "features": fields.get("Features", []),
                "rating": fields.get("Rating", 0),
                "review_count": fields.get("Review Count", 0),
                "api_available": fields.get("API Available ", False),
                "mobile_app": fields.get("Mobile App ", False),
                "data_sources": fields.get("Data Sources", []),
                "target_audience": fields.get("Target Audience", []),
                "affiliate_link": fields.get("Affiliate Link", ""),
                "status": fields.get("Status", "Active"),
                "date_added": fields.get("Date Added", ""),
            }
            tools.append(tool)

        print(f"  Fetched {len(tools)} tools from Airtable.")
        return tools

    except Exception as e:
        print(f"  Error fetching tools from Airtable: {e}")
        return None


def get_tools():
    """Get tools from Airtable or fall back to sample data."""
    tools = fetch_tools_from_airtable()
    if tools is None:
        tools = get_sample_tool_data()
        print(f"  Using {len(tools)} sample tools.")
    return tools


def group_tools_by_category(tools):
    """Group tools by their categories."""
    grouped = {cat["slug"]: [] for cat in config.CATEGORIES}
    for tool in tools:
        for category_name in tool.get("category", []):
            category_slug = slugify(category_name)
            if category_slug in grouped:
                grouped[category_slug].append(tool)
    return grouped


# =============================================================================
# ADVISOR DATA
# =============================================================================

def get_sample_advisor_data():
    """Return sample advisors for testing without Airtable."""
    return [
        {
            "name": "Smith Wealth Management",
            "slug": "smith-wealth-management-houston-tx",
            "description": "Smith Wealth Management is an independent, fee-only financial advisory firm serving clients in the Greater Houston area. With over 20 years of experience, our CFP professionals specialize in retirement planning, tax-efficient investing, and estate planning for high-net-worth individuals and families.",
            "address": "1234 Main Street, Suite 500",
            "city": "Houston",
            "state": "Texas",
            "state_slug": "texas",
            "city_slug": "houston",
            "zip": "77002",
            "phone": "(713) 555-0100",
            "website_url": "https://example.com/smith-wealth",
            "google_maps_url": "",
            "photo_url": "",
            "hours": "Mon-Fri: 8:30am-5:00pm",
            "specialties": ["Retirement Planning", "Tax Strategy", "Estate Planning"],
            "credentials": ["CFP", "CFA"],
            "services": ["Financial Planning", "Investment Management", "Tax Planning"],
            "firm_type": "Independent RIA",
            "minimum_investment": "$500,000",
            "fee_structure": ["Fee-Only"],
            "fiduciary": True,
            "sec_registered": True,
            "languages": ["English", "Spanish"],
            "year_established": 2003,
            "rating": 4.9,
            "review_count": 87,
            "status": "Featured",
            "date_added": "2025-01-15",
            "latitude": 29.7604,
            "longitude": -95.3698,
        },
        {
            "name": "Austin Financial Partners",
            "slug": "austin-financial-partners-austin-tx",
            "description": "Austin Financial Partners helps tech professionals and entrepreneurs build lasting wealth. We specialize in equity compensation planning, Roth conversion strategies, and comprehensive financial planning for Austin's growing tech community.",
            "address": "500 Congress Ave, Suite 200",
            "city": "Austin",
            "state": "Texas",
            "state_slug": "texas",
            "city_slug": "austin",
            "zip": "78701",
            "phone": "(512) 555-0200",
            "website_url": "https://example.com/austin-financial",
            "google_maps_url": "",
            "photo_url": "",
            "hours": "Mon-Fri: 9:00am-5:30pm",
            "specialties": ["Investment Management", "Tax Strategy", "Wealth Management"],
            "credentials": ["CFP", "CPA"],
            "services": ["Financial Planning", "Investment Management", "Tax Planning"],
            "firm_type": "Independent RIA",
            "minimum_investment": "$250,000",
            "fee_structure": ["Fee-Only"],
            "fiduciary": True,
            "sec_registered": True,
            "languages": ["English"],
            "year_established": 2015,
            "rating": 4.8,
            "review_count": 52,
            "status": "Featured",
            "date_added": "2025-01-20",
            "latitude": 30.2672,
            "longitude": -97.7431,
        },
        {
            "name": "Lakefront Advisors",
            "slug": "lakefront-advisors-chicago-il",
            "description": "Lakefront Advisors is a Chicago-based wealth management firm providing personalized financial planning for executives, business owners, and retirees. Our team of CFP and CFA professionals takes a holistic approach to your financial life.",
            "address": "200 N Michigan Ave, Suite 1500",
            "city": "Chicago",
            "state": "Illinois",
            "state_slug": "illinois",
            "city_slug": "chicago",
            "zip": "60601",
            "phone": "(312) 555-0300",
            "website_url": "https://example.com/lakefront",
            "google_maps_url": "",
            "photo_url": "",
            "hours": "Mon-Fri: 8:00am-6:00pm",
            "specialties": ["Retirement Planning", "Wealth Management", "Estate Planning"],
            "credentials": ["CFP", "CFA", "ChFC"],
            "services": ["Financial Planning", "Investment Management", "Estate Planning"],
            "firm_type": "Independent RIA",
            "minimum_investment": "$1,000,000",
            "fee_structure": ["Fee-Only"],
            "fiduciary": True,
            "sec_registered": True,
            "languages": ["English", "Polish"],
            "year_established": 1998,
            "rating": 4.7,
            "review_count": 134,
            "status": "Active",
            "date_added": "2025-02-01",
            "latitude": 41.8781,
            "longitude": -87.6298,
        },
        {
            "name": "Dallas Retirement Group",
            "slug": "dallas-retirement-group-dallas-tx",
            "description": "Dallas Retirement Group specializes in helping pre-retirees and retirees maximize their retirement income. We focus on Social Security optimization, pension distribution strategies, and creating sustainable withdrawal plans.",
            "address": "2100 Ross Ave, Suite 800",
            "city": "Dallas",
            "state": "Texas",
            "state_slug": "texas",
            "city_slug": "dallas",
            "zip": "75201",
            "phone": "(214) 555-0400",
            "website_url": "https://example.com/dallas-retirement",
            "google_maps_url": "",
            "photo_url": "",
            "hours": "Mon-Fri: 9:00am-5:00pm",
            "specialties": ["Retirement Planning", "Social Security Planning", "Insurance Planning"],
            "credentials": ["CFP", "RICP"],
            "services": ["Retirement Planning", "Social Security Optimization", "Insurance Analysis"],
            "firm_type": "Independent RIA",
            "minimum_investment": "No minimum",
            "fee_structure": ["Flat Fee", "Hourly"],
            "fiduciary": True,
            "sec_registered": False,
            "languages": ["English", "Spanish"],
            "year_established": 2010,
            "rating": 4.6,
            "review_count": 45,
            "status": "Active",
            "date_added": "2025-02-10",
            "latitude": 32.7767,
            "longitude": -96.7970,
        },
        {
            "name": "Sunshine Wealth Advisors",
            "slug": "sunshine-wealth-advisors-miami-fl",
            "description": "Sunshine Wealth Advisors serves South Florida's diverse community with bilingual financial planning services. We specialize in international wealth management, cross-border planning, and retirement strategies for clients relocating to Florida.",
            "address": "100 Biscayne Blvd, Suite 2000",
            "city": "Miami",
            "state": "Florida",
            "state_slug": "florida",
            "city_slug": "miami",
            "zip": "33132",
            "phone": "(305) 555-0500",
            "website_url": "https://example.com/sunshine-wealth",
            "google_maps_url": "",
            "photo_url": "",
            "hours": "Mon-Fri: 9:00am-6:00pm",
            "specialties": ["Wealth Management", "Tax Strategy", "Retirement Planning"],
            "credentials": ["CFP", "CPA", "EA"],
            "services": ["Wealth Management", "Tax Planning", "International Planning"],
            "firm_type": "Independent RIA",
            "minimum_investment": "$500,000",
            "fee_structure": ["Fee-Only"],
            "fiduciary": True,
            "sec_registered": True,
            "languages": ["English", "Spanish", "Portuguese"],
            "year_established": 2008,
            "rating": 4.8,
            "review_count": 201,
            "status": "Featured",
            "date_added": "2025-01-05",
            "latitude": 25.7617,
            "longitude": -80.1918,
        },
    ]


def fetch_advisors_from_airtable():
    """Fetch advisors from Airtable API with paginated fetch to avoid gateway timeouts."""
    if not config.AIRTABLE_API_KEY or not config.AIRTABLE_BASE_ID:
        print("  Airtable not configured. Using sample data.")
        return None

    try:
        from pyairtable import Api

        api = Api(config.AIRTABLE_API_KEY, timeout=(30, 60))
        table = api.table(config.AIRTABLE_BASE_ID, config.AIRTABLE_ADVISORS_TABLE_NAME)

        # Paginated fetch (100/page with delay) to avoid Netlify gateway timeouts
        records = []
        for page in table.iterate(page_size=100):
            records.extend(page)
            print(f"  Fetched {len(records)} advisor records so far...")
            time.sleep(0.2)

        advisors = []
        for record in records:
            fields = record.get("fields", {})
            if fields.get("Status") == "Draft":
                continue

            state_name = fields.get("State", "")
            city_name = fields.get("City", "")
            advisor = {
                "name": fields.get("Name", ""),
                "slug": fields.get("Slug") or slugify(fields.get("Name", "") + "-" + city_name),
                "description": fields.get("Description", ""),
                "address": fields.get("Address", ""),
                "city": city_name,
                "state": state_name,
                "state_slug": slugify(state_name),
                "city_slug": slugify(city_name),
                "zip": fields.get("Zip", ""),
                "phone": fields.get("Phone", ""),
                "website_url": fields.get("Website URL", ""),
                "google_maps_url": fields.get("Google Maps URL", ""),
                "photo_url": fields.get("Photo URL", ""),
                "hours": fields.get("Hours", ""),
                "specialties": _to_list(fields.get("Specialties", [])),
                "credentials": _to_list(fields.get("Credentials", [])),
                "services": _to_list(fields.get("Services", [])),
                "firm_type": fields.get("Firm Type", ""),
                "minimum_investment": fields.get("Minimum Investment", ""),
                "fee_structure": _to_list(fields.get("Fee Structure", [])),
                "fiduciary": fields.get("Fiduciary", False),
                "sec_registered": fields.get("SEC Registered", False),
                "languages": _to_list(fields.get("Languages", [])),
                "year_established": fields.get("Year Established", ""),
                "rating": fields.get("Rating", 0),
                "review_count": fields.get("Review Count", 0),
                "status": fields.get("Status", "Active"),
                "date_added": fields.get("Date Added", ""),
                "latitude": fields.get("Latitude", ""),
                "longitude": fields.get("Longitude", ""),
            }
            advisors.append(advisor)

        print(f"  Fetched {len(advisors)} advisors from Airtable.")
        return advisors

    except Exception as e:
        print(f"  Error fetching advisors from Airtable: {e}")
        return None


def get_advisors():
    """Get advisors from Airtable or fall back to sample data."""
    advisors = fetch_advisors_from_airtable()
    if advisors is None:
        advisors = get_sample_advisor_data()
        print(f"  Using {len(advisors)} sample advisors.")
    return advisors


def group_advisors_by_state(advisors):
    """Group advisors by state slug."""
    grouped = {}
    for advisor in advisors:
        state_slug = advisor.get("state_slug", "")
        if state_slug:
            grouped.setdefault(state_slug, []).append(advisor)
    return grouped


def group_advisors_by_city(advisors):
    """Group advisors by state and city."""
    grouped = {}
    for advisor in advisors:
        state_slug = advisor.get("state_slug", "")
        city_slug = advisor.get("city_slug", "")
        if state_slug and city_slug:
            key = (state_slug, city_slug, advisor.get("city", ""), advisor.get("state", ""))
            grouped.setdefault(key, []).append(advisor)
    return grouped


# =============================================================================
# BLOG DATA
# =============================================================================

def load_local_blog_posts():
    """Load blog posts from local markdown files in content/blogposts/."""
    blog_dir = config.CONTENT_DIR / "blogposts"
    if not blog_dir.exists():
        return []

    posts = []
    for md_file in sorted(blog_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")

        # Parse frontmatter between ``` markers
        meta = {}
        content = text
        if text.startswith("```"):
            parts = text.split("```", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, _, value = line.partition(":")
                        meta[key.strip().lower()] = value.strip()
                content = parts[2].strip()

        status = meta.get("status", "Published")
        if status != "Published":
            continue

        title = meta.get("title", md_file.stem)
        post = {
            "title": title,
            "slug": meta.get("slug", slugify(title)),
            "content": content,
            "excerpt": meta.get("excerpt", ""),
            "author": meta.get("author", "Smart Investor Staff"),
            "publish_date": meta.get("published date", meta.get("publish date", "")),
            "featured_image": meta.get("featured image", ""),
            "meta_description": meta.get("meta description", ""),
            "status": status,
            "featured": meta.get("featured", "").lower() == "true",
            "category": meta.get("category", ""),
        }
        posts.append(post)

    if posts:
        print(f"  Loaded {len(posts)} blog posts from content/blogposts/.")
    return posts


def fetch_blog_posts():
    """Fetch published blog posts from Airtable. Local markdown files in
    content/blogposts/ are kept as a backup library but are not used in builds."""
    posts = []
    if config.AIRTABLE_API_KEY and config.AIRTABLE_BASE_ID:
        try:
            from pyairtable import Api

            api = Api(config.AIRTABLE_API_KEY)
            table = api.table(config.AIRTABLE_BASE_ID, config.AIRTABLE_BLOG_TABLE_NAME)
            records = table.all()

            for record in records:
                fields = record.get("fields", {})
                if fields.get("Status") != "Published":
                    continue

                title = fields.get("Title", "")
                slug = (fields.get("Slug", "") or slugify(title)).strip()

                featured_image = fields.get("Featured Image", "")
                if isinstance(featured_image, list) and featured_image:
                    featured_image = featured_image[0].get("url", "")

                post = {
                    "title": title,
                    "slug": slug,
                    "content": fields.get("Content", ""),
                    "excerpt": fields.get("Excerpt", ""),
                    "author": fields.get("Author", "Smart Investor Staff"),
                    "publish_date": fields.get("Publish Date", ""),
                    "featured_image": featured_image,
                    "meta_description": fields.get("Meta Description", ""),
                    "status": fields.get("Status", "Published"),
                    "featured": fields.get("Featured", False),
                    "category": fields.get("Category", ""),
                }
                posts.append(post)

            print(f"  Fetched {len(posts)} blog posts from Airtable.")

        except Exception as e:
            print(f"  Note: Could not fetch blog posts ({e})")

    posts.sort(key=lambda x: x.get("publish_date", ""), reverse=True)
    return posts


# =============================================================================
# OUTPUT SETUP
# =============================================================================

def setup_output_directory():
    """Create clean output directory."""
    if config.OUTPUT_DIR.exists():
        shutil.rmtree(config.OUTPUT_DIR)

    config.OUTPUT_DIR.mkdir(parents=True)
    (config.OUTPUT_DIR / "state").mkdir()
    (config.OUTPUT_DIR / "advisor").mkdir()
    (config.OUTPUT_DIR / "specialty").mkdir()
    (config.OUTPUT_DIR / "category").mkdir()
    (config.OUTPUT_DIR / "tool").mkdir()
    (config.OUTPUT_DIR / "blog").mkdir()

    # Copy static files
    if config.STATIC_DIR.exists():
        shutil.copytree(config.STATIC_DIR, config.OUTPUT_DIR / "static")


# =============================================================================
# JINJA ENVIRONMENT
# =============================================================================

def create_jinja_env():
    """Create Jinja2 environment with custom filters and globals."""
    env = Environment(
        loader=FileSystemLoader(config.TEMPLATES_DIR),
        autoescape=True
    )

    def format_date(date_str):
        if not date_str:
            return ""
        try:
            dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
            return dt.strftime("%B ") + str(dt.day) + dt.strftime(", %Y")
        except (ValueError, TypeError):
            return date_str

    def star_rating(rating):
        """Convert numeric rating to star display."""
        if not rating:
            return ""
        full_stars = int(rating)
        half_star = 1 if rating - full_stars >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        return "\u2605" * full_stars + "\u00bd" * half_star + "\u2606" * empty_stars

    env.filters["slugify"] = slugify
    env.filters["tojson"] = lambda v: Markup(json.dumps(v, ensure_ascii=False))
    env.filters["markdown"] = lambda text: Markup(md_lib.markdown(text or "", extensions=["extra", "nl2br"]))
    env.filters["format_date"] = format_date
    env.filters["star_rating"] = star_rating

    # Global variables available in all templates
    env.globals["site_name"] = config.SITE_NAME
    env.globals["site_url"] = config.SITE_URL
    env.globals["site_description"] = config.SITE_DESCRIPTION
    env.globals["categories"] = config.CATEGORIES
    env.globals["specialties"] = config.SPECIALTIES
    env.globals["us_states"] = config.US_STATES
    env.globals["credentials"] = config.CREDENTIALS
    env.globals["fee_structures"] = config.FEE_STRUCTURES
    env.globals["blog_categories"] = config.BLOG_CATEGORIES
    env.globals["current_year"] = datetime.now().year
    env.globals["ga_measurement_id"] = config.GA_MEASUREMENT_ID

    return env


# =============================================================================
# BUILD: HOMEPAGE
# =============================================================================

def build_homepage(env, tools, advisors, posts):
    """Build the homepage — advisor directory focus with tools and blog preview."""
    template = env.get_template("index.html")

    # Featured tools
    featured_tools = [t for t in tools if t.get("status") == "Featured"][:config.FEATURED_COUNT]

    # Featured advisors
    featured_advisors = [a for a in advisors if a.get("status") == "Featured"][:config.FEATURED_COUNT]
    if not featured_advisors:
        featured_advisors = advisors[:config.FEATURED_COUNT]

    recent_advisors = sorted(advisors, key=lambda x: x.get("date_added", ""), reverse=True)[:config.RECENT_COUNT]

    # State counts for browse grid
    by_state = group_advisors_by_state(advisors)
    state_counts = {s: len(v) for s, v in by_state.items()}

    # Blog categories with counts
    blog_cats = []
    for cat in config.BLOG_CATEGORIES:
        count = sum(1 for p in posts if p.get("category", "").lower() == cat["name"].lower())
        blog_cats.append({**cat, "count": count})
    blog_categories = [c for c in blog_cats if c["count"] > 0]

    recent_posts = posts[:3]

    html = template.render(
        featured_tools=featured_tools,
        all_tools=tools,
        featured_advisors=featured_advisors,
        recent_advisors=recent_advisors,
        all_advisors=advisors,
        state_counts=state_counts,
        total_advisor_count=len(advisors),
        total_tool_count=len(tools),
        blog_categories=blog_categories,
        recent_posts=recent_posts,
        total_posts=len(posts),
        page_title=config.DEFAULT_META_TITLE,
        meta_description=config.DEFAULT_META_DESCRIPTION,
        request_path="/",
    )

    output_path = config.OUTPUT_DIR / "index.html"
    output_path.write_text(html)
    print(f"Built: index.html ({len(advisors)} advisors, {len(tools)} tools)")


# =============================================================================
# BUILD: STATE PAGES
# =============================================================================

MIN_ADVISORS_FOR_INDEX = 3


def build_state_pages(env, advisors):
    """Build one page per US state with Leaflet map, city sidebar, and advisor list."""
    template = env.get_template("state.html")
    grouped = group_advisors_by_state(advisors)

    indexed_states = []
    noindexed_states = []

    for state in config.US_STATES:
        state_advisors = grouped.get(state["slug"], [])
        state_advisors.sort(key=lambda x: x.get("city", ""))

        # Group by city for sidebar
        cities = {}
        for advisor in state_advisors:
            city = advisor.get("city", "Unknown")
            city_slug = advisor.get("city_slug", "unknown")
            cities.setdefault((city, city_slug), []).append(advisor)

        noindex = len(state_advisors) < MIN_ADVISORS_FOR_INDEX

        if noindex:
            noindexed_states.append(state["name"])
        else:
            indexed_states.append(state["slug"])

        html = template.render(
            state=state,
            advisors=state_advisors,
            cities=cities,
            noindex=noindex,
            page_title=f"Investment Advisors in {state['name']} - {config.SITE_NAME}",
            meta_description=f"Find {len(state_advisors)} trusted investment advisors in {state['name']}. Compare credentials, fee structures, and specialties.",
            request_path=f"/state/{state['slug']}.html",
        )

        output_path = config.OUTPUT_DIR / "state" / f"{state['slug']}.html"
        output_path.write_text(html)
        print(f"Built: state/{state['slug']}.html ({len(state_advisors)} advisors{' [noindex]' if noindex else ''})")

    if noindexed_states:
        print(f"  Noindexed {len(noindexed_states)} state pages (< {MIN_ADVISORS_FOR_INDEX} advisors)")

    return indexed_states


# =============================================================================
# BUILD: CITY PAGES
# =============================================================================

def build_city_pages(env, advisors):
    """Build one page per city (within state folders)."""
    template = env.get_template("city.html")
    grouped = group_advisors_by_city(advisors)

    indexed_cities = []
    noindex_count = 0

    for (state_slug, city_slug, city_name, state_name), city_advisors in grouped.items():
        city_advisors.sort(key=lambda x: x.get("name", ""))

        state_folder = config.OUTPUT_DIR / "state" / state_slug
        state_folder.mkdir(parents=True, exist_ok=True)

        state_info = next(
            (s for s in config.US_STATES if s["slug"] == state_slug),
            {"name": state_name, "slug": state_slug, "abbr": ""}
        )

        noindex = len(city_advisors) < MIN_ADVISORS_FOR_INDEX

        if noindex:
            noindex_count += 1
        else:
            indexed_cities.append(f"{state_slug}/{city_slug}")

        html = template.render(
            city=city_name,
            city_slug=city_slug,
            state=state_info,
            advisors=city_advisors,
            noindex=noindex,
            page_title=f"Investment Advisors in {city_name}, {state_info.get('abbr', '') or state_name} - {config.SITE_NAME}",
            meta_description=f"Find {len(city_advisors)} investment advisors in {city_name}, {state_name}. Compare fee structures, credentials, and specialties.",
            request_path=f"/state/{state_slug}/{city_slug}.html",
        )

        output_path = state_folder / f"{city_slug}.html"
        output_path.write_text(html)
        print(f"Built: state/{state_slug}/{city_slug}.html ({len(city_advisors)} advisors{' [noindex]' if noindex else ''})")

    if noindex_count:
        print(f"  Noindexed {noindex_count} city pages (< {MIN_ADVISORS_FOR_INDEX} advisors)")

    return indexed_cities


# =============================================================================
# BUILD: ADVISOR DETAIL PAGES
# =============================================================================

def build_advisor_pages(env, advisors):
    """Build individual advisor detail pages with JSON-LD FinancialService schema."""
    template = env.get_template("advisor.html")

    for advisor in advisors:
        related = [
            a for a in advisors
            if a["slug"] != advisor["slug"] and (
                a.get("city_slug") == advisor.get("city_slug") or
                a.get("state_slug") == advisor.get("state_slug")
            )
        ][:4]

        state_info = next(
            (s for s in config.US_STATES if s["slug"] == advisor.get("state_slug")),
            {"name": advisor.get("state", ""), "slug": advisor.get("state_slug", ""), "abbr": ""}
        )

        html = template.render(
            advisor=advisor,
            state=state_info,
            related_advisors=related,
            page_title=f"{advisor['name']} - {advisor['city']}, {advisor['state']} - {config.SITE_NAME}",
            meta_description=advisor.get("description", "")[:160] or f"{advisor['name']} is an investment advisor in {advisor['city']}, {advisor['state']}.",
            page_image=advisor.get("photo_url", ""),
            request_path=f"/advisor/{advisor['slug']}.html",
        )

        output_path = config.OUTPUT_DIR / "advisor" / f"{advisor['slug']}.html"
        output_path.write_text(html)
        print(f"Built: advisor/{advisor['slug']}.html")


# =============================================================================
# BUILD: SPECIALTY PAGES
# =============================================================================

def build_specialty_pages(env, advisors):
    """Build specialty filter pages (like service pages in senior home care)."""
    template = env.get_template("specialty.html")

    for specialty in config.SPECIALTIES:
        specialty_advisors = [
            a for a in advisors
            if specialty["name"] in a.get("specialties", [])
        ]

        # State breakdown for sidebar
        state_counts = {}
        for a in specialty_advisors:
            s = a.get("state", "")
            if s:
                state_counts[s] = state_counts.get(s, 0) + 1
        state_list = sorted(state_counts.items(), key=lambda x: (-x[1], x[0]))

        html = template.render(
            specialty=specialty,
            advisors=specialty_advisors,
            state_list=state_list,
            page_title=f"{specialty['name']} Advisors - {config.SITE_NAME}",
            meta_description=specialty["description"],
            request_path=f"/specialty/{specialty['slug']}.html",
        )

        output_path = config.OUTPUT_DIR / "specialty" / f"{specialty['slug']}.html"
        output_path.write_text(html)
        print(f"Built: specialty/{specialty['slug']}.html ({len(specialty_advisors)} advisors)")


# =============================================================================
# BUILD: TOOLS PAGES (existing, preserved)
# =============================================================================

def build_tools_hub(env, tools):
    """Build the Investor Tools hub page at /tools.html."""
    template = env.get_template("tools.html")
    grouped = group_tools_by_category(tools)

    html = template.render(
        tools=tools,
        grouped=grouped,
        page_title=f"Investor Tools - {config.SITE_NAME}",
        meta_description="Discover the best financial tools, stock screeners, portfolio trackers, and trading platforms for investors.",
        request_path="/tools.html",
    )

    output_path = config.OUTPUT_DIR / "tools.html"
    output_path.write_text(html)
    print(f"Built: tools.html ({len(tools)} tools)")


def build_category_pages(env, tools):
    """Build tool category listing pages."""
    template = env.get_template("category.html")
    grouped = group_tools_by_category(tools)

    for category in config.CATEGORIES:
        category_tools = grouped.get(category["slug"], [])
        category_tools.sort(key=lambda x: x.get("rating", 0), reverse=True)

        html = template.render(
            category=category,
            tools=category_tools,
            page_title=f"{category['name']} - Investor Tools - {config.SITE_NAME}",
            meta_description=category["description"],
            request_path=f"/category/{category['slug']}.html",
        )

        output_path = config.OUTPUT_DIR / "category" / f"{category['slug']}.html"
        output_path.write_text(html)
        print(f"Built: category/{category['slug']}.html ({len(category_tools)} tools)")


def build_tool_pages(env, tools):
    """Build individual tool detail pages."""
    template = env.get_template("tool.html")

    for tool in tools:
        related = []
        for t in tools:
            if t["slug"] != tool["slug"]:
                if any(cat in t.get("category", []) for cat in tool.get("category", [])):
                    related.append(t)
        related = related[:4]

        html = template.render(
            tool=tool,
            related_tools=related,
            page_title=f"{tool['name']} - Investor Tools - {config.SITE_NAME}",
            meta_description=tool.get("description", "")[:160],
            request_path=f"/tool/{tool['slug']}.html",
        )

        output_path = config.OUTPUT_DIR / "tool" / f"{tool['slug']}.html"
        output_path.write_text(html)
        print(f"Built: tool/{tool['slug']}.html")


# =============================================================================
# BUILD: BLOG
# =============================================================================

def build_blog_page(env, posts):
    """Build the blog listing page with category filtering."""
    template = env.get_template("blog.html")
    html = template.render(
        posts=posts,
        page_title=f"Blog - {config.SITE_NAME}",
        meta_description="Guides, tips, and resources to help you find the right financial advisor and make smart investment decisions.",
        request_path="/blog.html",
    )
    output_path = config.OUTPUT_DIR / "blog.html"
    output_path.write_text(html)
    print(f"Built: blog.html ({len(posts)} posts)")


def build_post_pages(env, posts):
    """Build individual blog post pages."""
    template = env.get_template("post.html")

    for post in posts:
        if not post.get("slug"):
            continue
        html = template.render(
            post=post,
            all_posts=posts,
            page_title=f"{post['title']} - {config.SITE_NAME}",
            meta_description=post.get("meta_description") or post.get("excerpt", "")[:160],
            page_image=post.get("featured_image", ""),
            request_path=f"/blog/{post['slug']}.html",
        )
        output_path = config.OUTPUT_DIR / "blog" / f"{post['slug']}.html"
        output_path.write_text(html)
        print(f"Built: blog/{post['slug']}.html")


# =============================================================================
# BUILD: SEARCH INDEX
# =============================================================================

def build_search_index(advisors):
    """Generate search-index.json for client-side search."""
    index = [
        {
            "name": a["name"],
            "city": a.get("city", ""),
            "state": a.get("state", ""),
            "slug": a["slug"],
            "specialties": a.get("specialties", []),
        }
        for a in advisors if a.get("name") and a.get("slug")
    ]
    output_path = config.OUTPUT_DIR / "search-index.json"
    with open(output_path, "w") as f:
        json.dump(index, f, ensure_ascii=False)
    print(f"Built: search-index.json ({len(index)} advisors)")


# =============================================================================
# BUILD: SITEMAP & SEO
# =============================================================================

def build_sitemap(tools, advisors, posts, indexed_states=None, indexed_cities=None):
    """Generate sitemap.xml — only includes indexable pages."""
    urls = [
        f"{config.SITE_URL}/",
        f"{config.SITE_URL}/tools.html",
        f"{config.SITE_URL}/blog.html",
        f"{config.SITE_URL}/about.html",
        f"{config.SITE_URL}/contact.html",
        f"{config.SITE_URL}/privacy.html",
        f"{config.SITE_URL}/terms.html",
    ]

    # State pages — only indexed ones
    if indexed_states:
        for state_slug in indexed_states:
            urls.append(f"{config.SITE_URL}/state/{state_slug}.html")
    else:
        for state in config.US_STATES:
            urls.append(f"{config.SITE_URL}/state/{state['slug']}.html")

    # City pages — only indexed ones
    if indexed_cities:
        for city_key in indexed_cities:
            urls.append(f"{config.SITE_URL}/state/{city_key}.html")
    else:
        cities_added = set()
        for advisor in advisors:
            state_slug = advisor.get("state_slug", "")
            city_slug = advisor.get("city_slug", "")
            if state_slug and city_slug:
                city_key = f"{state_slug}/{city_slug}"
                if city_key not in cities_added:
                    urls.append(f"{config.SITE_URL}/state/{state_slug}/{city_slug}.html")
                    cities_added.add(city_key)

    # Specialty pages
    for specialty in config.SPECIALTIES:
        urls.append(f"{config.SITE_URL}/specialty/{specialty['slug']}.html")

    # Advisor pages
    for advisor in advisors:
        urls.append(f"{config.SITE_URL}/advisor/{advisor['slug']}.html")

    # Tool category pages
    for category in config.CATEGORIES:
        urls.append(f"{config.SITE_URL}/category/{category['slug']}.html")

    # Tool pages
    for tool in tools:
        urls.append(f"{config.SITE_URL}/tool/{tool['slug']}.html")

    # Blog posts
    for post in posts:
        if post.get("slug"):
            urls.append(f"{config.SITE_URL}/blog/{post['slug']}.html")

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        sitemap += f"  <url><loc>{url}</loc></url>\n"
    sitemap += "</urlset>"

    output_path = config.OUTPUT_DIR / "sitemap.xml"
    output_path.write_text(sitemap)
    print(f"Built: sitemap.xml ({len(urls)} URLs)")


def build_robots():
    """Generate robots.txt."""
    robots = f"""User-agent: *
Allow: /

Sitemap: {config.SITE_URL}/sitemap.xml
"""
    output_path = config.OUTPUT_DIR / "robots.txt"
    output_path.write_text(robots)
    print("Built: robots.txt")


def copy_ads_txt():
    """Copy ads.txt to output directory."""
    ads_txt_path = Path("ads.txt")
    if ads_txt_path.exists():
        shutil.copy(ads_txt_path, config.OUTPUT_DIR / "ads.txt")
        print("Built: ads.txt")


# =============================================================================
# BUILD: STATIC PAGES
# =============================================================================

STATIC_PAGES = [
    {
        "template": "about.html",
        "output": "about.html",
        "title": "About Us",
        "description": f"Learn about {config.SITE_NAME} and our mission to help investors find trusted financial advisors.",
    },
    {
        "template": "privacy.html",
        "output": "privacy.html",
        "title": "Privacy Policy",
        "description": "Our privacy policy explains how we collect, use, and protect your information.",
    },
    {
        "template": "contact.html",
        "output": "contact.html",
        "title": "Contact Us",
        "description": f"Get in touch with {config.SITE_NAME} for questions, suggestions, or business inquiries.",
    },
    {
        "template": "terms.html",
        "output": "terms.html",
        "title": "Terms of Service",
        "description": f"Terms and conditions for using {config.SITE_NAME}.",
    },
    {
        "template": "success.html",
        "output": "success/index.html",
        "title": "Message Sent",
        "description": "Thank you for contacting us.",
    },
]


def build_static_pages(env, advisors=None):
    """Build static informational pages."""
    total_count = len(advisors) if advisors else 0
    for page in STATIC_PAGES:
        template = env.get_template(page["template"])
        html = template.render(
            page_title=f"{page['title']} - {config.SITE_NAME}",
            meta_description=page["description"],
            request_path=f"/{page['output']}",
            total_count=total_count,
        )
        output_path = config.OUTPUT_DIR / page["output"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
        print(f"Built: {page['output']}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main build process."""
    print(f"\n{'='*50}")
    print(f"Building {config.SITE_NAME}")
    print(f"{'='*50}\n")

    # Setup
    print("Setting up output directory...")
    setup_output_directory()

    # Get data
    print("\nFetching tools...")
    tools = get_tools()

    print("\nFetching advisors...")
    advisors = get_advisors()

    print("\nFetching blog posts...")
    posts = fetch_blog_posts()

    # Create Jinja environment
    env = create_jinja_env()

    # Build advisor directory pages
    print("\nBuilding pages...")
    build_homepage(env, tools, advisors, posts)
    indexed_states = build_state_pages(env, advisors)
    indexed_cities = build_city_pages(env, advisors)
    build_advisor_pages(env, advisors)
    build_specialty_pages(env, advisors)

    # Build tool pages (preserved from original site)
    build_tools_hub(env, tools)
    build_category_pages(env, tools)
    build_tool_pages(env, tools)

    # Build blog
    build_blog_page(env, posts)
    build_post_pages(env, posts)

    # Build static pages
    build_static_pages(env, advisors)

    # Build SEO files
    print("\nBuilding SEO files...")
    build_sitemap(tools, advisors, posts, indexed_states, indexed_cities)
    build_robots()
    copy_ads_txt()
    build_search_index(advisors)

    print(f"\n{'='*50}")
    print(f"Build complete! Output in: {config.OUTPUT_DIR}")
    print(f"{'='*50}")
    print(f"\nTo preview locally:")
    print(f"  cd {config.OUTPUT_DIR}")
    print(f"  python3 -m http.server 8000")
    print(f"  Open http://localhost:8000")


if __name__ == "__main__":
    main()
