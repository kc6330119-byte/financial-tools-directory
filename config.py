"""
Configuration for Financial Tools Directory
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "dist"

# Site Configuration
SITE_NAME = "Financial Tools Directory"
SITE_DESCRIPTION = "Discover the best financial tools, stock screeners, portfolio trackers, and trading platforms."
SITE_URL = os.getenv("SITE_URL", "https://financialtools.directory")
SITE_AUTHOR = "Financial Tools Directory"

# Airtable Configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Tools")

# Categories
CATEGORIES = [
    {"name": "Stock Screeners", "slug": "stock-screeners", "description": "Filter and find stocks based on your criteria"},
    {"name": "Portfolio Trackers", "slug": "portfolio-trackers", "description": "Track your investments across accounts"},
    {"name": "Technical Analysis", "slug": "technical-analysis", "description": "Chart patterns and technical indicators"},
    {"name": "Fundamental Analysis", "slug": "fundamental-analysis", "description": "Financial statements and valuation metrics"},
    {"name": "Data Providers", "slug": "data-providers", "description": "APIs and data feeds for financial data"},
    {"name": "Trading Platforms", "slug": "trading-platforms", "description": "Execute trades and manage orders"},
    {"name": "Research Tools", "slug": "research-tools", "description": "In-depth research and analysis"},
    {"name": "News & Alerts", "slug": "news-alerts", "description": "Financial news and price alerts"},
]

# Pricing Models
PRICING_MODELS = ["Free", "Freemium", "Paid", "Subscription"]

# SEO Settings
DEFAULT_META_TITLE = f"{SITE_NAME} - Best Financial Tools & Software"
DEFAULT_META_DESCRIPTION = SITE_DESCRIPTION

# Build Settings
ITEMS_PER_PAGE = 20
FEATURED_COUNT = 6
RECENT_COUNT = 8
