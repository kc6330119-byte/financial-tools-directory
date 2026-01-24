# Financial Tools Directory

A Python-based static site generator for a financial tools directory. Uses Airtable as a CMS and generates static HTML that can be deployed to Netlify or Vercel.

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build site (uses sample data)
python build.py

# Preview locally
cd dist
python -m http.server 8000
# Open http://localhost:8000
```

## Project Structure

```
financial-tools-directory/
├── build.py              # Main build script
├── config.py             # Site configuration
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── templates/            # Jinja2 templates
│   ├── base.html         # Base layout
│   ├── index.html        # Homepage
│   ├── category.html     # Category pages
│   └── tool.html         # Tool detail pages
├── static/               # Static assets
│   └── css/custom.css
└── dist/                 # Generated site (gitignored)
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and fill in your Airtable credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
AIRTABLE_API_KEY=your_api_key
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_TABLE_NAME=Tools
```

### Site Settings

Edit `config.py` to customize:
- Site name and description
- Categories
- SEO settings
- Build settings

## Airtable Setup

1. Create a free Airtable account
2. Create a new base called "Financial Tools Directory"
3. Create a "Tools" table with these fields:
   - Name (Single line text)
   - Description (Long text)
   - Category (Multiple select)
   - Pricing Model (Single select: Free, Freemium, Paid, Subscription)
   - Price Range (Single line text)
   - Website URL (URL)
   - Logo URL (URL)
   - Features (Multiple select)
   - Rating (Number)
   - Review Count (Number)
   - API Available (Checkbox)
   - Mobile App (Checkbox)
   - Data Sources (Multiple select)
   - Target Audience (Multiple select)
   - Affiliate Link (URL)
   - Status (Single select: Active, Featured, Draft)
   - Date Added (Date)

4. Get your API key from https://airtable.com/create/tokens
5. Get your Base ID from the Airtable URL

## Deployment

### Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Build and deploy
python build.py
cd dist
netlify deploy --prod
```

### Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Build and deploy
python build.py
vercel --prod
```

## Adding Tools

### Without Airtable
Edit the `get_sample_data()` function in `build.py` to add more sample tools.

### With Airtable
1. Add tools to your Airtable base
2. Run `python build.py` to regenerate the site

## Categories

Default categories (edit in `config.py`):
- Stock Screeners
- Portfolio Trackers
- Technical Analysis
- Fundamental Analysis
- Data Providers
- Trading Platforms
- Research Tools
- News & Alerts

## License

MIT
