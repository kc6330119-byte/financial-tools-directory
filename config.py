"""
Configuration for Investment Advisor Directory (formerly Financial Tools Directory)
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
CONTENT_DIR = BASE_DIR / "content"

# Site Configuration
SITE_NAME = "Smart Investor"  # Hardcoded — do not use os.getenv, Netlify overrides SITE_NAME with its internal site ID
SITE_DESCRIPTION = "Find a trusted investment advisor near you. Compare credentials, fee structures, and specialties. Browse fiduciary financial advisors by state and city."
SITE_URL = os.getenv("SITE_URL", "https://smart-investor-financial-tools.com")
SITE_AUTHOR = "Smart Investor"

# Airtable Configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Tools")
AIRTABLE_ADVISORS_TABLE_NAME = os.getenv("AIRTABLE_ADVISORS_TABLE_NAME", "Advisors")
AIRTABLE_BLOG_TABLE_NAME = os.getenv("AIRTABLE_BLOG_TABLE_NAME", "Blog Posts")

# Google Analytics
GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "")

# =============================================================================
# INVESTMENT TOOLS (existing — preserved from original site)
# =============================================================================

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

PRICING_MODELS = ["Free", "Freemium", "Paid", "Subscription"]

# =============================================================================
# ADVISOR DIRECTORY
# =============================================================================

# Minimum advisors for a state/city page to be indexed by search engines
MIN_ADVISORS_FOR_INDEX = 3

# US States + DC for state-based pages
US_STATES = [
    {"name": "Alabama", "slug": "alabama", "abbr": "AL", "description": "Alabama's investment landscape is shaped by a favorable tax climate — the state does not tax Social Security benefits and offers deductions on certain retirement income. Birmingham and Huntsville are the primary financial services hubs, with a growing number of independent RIAs serving Mobile, Montgomery, and Auburn. Alabama investors benefit from a lower cost of living that allows retirement savings to stretch further, and local advisors often specialize in retirement income planning for state employees and military families near Redstone Arsenal."},
    {"name": "Alaska", "slug": "alaska", "abbr": "AK", "description": "Alaska stands out as one of the most tax-friendly states for investors — no state income tax, no state sales tax, and no tax on Social Security or retirement income. Anchorage and Fairbanks are home to most of the state's financial advisory firms. The Alaska Permanent Fund Dividend adds a unique planning dimension, and advisors here often specialize in helping oil industry workers, military families, and federal employees with retirement transitions and resource-based wealth management."},
    {"name": "Arizona", "slug": "arizona", "abbr": "AZ", "description": "Arizona is a top retirement destination with a rapidly growing population of high-net-worth retirees in Phoenix, Scottsdale, Tucson, and Sun City. The state has a flat income tax rate and does not tax Social Security benefits. Arizona's financial advisory market is competitive, with hundreds of RIAs and wealth management firms. Advisors here frequently specialize in retirement income distribution, real estate investment planning, and tax-efficient strategies for retirees relocating from higher-tax states like California and Illinois."},
    {"name": "Arkansas", "slug": "arkansas", "abbr": "AR", "description": "Arkansas offers a moderate tax environment with partial exemptions on retirement income and Social Security benefits. Little Rock, Fayetteville, and Bentonville (home to Walmart's corporate influence) are the main financial services centers. The state's lower cost of living makes it attractive for retirees, and local advisors often focus on retirement planning for state employees, small business succession, and agricultural wealth management in the Delta and Ozark regions."},
    {"name": "California", "slug": "california", "abbr": "CA", "description": "California has the largest concentration of registered investment advisors in the nation, centered in Los Angeles, San Francisco, San Diego, and Silicon Valley. The state's high income tax rates (up to 13.3%) make tax-efficient investing a top priority. California advisors frequently specialize in equity compensation planning for tech workers, real estate portfolio management, venture capital wealth transitions, and cross-border planning for the state's diverse international communities. The California Department of Financial Protection and Innovation oversees state-registered advisors."},
    {"name": "Colorado", "slug": "colorado", "abbr": "CO", "description": "Colorado's Front Range corridor — Denver, Boulder, Colorado Springs, and Fort Collins — hosts a thriving financial advisory community serving the state's educated, active population. Colorado partially taxes retirement income but exempts Social Security benefits for most filers. The state's booming tech sector and outdoor lifestyle attract younger investors interested in ESG investing, FIRE planning, and equity compensation strategies. Mountain resort communities also have advisors specializing in second-home and vacation property planning."},
    {"name": "Connecticut", "slug": "connecticut", "abbr": "CT", "description": "Connecticut's financial advisory market is among the most sophisticated in the country, anchored by the hedge fund corridor in Greenwich and Stamford and the insurance industry in Hartford. The state has high income taxes and estate taxes, making tax planning and wealth preservation critical. Connecticut advisors often specialize in executive compensation, concentrated stock positions, estate planning for high-net-worth families, and insurance-based strategies. Many firms serve clients commuting to New York City's financial district."},
    {"name": "Delaware", "slug": "delaware", "abbr": "DE", "description": "Delaware's tax-friendly trust laws and absence of sales tax make it a strategic location for wealth planning. Wilmington's banking industry creates a concentration of financial professionals, and advisors here often specialize in trust and estate planning, corporate executive benefits, and tax-efficient investment structures. Delaware does not tax Social Security benefits and offers partial exclusions on other retirement income, benefiting the state's retirees in beach communities like Rehoboth and Lewes."},
    {"name": "District of Columbia", "slug": "district-of-columbia", "abbr": "DC", "description": "Washington, D.C. has a high concentration of financial advisors serving federal employees, government contractors, military officers, and diplomatic personnel. The District's advisory market specializes in federal retirement benefits (FERS/CSRS), Thrift Savings Plan optimization, and security-clearance-sensitive financial planning. D.C. has its own income tax and estate tax, and advisors frequently coordinate with Virginia and Maryland planning for clients living and working across state lines."},
    {"name": "Florida", "slug": "florida", "abbr": "FL", "description": "Florida is the nation's premier retirement state and one of the largest markets for financial advisory services. With no state income tax, no estate tax, and no inheritance tax, Florida attracts wealthy retirees and their assets from across the country. Miami, Palm Beach, Naples, Tampa, and Jacksonville all have dense concentrations of wealth management firms and independent RIAs. Florida advisors specialize in retirement income planning, estate planning for snowbirds, international wealth management (particularly Latin American clients in South Florida), and navigating the state's unique homestead exemption for asset protection."},
    {"name": "Georgia", "slug": "georgia", "abbr": "GA", "description": "Georgia's financial services sector is anchored by Atlanta, one of the South's major wealth management hubs. The state partially taxes retirement income and Social Security benefits. Savannah, Augusta, and the north Georgia mountains also have growing advisory communities. Atlanta advisors frequently serve executives at the city's Fortune 500 companies (Coca-Cola, Delta, Home Depot, UPS) with equity compensation, deferred comp, and concentrated stock strategies. Georgia's growing tech corridor also brings demand for startup equity and RSU planning."},
    {"name": "Hawaii", "slug": "hawaii", "abbr": "HI", "description": "Hawaii's unique island economy and high cost of living create specialized financial planning needs. Honolulu and Maui host most of the state's advisory firms. Hawaii has relatively high income taxes and taxes most retirement income, making tax-efficient investing important. Advisors here specialize in military family financial planning (given the large military presence), real estate investment in Hawaii's constrained market, and retirement planning for workers in tourism and government — the state's two largest employment sectors."},
    {"name": "Idaho", "slug": "idaho", "abbr": "ID", "description": "Idaho's rapidly growing population, especially in the Boise-Meridian metro area, has expanded its financial advisory market. The state taxes income at a flat rate but does not tax Social Security benefits. Many newcomers relocating from California, Oregon, and Washington bring substantial assets and need advisors experienced in cross-state tax planning. Local advisors also serve Idaho's agricultural community and the growing tech presence in the Treasure Valley with specialized wealth management strategies."},
    {"name": "Illinois", "slug": "illinois", "abbr": "IL", "description": "Illinois has one of the largest financial advisory markets in the Midwest, centered in Chicago's financial district and North Shore suburbs. The state's flat income tax rate applies to retirement income, but Illinois does not tax Social Security, pension, or 401(k)/IRA distributions — a significant benefit for retirees. Chicago advisors serve a broad client base from commodities traders to corporate executives, while downstate advisors in Springfield and Champaign often specialize in state employee retirement planning and agricultural wealth."},
    {"name": "Indiana", "slug": "indiana", "abbr": "IN", "description": "Indiana offers a relatively low flat income tax and does not tax Social Security benefits, making it moderately tax-friendly for retirees. Indianapolis is the state's financial services hub, with growing advisory markets in Fort Wayne, South Bend, and Carmel. Indiana advisors often specialize in retirement planning for manufacturing and pharmaceutical industry workers (Eli Lilly, Cummins), small business succession, and conservative income-focused investment strategies suited to the state's Midwest values."},
    {"name": "Iowa", "slug": "iowa", "abbr": "IA", "description": "Iowa recently transitioned to a flat income tax rate and fully exempts retirement income including Social Security, pensions, and 401(k)/IRA distributions. Des Moines — a national insurance and financial services hub — has a strong concentration of advisors and wealth managers. Cedar Rapids, Iowa City, and the Quad Cities also have active advisory communities. Iowa advisors frequently specialize in agricultural estate planning, farm succession, insurance-linked investment strategies, and retirement planning for education and healthcare professionals."},
    {"name": "Kansas", "slug": "kansas", "abbr": "KS", "description": "Kansas taxes most retirement income including Social Security benefits for higher earners, creating demand for tax-efficient planning. Overland Park and the Kansas City metro area host most of the state's financial advisory firms, with Wichita as a secondary hub. Kansas advisors often serve the aviation and energy industries (Koch Industries, Spirit AeroSystems) and specialize in corporate retirement plan optimization, oil and gas wealth management, and cross-border planning for clients living on the Kansas-Missouri state line."},
    {"name": "Kentucky", "slug": "kentucky", "abbr": "KY", "description": "Kentucky exempts Social Security benefits from state income tax and offers partial exclusions on other retirement income. Louisville and Lexington are the main advisory markets, with growing services in Northern Kentucky near Cincinnati. Kentucky advisors specialize in retirement planning for state government employees, bourbon industry wealth management, equine industry estate planning, and healthcare system retirees. The state's affordable cost of living makes it increasingly attractive for retirees from higher-cost neighboring states."},
    {"name": "Louisiana", "slug": "louisiana", "abbr": "LA", "description": "Louisiana does not tax Social Security benefits and offers favorable treatment of other retirement income. New Orleans, Baton Rouge, and Shreveport are the primary advisory markets. Louisiana advisors frequently specialize in oil and gas wealth management, estate planning for family-owned businesses, and navigating the state's unique community property laws (one of only nine community property states). The state's energy sector creates cyclical wealth that requires specialized income smoothing and diversification strategies."},
    {"name": "Maine", "slug": "maine", "abbr": "ME", "description": "Maine taxes retirement income and has a relatively high income tax rate, making tax planning important for retirees. Portland and Bangor host most of the state's advisory firms. Maine's aging population — the oldest median age in the country — drives strong demand for retirement income distribution, long-term care planning, and estate planning. Advisors here often serve seasonal residents who split time between Maine and Florida, requiring multi-state tax coordination."},
    {"name": "Maryland", "slug": "maryland", "abbr": "MD", "description": "Maryland's proximity to Washington, D.C. creates a large market of federal employees, military officers, and government contractors seeking financial advice. Bethesda, Rockville, Baltimore, and Annapolis host numerous advisory firms. Maryland taxes retirement income but offers significant pension exclusions for retirees. Advisors specialize in federal benefits optimization (FERS, TSP, FEHB), military retirement transitions, Social Security coordination, and estate planning given Maryland's estate tax with a lower exemption threshold than the federal level."},
    {"name": "Massachusetts", "slug": "massachusetts", "abbr": "MA", "description": "Massachusetts has one of the most concentrated financial advisory markets in the nation, anchored by Boston's asset management industry (Fidelity, Putnam, State Street). The state's flat income tax applies to most retirement income but exempts Social Security benefits. Boston and Cambridge advisors serve the biotech and technology sectors with equity compensation expertise, while firms across the state handle estate planning under Massachusetts' estate tax (threshold well below federal level). The state's highly educated population demands sophisticated planning."},
    {"name": "Michigan", "slug": "michigan", "abbr": "MI", "description": "Michigan offers favorable retirement income tax treatment, exempting most pension and retirement account income for qualifying seniors. Detroit, Ann Arbor, Grand Rapids, and Troy are the main advisory hubs. Michigan advisors frequently specialize in automotive industry retirement planning (GM, Ford, Stellantis pension optimization), real estate investment in the state's recovering markets, and small business succession planning. The state's manufacturing heritage means many clients have defined benefit pensions requiring complex distribution strategies."},
    {"name": "Minnesota", "slug": "minnesota", "abbr": "MN", "description": "Minnesota has higher income tax rates that apply to most retirement income, making tax-efficient planning critical. Minneapolis-St. Paul is a major financial services center (U.S. Bank, Ameriprise, Thrivent) with a dense advisory market. Rochester (home to Mayo Clinic) and Duluth also have active advisory communities. Minnesota advisors specialize in corporate executive compensation, healthcare professional planning, and ESG/socially responsible investing — reflecting the state's culturally progressive investor base."},
    {"name": "Mississippi", "slug": "mississippi", "abbr": "MS", "description": "Mississippi does not tax Social Security benefits and exempts most other retirement income from state taxation, making it one of the more tax-friendly states for retirees. Jackson, Gulfport, and Oxford host most advisory firms. The state's lower cost of living allows retirement savings to stretch significantly further than in coastal states. Mississippi advisors often specialize in retirement planning for military families (Keesler AFB, Columbus AFB), state employee pensions, and conservative income-focused strategies."},
    {"name": "Missouri", "slug": "missouri", "abbr": "MO", "description": "Missouri partially taxes Social Security benefits and retirement income, with increasing exemptions for seniors. St. Louis and Kansas City are major financial advisory markets, with Springfield and Columbia as secondary hubs. Edward Jones, headquartered in St. Louis, gives the state an outsized presence in financial services. Missouri advisors serve a diverse client base including Anheuser-Busch and Bayer retirees, small business owners, and agricultural families in the state's rural regions."},
    {"name": "Montana", "slug": "montana", "abbr": "MT", "description": "Montana has no state sales tax and recently reduced its income tax rates. The state does not tax Social Security benefits. Billings, Missoula, and Bozeman — the latter a rapidly growing destination for wealthy relocators — are the main advisory markets. Montana advisors specialize in ranch and agricultural estate planning, retirement planning for resource industry workers, and wealth management for the growing population of high-net-worth individuals moving to the state for its lifestyle and tax advantages."},
    {"name": "Nebraska", "slug": "nebraska", "abbr": "NE", "description": "Nebraska is phasing out its Social Security income tax and offers moderate treatment of other retirement income. Omaha — home to Berkshire Hathaway and a strong financial services sector — is the state's advisory hub, with Lincoln as a secondary market. Nebraska advisors serve the state's agricultural community with farm succession and estate planning, Berkshire Hathaway shareholders with concentrated stock strategies, and insurance industry professionals with complex compensation planning."},
    {"name": "Nevada", "slug": "nevada", "abbr": "NV", "description": "Nevada's absence of state income tax makes it one of the most attractive states for investors and retirees. Las Vegas, Reno, and Henderson host a large and growing financial advisory market serving high-net-worth relocators from California and other high-tax states. Nevada advisors specialize in tax-efficient relocation strategies, asset protection planning (Nevada has strong trust laws), real estate portfolio management, and entertainment industry wealth management. The state's favorable trust and estate laws also attract dynasty trust planning."},
    {"name": "New Hampshire", "slug": "new-hampshire", "abbr": "NH", "description": "New Hampshire has no state income tax on earned income (it recently eliminated the interest and dividends tax as well), making it extremely attractive for investors and retirees. Manchester, Nashua, and Concord host most advisory firms, with many clients commuting to Boston. New Hampshire advisors specialize in cross-border planning with Massachusetts, tax-efficient portfolio construction, and retirement planning for technology and defense industry workers in the southern tier."},
    {"name": "New Jersey", "slug": "new-jersey", "abbr": "NJ", "description": "New Jersey's high income taxes, property taxes, and estate tax create significant demand for tax-efficient financial planning. The state has one of the densest advisory markets in the country, particularly in Bergen County, Morris County, and along the Route 1 corridor. New Jersey advisors specialize in executive compensation for NYC commuters, pharmaceutical industry equity plans (J&J, Merck, Bristol-Myers Squibb), estate tax mitigation (NJ estate tax threshold is below federal), and retirement relocation strategies to lower-tax states."},
    {"name": "New Mexico", "slug": "new-mexico", "abbr": "NM", "description": "New Mexico recently exempted Social Security benefits from state taxation and offers favorable treatment of retirement income for seniors. Albuquerque, Santa Fe, and Las Cruces host most of the state's advisory firms. New Mexico's diverse population includes significant military and federal communities (Kirtland AFB, Los Alamos, Sandia Labs). Advisors specialize in federal employee retirement planning, TSP optimization, and retirement income strategies for the state's growing retiree population drawn by its low cost of living and cultural attractions."},
    {"name": "New York", "slug": "new-york", "abbr": "NY", "description": "New York has one of the world's largest concentrations of financial advisors, centered in Manhattan, Westchester County, and Long Island. Upstate markets include Albany, Buffalo, and Rochester. New York's high state and city income taxes (up to 14.8% combined in NYC) make tax planning paramount. The state exempts Social Security and up to $20,000 of pension income. New York advisors serve Wall Street professionals, corporate executives, entertainers, and entrepreneurs with complex compensation, estate planning (NY estate tax cliff), concentrated stock, and philanthropic strategies."},
    {"name": "North Carolina", "slug": "north-carolina", "abbr": "NC", "description": "North Carolina's flat income tax rate and full taxation of retirement income (Social Security is exempt) create a moderate tax environment for investors. Charlotte — the nation's second-largest banking center — Raleigh-Durham's Research Triangle, and Asheville's retirement communities are the major advisory markets. Charlotte advisors specialize in banking and financial services executive compensation. Triangle advisors serve tech, biotech, and university communities. Asheville advisors focus on retirement income planning for relocating retirees."},
    {"name": "North Dakota", "slug": "north-dakota", "abbr": "ND", "description": "North Dakota has low income tax rates and follows federal treatment of Social Security benefits. Fargo, Bismarck, and Grand Forks host the state's advisory community. North Dakota advisors specialize in oil and gas wealth management (Bakken formation), agricultural estate planning, and retirement planning for state employees and healthcare professionals. The state's energy booms and busts create cyclical wealth that requires careful diversification and income smoothing strategies."},
    {"name": "Ohio", "slug": "ohio", "abbr": "OH", "description": "Ohio does not tax Social Security benefits and offers a credit for other retirement income. Columbus, Cleveland, Cincinnati, and Dayton are major advisory markets. Ohio's diverse economy — from banking in Cincinnati to healthcare in Cleveland to tech in Columbus — creates varied advisory specializations. Ohio advisors serve P&G, Kroger, and Cardinal Health executives with equity compensation planning, and the state's many public pension systems (OPERS, STRS, SERS) drive demand for pension optimization expertise."},
    {"name": "Oklahoma", "slug": "oklahoma", "abbr": "OK", "description": "Oklahoma exempts Social Security benefits from state tax and offers partial exclusions on retirement income. Oklahoma City and Tulsa are the primary advisory markets. The state's energy sector (Devon Energy, Continental Resources, Williams Companies) creates significant wealth management demand. Oklahoma advisors specialize in oil and gas asset management, tribal enterprise financial planning, and retirement strategies for energy industry workers navigating boom-and-bust cycles."},
    {"name": "Oregon", "slug": "oregon", "abbr": "OR", "description": "Oregon has no state sales tax but relatively high income tax rates that apply to most retirement income, including Social Security for higher earners. Portland, Eugene, Salem, and Bend host the state's advisory market. Oregon advisors specialize in tax-efficient investing for the state's tech workers (Intel, Nike), sustainable and ESG investing (reflecting Oregon's environmentally conscious culture), and retirement planning for state employees covered by PERS, one of the nation's most generous public pension systems."},
    {"name": "Pennsylvania", "slug": "pennsylvania", "abbr": "PA", "description": "Pennsylvania does not tax retirement income (including Social Security, pensions, and retirement account distributions) for retirees, making it surprisingly tax-friendly despite its income tax on earned income. Philadelphia and Pittsburgh are major advisory markets, with growing services in the Lehigh Valley, King of Prussia, and State College. Philadelphia advisors serve healthcare, pharmaceutical (Comcast, AmerisourceBergen), and financial sector executives. Pittsburgh's revitalized tech sector brings demand for startup equity and RSU planning."},
    {"name": "Rhode Island", "slug": "rhode-island", "abbr": "RI", "description": "Rhode Island offers Social Security tax exemptions for qualifying residents and has been reducing its income tax rates. Providence and Newport host most of the state's advisory firms. Rhode Island advisors specialize in estate planning (the state has its own estate tax), retirement income planning for the state's healthcare and education sectors, and wealth management for the state's yachting and coastal communities. Many advisors also serve clients with connections to nearby Boston and Connecticut."},
    {"name": "South Carolina", "slug": "south-carolina", "abbr": "SC", "description": "South Carolina's favorable tax treatment of retirement income — Social Security is fully exempt, and there's a substantial deduction on other retirement income — makes it a popular retirement destination. Charleston, Greenville, Columbia, and Hilton Head/Bluffton are the main advisory markets. South Carolina advisors specialize in retirement relocation planning (many clients move from the Northeast), military retirement (Fort Jackson, Shaw AFB), and real estate-heavy portfolio management in the state's booming coastal and suburban markets."},
    {"name": "South Dakota", "slug": "south-dakota", "abbr": "SD", "description": "South Dakota has no state income tax, no estate tax, and some of the nation's most favorable trust laws — making it a premier jurisdiction for wealth planning. Sioux Falls is the state's financial services hub, home to major bank card operations and a growing advisory market. South Dakota's dynasty trust provisions attract wealthy families nationwide. Local advisors specialize in trust administration, agricultural estate planning, and wealth management for the state's banking and healthcare professionals."},
    {"name": "Tennessee", "slug": "tennessee", "abbr": "TN", "description": "Tennessee has no state income tax on wages or salary (it recently eliminated the Hall Tax on investment income as well), making it one of the most tax-friendly states for investors. Nashville, Memphis, Knoxville, and Chattanooga are the primary advisory markets. Nashville's booming economy and healthcare industry (HCA, Community Health Systems) drive strong demand for advisory services. Tennessee advisors specialize in healthcare executive compensation, entertainment and music industry wealth management, and tax-efficient strategies for relocating retirees."},
    {"name": "Texas", "slug": "texas", "abbr": "TX", "description": "Texas has no state income tax, making it one of the largest and most competitive financial advisory markets in the country. Houston, Dallas-Fort Worth, Austin, and San Antonio all have dense concentrations of wealth management firms and independent RIAs. Texas advisors specialize in energy sector wealth management (Exxon, Chevron, EOG Resources), tech executive equity compensation (Austin's booming tech scene), real estate portfolio management, and cross-border planning for clients with Mexico business interests. The state's rapid population growth from domestic migration brings constant demand for relocation-based financial planning."},
    {"name": "Utah", "slug": "utah", "abbr": "UT", "description": "Utah's flat income tax rate applies to all retirement income including Social Security, though a tax credit offsets some burden for lower-income retirees. Salt Lake City, Provo, and St. George are the main advisory markets. Utah's younger-than-average population and strong tech sector (Silicon Slopes) create demand for growth-oriented financial planning. Advisors specialize in tech equity compensation, large family financial planning, retirement strategies for LDS Church employees, and real estate investment in the state's rapidly appreciating markets."},
    {"name": "Vermont", "slug": "vermont", "abbr": "VT", "description": "Vermont has relatively high income tax rates and taxes most retirement income, including Social Security for higher earners. Burlington and Montpelier host the state's advisory community. Vermont's aging population — second-oldest median age in the nation — drives strong demand for retirement income planning, long-term care planning, and estate strategies. Vermont advisors often serve seasonal residents, small business owners, and retirees who value the state's quality of life and are willing to accept higher taxes for the lifestyle."},
    {"name": "Virginia", "slug": "virginia", "abbr": "VA", "description": "Virginia's financial advisory market benefits from the massive federal workforce in Northern Virginia, military communities in Hampton Roads and Quantico, and corporate headquarters in the Tysons Corner and Richmond corridors. Virginia exempts Social Security and provides age-based deductions on other retirement income. Northern Virginia advisors specialize in federal retirement benefits (FERS, TSP), military pension optimization, and government contractor equity compensation. Richmond advisors serve the state's banking and Fortune 500 corporate community."},
    {"name": "Washington", "slug": "washington", "abbr": "WA", "description": "Washington has no state income tax but recently enacted a capital gains tax on high earners, creating new planning considerations. Seattle, Bellevue, Tacoma, and Spokane are the main advisory markets. Washington's massive tech sector (Amazon, Microsoft, Boeing) generates enormous demand for equity compensation planning, concentrated stock strategies, and tax-efficient wealth management. Seattle-area advisors are among the most experienced in the country with RSUs, ISOs, and mega-backdoor Roth strategies for tech workers."},
    {"name": "West Virginia", "slug": "west-virginia", "abbr": "WV", "description": "West Virginia is phasing out its income tax on Social Security benefits and offers moderate treatment of other retirement income. Charleston, Huntington, and Morgantown host the state's advisory community. West Virginia advisors specialize in retirement planning for state employees, energy industry wealth management (coal and natural gas), and helping clients navigate the transition from resource-dependent careers. The state's lower cost of living is increasingly attractive to retirees from neighboring Virginia and Maryland."},
    {"name": "Wisconsin", "slug": "wisconsin", "abbr": "WI", "description": "Wisconsin exempts Social Security benefits from state taxation and offers favorable treatment of retirement income from certain state pensions. Milwaukee, Madison, and Green Bay are the primary advisory markets. Wisconsin advisors serve the state's manufacturing sector (Johnson Controls, Harley-Davidson, Rockwell Automation) with corporate retirement plan optimization. Madison's university and state government workforce creates demand for public pension planning, and the state's strong agricultural heritage drives need for farm succession and estate planning."},
    {"name": "Wyoming", "slug": "wyoming", "abbr": "WY", "description": "Wyoming has no state income tax, no estate tax, and favorable trust laws — making it alongside South Dakota and Nevada as a top wealth planning jurisdiction. Cheyenne, Casper, and Jackson Hole are the main advisory markets, with Jackson Hole hosting a concentration of high-net-worth wealth managers serving ultra-wealthy clients drawn to the area's lifestyle. Wyoming advisors specialize in trust administration, ranch and mineral rights estate planning, and wealth management for energy industry families."},
]

# Advisor specialties (equivalent to SERVICES in senior home care)
SPECIALTIES = [
    {
        "name": "Retirement Planning",
        "slug": "retirement-planning",
        "icon": "🏖️",
        "description": "Comprehensive planning for retirement income, Social Security optimization, and lifestyle goals",
        "intro": "Retirement planning is the most sought-after financial advisory specialty, helping individuals and couples prepare for a financially secure retirement. A retirement planning advisor analyzes your current savings, projected Social Security benefits, pension income, and anticipated expenses to create a sustainable withdrawal strategy. Key areas include determining when to claim Social Security, optimizing 401(k) and IRA distributions, managing sequence-of-returns risk, and planning for healthcare costs including Medicare and long-term care. Whether you're 10 years from retirement or already retired, a qualified advisor can help you maximize your income while preserving your savings for the long term."
    },
    {
        "name": "Investment Management",
        "slug": "investment-management",
        "icon": "📈",
        "description": "Portfolio construction, asset allocation, and ongoing investment oversight",
        "intro": "Investment management advisors build and maintain diversified portfolios aligned with your financial goals, risk tolerance, and time horizon. Services typically include asset allocation strategy, security selection, portfolio rebalancing, tax-loss harvesting, and performance monitoring. A good investment manager takes a disciplined approach to markets, avoiding emotional decisions during volatility while capturing long-term growth. When evaluating investment management advisors, ask about their investment philosophy (active vs. passive), typical portfolio construction, fee structure (percentage of assets under management is most common), and how they measure and report performance."
    },
    {
        "name": "Tax Strategy",
        "slug": "tax-strategy",
        "icon": "📋",
        "description": "Tax-efficient investing, Roth conversions, and minimizing your lifetime tax burden",
        "intro": "Tax strategy advisors specialize in minimizing your lifetime tax burden through sophisticated planning techniques. This includes tax-loss harvesting, asset location optimization (placing investments in the most tax-efficient accounts), Roth conversion strategies, charitable giving optimization, and capital gains management. For business owners, tax planning extends to entity structure, qualified business income deductions, and retirement plan selection. A skilled tax strategist coordinates with your CPA to ensure investment decisions and tax filing work together. The best tax planners think in terms of lifetime tax minimization rather than just reducing this year's bill."
    },
    {
        "name": "Estate Planning",
        "slug": "estate-planning",
        "icon": "🏛️",
        "description": "Wealth transfer, trust strategies, and legacy planning for your heirs",
        "intro": "Estate planning advisors help you structure the transfer of wealth to heirs, charities, and other beneficiaries in the most tax-efficient way possible. Services include coordinating with estate attorneys on wills and trusts, beneficiary designation optimization, life insurance analysis, charitable giving strategies (donor-advised funds, charitable remainder trusts), and business succession planning. With the federal estate tax exemption potentially decreasing in coming years, proactive estate planning is more important than ever for families with significant assets. A qualified advisor ensures your wealth passes to the people and causes you care about, not to unnecessary taxes."
    },
    {
        "name": "College Savings",
        "slug": "college-savings",
        "icon": "🎓",
        "description": "529 plans, education funding strategies, and financial aid optimization",
        "intro": "College savings advisors help families plan for the rising cost of higher education through strategies like 529 plans, Coverdell ESAs, custodial accounts, and financial aid optimization. With the average cost of a four-year degree exceeding $100,000 at many institutions, early and strategic planning can make a significant difference. Advisors evaluate the best savings vehicles based on your state's tax benefits, your expected financial aid eligibility, and your timeline. They also help coordinate college funding with other financial goals like retirement savings, ensuring you don't sacrifice your own financial security for your children's education."
    },
    {
        "name": "Insurance Planning",
        "slug": "insurance-planning",
        "icon": "🛡️",
        "description": "Life insurance, disability, long-term care, and risk management strategies",
        "intro": "Insurance planning advisors evaluate your risk exposure and recommend appropriate coverage for life insurance, disability insurance, long-term care insurance, and umbrella liability policies. The goal is protecting your family and wealth against catastrophic events without overpaying for unnecessary coverage. Fee-only insurance planning advisors are particularly valuable because they have no commission incentive to recommend products you don't need. Key areas include determining the right amount and type of life insurance, evaluating long-term care options (traditional policies, hybrid products, self-insurance), and coordinating insurance with your overall financial plan."
    },
    {
        "name": "Small Business",
        "slug": "small-business",
        "icon": "🏢",
        "description": "Business retirement plans, succession planning, and owner financial strategies",
        "intro": "Small business financial advisors help entrepreneurs and business owners navigate the unique financial challenges of running a company. Services include selecting and managing business retirement plans (SEP IRA, SIMPLE IRA, Solo 401(k), defined benefit plans), business succession and exit planning, entity structure optimization, cash flow management, and key person insurance. Many business owners have the majority of their wealth tied up in their company, making diversification and exit planning critical. A qualified advisor helps you build personal wealth alongside your business and plan for a successful eventual transition — whether through sale, family succession, or closing."
    },
    {
        "name": "Wealth Management",
        "slug": "wealth-management",
        "icon": "💎",
        "description": "Comprehensive financial oversight for high-net-worth individuals and families",
        "intro": "Wealth management advisors provide comprehensive financial oversight for high-net-worth individuals and families, typically those with $1 million or more in investable assets. Services integrate investment management, tax planning, estate planning, risk management, philanthropic strategy, and family governance into a coordinated plan. Wealth managers often serve as the quarterback of your financial life, coordinating with your CPA, estate attorney, insurance agent, and other professionals. When selecting a wealth manager, consider their minimum account size, the breadth of services included, their team structure, and how they handle multi-generational family planning."
    },
    {
        "name": "Debt Management",
        "slug": "debt-management",
        "icon": "📉",
        "description": "Student loan strategies, debt payoff planning, and credit optimization",
        "intro": "Debt management advisors help individuals create strategies for paying down debt efficiently while still building wealth. This includes student loan repayment optimization (evaluating PSLF, income-driven repayment, refinancing), mortgage strategy (15-year vs. 30-year, when to refinance), and prioritizing high-interest debt elimination. Many people struggle with the question of whether to pay down debt or invest, and a qualified advisor can model both scenarios based on your interest rates, tax situation, and investment returns. Debt management planning is often integrated with broader financial planning to ensure you're making progress toward all your goals simultaneously."
    },
    {
        "name": "Social Security Planning",
        "slug": "social-security",
        "icon": "🏛️",
        "description": "Optimizing Social Security claiming strategies for maximum lifetime benefits",
        "intro": "Social Security planning advisors specialize in helping individuals and couples optimize their claiming strategy to maximize lifetime benefits. The decision of when to claim Social Security — age 62, full retirement age, or 70 — can result in differences of hundreds of thousands of dollars over a lifetime. For married couples, the analysis becomes even more complex with spousal benefits, survivor benefits, and coordinated claiming strategies. Advisors use specialized software to model different scenarios based on your health, life expectancy, other income sources, and tax situation. Given that Social Security is the foundation of most Americans' retirement income, getting this decision right is one of the highest-value planning activities available."
    },
]

# Advisor credentials (trust signals)
CREDENTIALS = [
    {"abbr": "CFP", "name": "Certified Financial Planner", "description": "Comprehensive financial planning certification requiring extensive education, examination, experience, and ethical standards"},
    {"abbr": "CFA", "name": "Chartered Financial Analyst", "description": "Investment analysis and portfolio management credential, considered the gold standard for investment professionals"},
    {"abbr": "CPA", "name": "Certified Public Accountant", "description": "Accounting and tax expertise, valuable for tax-focused financial planning"},
    {"abbr": "ChFC", "name": "Chartered Financial Consultant", "description": "Advanced financial planning credential with broader curriculum than CFP"},
    {"abbr": "RICP", "name": "Retirement Income Certified Professional", "description": "Specialized in retirement income planning and distribution strategies"},
    {"abbr": "CLU", "name": "Chartered Life Underwriter", "description": "Insurance and risk management expertise, especially life insurance planning"},
    {"abbr": "EA", "name": "Enrolled Agent", "description": "Federally licensed tax practitioner authorized to represent clients before the IRS"},
]

# Fee structures
FEE_STRUCTURES = [
    "Fee-Only",
    "Fee-Based",
    "Commission",
    "Flat Fee",
    "Hourly",
]

# Firm types
FIRM_TYPES = [
    "Independent RIA",
    "Wirehouse",
    "Hybrid",
    "Insurance-Based",
    "Bank-Affiliated",
    "Robo-Advisor",
]

# Blog categories
BLOG_CATEGORIES = [
    {"name": "Guides", "slug": "guides", "icon": "📖", "description": "Step-by-step guides for finding and working with financial advisors"},
    {"name": "Retirement", "slug": "retirement", "icon": "🏖️", "description": "Retirement planning strategies, Social Security, and pension optimization"},
    {"name": "Financial Planning", "slug": "financial-planning", "icon": "📊", "description": "Comprehensive financial planning topics and strategies"},
    {"name": "Investing", "slug": "investing", "icon": "📈", "description": "Investment strategies, portfolio management, and market insights"},
    {"name": "Tax Strategy", "slug": "tax-strategy", "icon": "📋", "description": "Tax-efficient investing and tax planning strategies"},
    {"name": "Resources", "slug": "resources", "icon": "🔗", "description": "Tools, checklists, and resources for investors"},
]

# SEO Settings
DEFAULT_META_TITLE = f"{SITE_NAME} - Find a Trusted Investment Advisor Near You"
DEFAULT_META_DESCRIPTION = SITE_DESCRIPTION

# Build Settings
ITEMS_PER_PAGE = 24
FEATURED_COUNT = 6
RECENT_COUNT = 8
