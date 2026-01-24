#!/usr/bin/env python3
"""
Financial Tools Directory - Static Site Generator

Fetches tools from Airtable and generates a static HTML site.
Falls back to sample data if Airtable is not configured.
"""
import os
import shutil
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from slugify import slugify

import config


def get_sample_data():
    """Return sample tools for testing without Airtable."""
    return [
        {
        'template': 'success.html',
        'output': 'success/index.html',
        'title': 'Message Sent',
        'description': 'Thank you for contacting us.',
    },
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
        'template': 'success.html',
        'output': 'success/index.html',
        'title': 'Message Sent',
        'description': 'Thank you for contacting us.',
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
        'template': 'success.html',
        'output': 'success/index.html',
        'title': 'Message Sent',
        'description': 'Thank you for contacting us.',
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


def fetch_from_airtable():
    """Fetch tools from Airtable API."""
    if not config.AIRTABLE_API_KEY or not config.AIRTABLE_BASE_ID:
        print("Airtable not configured. Using sample data.")
        return None

    try:
        from pyairtable import Api

        api = Api(config.AIRTABLE_API_KEY)
        table = api.table(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME)
        records = table.all()

        tools = []
        for record in records:
            fields = record.get("fields", {})

            # Skip drafts
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

        print(f"Fetched {len(tools)} tools from Airtable.")
        return tools

    except Exception as e:
        print(f"Error fetching from Airtable: {e}")
        return None


def get_tools():
    """Get tools from Airtable or fall back to sample data."""
    tools = fetch_from_airtable()
    if tools is None:
        tools = get_sample_data()
        print(f"Using {len(tools)} sample tools.")
    return tools


def setup_output_directory():
    """Create clean output directory."""
    if config.OUTPUT_DIR.exists():
        shutil.rmtree(config.OUTPUT_DIR)

    config.OUTPUT_DIR.mkdir(parents=True)
    (config.OUTPUT_DIR / "category").mkdir()
    (config.OUTPUT_DIR / "tool").mkdir()

    # Copy static files
    if config.STATIC_DIR.exists():
        shutil.copytree(config.STATIC_DIR, config.OUTPUT_DIR / "static")


def create_jinja_env():
    """Create Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(config.TEMPLATES_DIR),
        autoescape=True
    )

    # Add custom filters
    env.filters["slugify"] = slugify

    # Add global variables
    env.globals["site_name"] = config.SITE_NAME
    env.globals["site_url"] = config.SITE_URL
    env.globals["site_description"] = config.SITE_DESCRIPTION
    env.globals["categories"] = config.CATEGORIES
    env.globals["current_year"] = datetime.now().year

    return env


def group_tools_by_category(tools):
    """Group tools by their categories."""
    grouped = {cat["slug"]: [] for cat in config.CATEGORIES}

    for tool in tools:
        for category_name in tool.get("category", []):
            category_slug = slugify(category_name)
            if category_slug in grouped:
                grouped[category_slug].append(tool)

    return grouped


def build_homepage(env, tools):
    """Build the homepage."""
    template = env.get_template("index.html")

    # Get featured tools
    featured = [t for t in tools if t.get("status") == "Featured"][:config.FEATURED_COUNT]

    # Get recent tools (sorted by date)
    recent = sorted(
        tools,
        key=lambda x: x.get("date_added", ""),
        reverse=True
    )[:config.RECENT_COUNT]

    html = template.render(
        featured_tools=featured,
        recent_tools=recent,
        all_tools=tools,
        page_title=config.DEFAULT_META_TITLE,
        meta_description=config.DEFAULT_META_DESCRIPTION,
    )

    output_path = config.OUTPUT_DIR / "index.html"
    output_path.write_text(html)
    print(f"Built: index.html")


def build_category_pages(env, tools):
    """Build category listing pages."""
    template = env.get_template("category.html")
    grouped = group_tools_by_category(tools)

    for category in config.CATEGORIES:
        category_tools = grouped.get(category["slug"], [])

        # Sort by rating
        category_tools.sort(key=lambda x: x.get("rating", 0), reverse=True)

        html = template.render(
            category=category,
            tools=category_tools,
            page_title=f"{category['name']} - {config.SITE_NAME}",
            meta_description=category["description"],
        )

        output_path = config.OUTPUT_DIR / "category" / f"{category['slug']}.html"
        output_path.write_text(html)
        print(f"Built: category/{category['slug']}.html ({len(category_tools)} tools)")


def build_tool_pages(env, tools):
    """Build individual tool detail pages."""
    template = env.get_template("tool.html")

    for tool in tools:
        # Find related tools (same category, different tool)
        related = []
        for t in tools:
            if t["slug"] != tool["slug"]:
                if any(cat in t.get("category", []) for cat in tool.get("category", [])):
                    related.append(t)
        related = related[:4]  # Limit to 4 related tools

        html = template.render(
            tool=tool,
            related_tools=related,
            page_title=f"{tool['name']} - {config.SITE_NAME}",
            meta_description=tool.get("description", "")[:160],
        )

        output_path = config.OUTPUT_DIR / "tool" / f"{tool['slug']}.html"
        output_path.write_text(html)
        print(f"Built: tool/{tool['slug']}.html")


def build_sitemap(tools):
    """Generate sitemap.xml."""
    urls = [
        f"{config.SITE_URL}/about.html",
        f"{config.SITE_URL}/privacy.html",
        f"{config.SITE_URL}/contact.html",
        f"{config.SITE_URL}/terms.html",
        f"{config.SITE_URL}/",
    ]

    # Category pages
    for category in config.CATEGORIES:
        urls.append(f"{config.SITE_URL}/category/{category['slug']}.html")

    # Tool pages
    for tool in tools:
        urls.append(f"{config.SITE_URL}/tool/{tool['slug']}.html")

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for url in urls:
        sitemap += f"  <url><loc>{url}</loc></url>\n"

    sitemap += "</urlset>"

    output_path = config.OUTPUT_DIR / "sitemap.xml"
    output_path.write_text(sitemap)
    print("Built: sitemap.xml")


def build_robots():
    """Generate robots.txt."""
    robots = f"""User-agent: *
Allow: /

Sitemap: {config.SITE_URL}/sitemap.xml
"""

    output_path = config.OUTPUT_DIR / "robots.txt"
    output_path.write_text(robots)
    print("Built: robots.txt")



# Static pages configuration
STATIC_PAGES = [
    {
        'template': 'about.html',
        'output': 'about.html',
        'title': 'About Us',
        'description': 'Learn about Financial Tools Directory and our mission to help investors find the best tools.',
    },
    {
        'template': 'privacy.html',
        'output': 'privacy.html',
        'title': 'Privacy Policy',
        'description': 'Our privacy policy explains how we collect, use, and protect your information.',
    },
    {
        'template': 'contact.html',
        'output': 'contact.html',
        'title': 'Contact Us',
        'description': 'Get in touch with Financial Tools Directory for questions, suggestions, or business inquiries.',
    },
    {
        'template': 'terms.html',
        'output': 'terms.html',
        'title': 'Terms of Service',
        'description': 'Terms and conditions for using Financial Tools Directory.',
    },
    {
        'template': 'success.html',
        'output': 'success/index.html',
        'title': 'Message Sent',
        'description': 'Thank you for contacting us.',
    },
]


def build_static_pages(env):
    """Build static informational pages."""
    for page in STATIC_PAGES:
        template = env.get_template(page['template'])
        html = template.render(
            page_title=f"{page['title']} - {config.SITE_NAME}",
            meta_description=page['description'],
        )
        output_path = config.OUTPUT_DIR / page['output']
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
        print(f"Built: {page['output']}")

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

    # Create Jinja environment
    env = create_jinja_env()

    # Build pages
    print("\nBuilding pages...")
    build_homepage(env, tools)
    build_category_pages(env, tools)
    build_tool_pages(env, tools)
    build_static_pages(env)

    # Build SEO files
    print("\nBuilding SEO files...")
    build_sitemap(tools)
    build_robots()

    print(f"\n{'='*50}")
    print(f"Build complete! Output in: {config.OUTPUT_DIR}")
    print(f"{'='*50}")
    print(f"\nTo preview locally:")
    print(f"  cd {config.OUTPUT_DIR}")
    print(f"  python3 -m http.server 8000")
    print(f"  Open http://localhost:8000")


if __name__ == "__main__":
    main()
