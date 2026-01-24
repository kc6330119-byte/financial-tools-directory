# Financial Tools Directory - Claude Code Handoff

## Project Overview
Building a **Python-based static site generator** for a financial tools directory. Uses Airtable as CMS, generates static HTML via Jinja2 templates, and deploys to Netlify/Vercel for free hosting.

## Current Status
✅ Complete project structure created
✅ All Python code written (build.py, config.py)
✅ All Jinja2 templates created (4 HTML files)
✅ Documentation written (README, setup guides)
❌ **Issue**: ZIP file extraction problems on user's Mac
🎯 **Next Step**: Help user set up project in terminal with Claude Code

## User Context
- **Name**: Kevin
- **Role**: Service Reliability Engineer, ITIL 4 certified
- **Skills**: Strong Python background, works with vector DBs (ChromaDB), familiar with Docker
- **Projects**: Built TRCA RAG pipeline, stock analysis workflows with Alpha Vantage API
- **Comfort Level**: Very comfortable with Python, prefers it over JavaScript

## Project Architecture

### Tech Stack
- **Language**: Python 3.9+
- **Templates**: Jinja2
- **CMS**: Airtable (free tier: 1,000 records)
- **Styling**: Tailwind CSS (via CDN)
- **Hosting**: Netlify/Vercel (free tier)
- **Cost**: ~$12/year (just domain)

### Directory Structure
```
financial-tools-directory/
├── build.py              # Main build script - fetches from Airtable, generates static HTML
├── config.py             # Configuration (site name, categories, Airtable settings)
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # User's Airtable credentials (not in git)
├── .gitignore
├── README.md            # Complete documentation
├── QUICKSTART.md        # 15-minute setup guide
├── AIRTABLE_SETUP.md    # Detailed Airtable configuration
├── DEPLOYMENT.md        # Deploy to Netlify/Vercel
├── test_build.py        # Test build without Airtable
├── templates/           # Jinja2 HTML templates
│   ├── base.html       # Base layout with nav/footer
│   ├── index.html      # Homepage with featured tools
│   ├── category.html   # Category listing pages
│   └── tool.html       # Individual tool detail pages
├── static/              # Static assets
│   ├── css/
│   │   └── custom.css
│   └── js/
├── data/               # Local cache (optional)
└── dist/               # Generated static site (gitignored)
```

### Key Files Explained

**build.py** (Main build script):
- Fetches tools from Airtable API
- Falls back to sample data if no Airtable configured
- Generates static HTML pages using Jinja2 templates
- Creates sitemap.xml and robots.txt
- Outputs everything to `dist/` folder
- Sample data includes 3 tools (Alpha Vantage, TradingView, Yahoo Finance)

**config.py** (Site configuration):
- Site name, description, URL
- Airtable credentials (loaded from .env)
- Categories list (Stock Screeners, Portfolio Trackers, etc.)
- Output directories
- SEO settings

**templates/** (Jinja2 templates):
- Uses Tailwind CSS for styling
- Responsive design
- SEO-optimized with meta tags
- Clean, modern financial theme

### Python Dependencies
```
pyairtable==2.3.3      # Airtable Python SDK
jinja2==3.1.4          # Template engine
python-slugify==8.0.4  # URL-friendly slugs
python-dotenv==1.0.1   # Environment variables
markdown==3.6          # Markdown support (future)
pyyaml==6.0.1         # YAML config (future)
```

## Build Process Flow

1. **Initialize**: Load config, setup Jinja2 environment
2. **Fetch Data**: Get tools from Airtable (or use sample data)
3. **Process**: Group tools by category, sort by rating/date
4. **Generate Pages**:
   - Homepage (index.html) - featured tools, recent additions
   - Category pages (category/*.html) - filtered tool listings
   - Tool pages (tool/*.html) - individual tool details
5. **SEO Files**: Create sitemap.xml, robots.txt
6. **Output**: Everything goes to `dist/` folder

## Airtable Schema

### Tools Table Fields
| Field | Type | Purpose |
|-------|------|---------|
| Name | Single line text | Tool name |
| Description | Long text | Full description |
| Category | Multiple select | Stock Screeners, Portfolio Trackers, etc. |
| Pricing Model | Single select | Free, Freemium, Paid, Subscription |
| Price Range | Single line text | "$0", "$10-50/mo" |
| Website URL | URL | Main website |
| Logo URL | URL | Direct link to logo |
| Features | Multiple select | Key features list |
| Rating | Number | 0-5 scale |
| Review Count | Number | Number of reviews |
| API Available | Checkbox | Has API? |
| Mobile App | Checkbox | Has mobile app? |
| Data Sources | Multiple select | Real-time, Delayed, EOD |
| Target Audience | Multiple select | Beginners, Active Traders, etc. |
| Affiliate Link | URL | Optional affiliate URL |
| Status | Single select | Active, Featured, Draft |
| Date Added | Date | When added |

## Current Problem

**Issue**: User downloaded ZIP file but extraction didn't work properly
- Files might be nested in subdirectory
- User ran `pip3 install -r requirements.txt` but got "No such file"
- User is in directory: `~/Documents/Documents - Kevin's MacBook Pro/Projects/financial-tools-directory/`

## What User Needs from Claude Code

### Immediate Tasks
1. **Navigate to correct directory** and verify file structure
2. **Check if files are in nested subdirectory** (common ZIP issue)
3. **Set up project properly** if files are missing/misplaced
4. **Create virtual environment** and install dependencies
5. **Test build** with sample data (no Airtable needed initially)
6. **Preview site** locally

### Setup Commands (if files exist)
```bash
# Navigate to project
cd ~/Documents/Projects/financial-tools-directory

# Check structure
ls -la

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Test build (uses sample data)
python3 build.py

# Preview
cd dist
python3 -m http.server 8000
# Open http://localhost:8000
```

### If Files Are Missing
Claude Code should help recreate the project structure from scratch. All file contents are available in the outputs folder.

## Airtable Setup (Next Phase)

**After project works locally, user needs to**:
1. Create free Airtable account
2. Create "Financial Tools Directory" base
3. Add "Tools" table with fields listed above
4. Get API key and Base ID
5. Configure `.env` file
6. Add initial tools (20-30 to start)
7. Rebuild: `python3 build.py`

## Deployment (Final Phase)

**Recommended: Netlify**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Build site
python3 build.py

# Deploy
cd dist
netlify deploy --prod
```

**Alternative: Vercel**
```bash
npm install -g vercel
python3 build.py
vercel --prod
```

## File Locations in Current Session

All project files are available at:
- `/mnt/user-data/outputs/financial-tools-directory.zip` (28 KB)
- `/mnt/user-data/outputs/financial-tools-directory.tar.gz` (21 KB)
- Individual files also in `/mnt/user-data/outputs/`:
  - requirements.txt
  - config.py
  - build.py
  - .env.example
  - base.html, index.html, category.html, tool.html
  - README.md, AIRTABLE_SETUP.md, QUICKSTART.md

## Sample Data (Built-in)

The build script includes 3 sample tools that work without Airtable:
1. **Alpha Vantage** - Data provider (Featured)
2. **TradingView** - Technical analysis
3. **Yahoo Finance** - Portfolio tracker

This allows testing before Airtable is configured.

## Key Design Decisions

1. **Why Python over Next.js**: User is most comfortable with Python
2. **Why Airtable**: No database setup, visual CMS, free tier sufficient
3. **Why Static**: Fast, cheap, secure, easy to host
4. **Why Netlify**: Best free tier, easy deployment, build hooks for auto-updates

## Monetization Plan (Future)

- Google AdSense (high CPC for finance niche: $15-50)
- Affiliate links (stored in Airtable)
- Featured listings (tools pay to be highlighted)
- Email newsletter
- Sponsored content

## Success Metrics

**MVP Goals (Week 1)**:
- 30+ tools in directory
- All categories represented
- Site deployed and live
- Custom domain configured

**Month 1 Goals**:
- 100+ tools
- SEO optimization complete
- AdSense integrated
- First affiliate partnerships

## Important Notes

- User has experience with Alpha Vantage API (could integrate live data later)
- User familiar with Docker (could containerize later)
- User works on incident management - might add tool reliability ratings
- Strong Python skills mean easy to extend/customize

## Next Steps for Claude Code

1. Help user locate/fix ZIP extraction issue
2. Get project running locally with sample data
3. Walk through Airtable setup when ready
4. Assist with first deployment to Netlify
5. Help customize design/add features as needed

## Questions User Might Have

**"Can I add [feature]?"** - Yes! Python makes it easy to extend
**"How do I add more categories?"** - Edit `config.py` CATEGORIES list
**"Can I use a different database?"** - Yes, but Airtable is easiest to start
**"How often should I rebuild?"** - Daily auto-builds or after major updates
**"What about Docker?"** - Could containerize later, not needed initially

## Documentation Priority

1. **QUICKSTART.md** - Get running in 15 minutes
2. **AIRTABLE_SETUP.md** - Detailed Airtable configuration
3. **README.md** - Complete reference
4. **DEPLOYMENT.md** - Deploy to production

---

## Claude Code: Start Here

**First Command to Run**:
```bash
cd ~/Documents/Projects/financial-tools-directory
ls -la
```

This will show if files are properly extracted or in nested directory.

**Expected Output** (if correct):
```
total 64
-rw-r--r--  requirements.txt
-rw-r--r--  config.py
-rw-r--r--  build.py
-rw-r--r--  .env.example
drwxr-xr-x  templates/
drwxr-xr-x  static/
...
```

**If nested**, files will be in:
```
financial-tools-directory/financial-tools-directory/
```

Good luck! This is a well-structured project that should work smoothly once files are in place.
