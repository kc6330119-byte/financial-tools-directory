import pandas as pd
import re
import json
import os
from datetime import datetime
from difflib import SequenceMatcher
from slugify import slugify

# ==============================
# CONFIGURATION
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# UPDATE THESE FILE NAMES when you have your Outscraper export
OUTSCRAPER_FILE = os.path.join(BASE_DIR, "outscraper_advisors.xlsx")
PREVIOUS_AIRTABLE_FILE = os.path.join(BASE_DIR, "Advisors Table-Grid view.csv")  # Export from Airtable if you have existing records

OUTPUT_FILE = os.path.join(BASE_DIR, "Advisors_NEW_ONLY.csv")
DUPLICATES_FILE = os.path.join(BASE_DIR, "Advisors_DUPLICATES_SKIPPED.csv")

COORD_TOLERANCE = 0.001
FUZZY_THRESHOLD = 0.90

# ==============================
# LOAD DATA
# ==============================

df = pd.read_excel(OUTSCRAPER_FILE)
print(f"Original Outscraper rows: {len(df)}")

# Load previous Airtable data if it exists
if os.path.exists(PREVIOUS_AIRTABLE_FILE):
    previous = pd.read_csv(PREVIOUS_AIRTABLE_FILE, encoding="utf-8-sig")
    print(f"Existing Airtable records: {len(previous)}")
else:
    previous = pd.DataFrame()
    print("No previous Airtable file found - importing all records")

df.columns = df.columns.str.strip().str.lower()
if not previous.empty:
    previous.columns = previous.columns.str.strip().str.lower()

def normalize(series):
    if isinstance(series, str):
        return pd.Series([series]).astype(str).str.strip().str.lower()
    return series.astype(str).str.strip().str.lower()


def safe_col(dataframe, col_name):
    """Get a column from a DataFrame, returning empty strings if column doesn't exist."""
    if col_name in dataframe.columns:
        return dataframe[col_name]
    return pd.Series([""] * len(dataframe))


# Normalize key fields for dedupe
df["name_clean"] = normalize(safe_col(df, "name"))
df["street_clean"] = normalize(safe_col(df, "address"))
df["city_clean"] = normalize(safe_col(df, "city"))
df["state_clean"] = normalize(safe_col(df, "state"))
df["location_link_clean"] = normalize(safe_col(df, "location_link"))

if not previous.empty:
    previous["name_clean"] = normalize(safe_col(previous, "name"))
    # Handle both "address" and "adress" (Airtable typo)
    previous["street_clean"] = normalize(safe_col(previous, "address") if "address" in previous.columns else safe_col(previous, "adress"))
    previous["city_clean"] = normalize(safe_col(previous, "city"))
    previous["state_clean"] = normalize(safe_col(previous, "state"))
    previous["location_link_clean"] = normalize(safe_col(previous, "google maps url"))

# ==============================
# INTERNAL DEDUPE
# ==============================

df = df.drop_duplicates(subset=["location_link_clean"])
df = df.drop_duplicates(subset=["name_clean", "street_clean"])
df = df.drop_duplicates(subset=["name_clean", "city_clean", "state_clean"])

print(f"After internal dedupe: {len(df)}")

# ==============================
# DUPLICATE DETECTION (vs existing Airtable)
# ==============================

if not previous.empty:
    existing_links = set(previous["location_link_clean"])
    existing_name_address = set(previous["name_clean"] + "|" + previous["street_clean"])
    previous_records = previous.to_dict("records")
else:
    existing_links = set()
    existing_name_address = set()
    previous_records = []

def fuzzy_match(a, b):
    return SequenceMatcher(None, a, b).ratio()

def coord_close(lat1, lon1, lat2, lon2):
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return False
    return abs(lat1 - lat2) <= COORD_TOLERANCE and abs(lon1 - lon2) <= COORD_TOLERANCE

def is_duplicate(row):
    if row["location_link_clean"] in existing_links:
        return True

    key = row["name_clean"] + "|" + row["street_clean"]
    if key in existing_name_address:
        return True

    for prev in previous_records:
        if row["city_clean"] != prev.get("city_clean", ""):
            continue
        if row["state_clean"] != prev.get("state_clean", ""):
            continue

        if coord_close(row.get("latitude"), row.get("longitude"),
                       prev.get("latitude"), prev.get("longitude")):
            return True

        if fuzzy_match(row["name_clean"], prev.get("name_clean", "")) >= FUZZY_THRESHOLD:
            return True

    return False

df["is_duplicate"] = df.apply(is_duplicate, axis=1).fillna(False)

duplicates = df[df["is_duplicate"]]
new_records = df[~df["is_duplicate"]]

print(f"Removed existing records: {len(duplicates)}")
print(f"New records to import: {len(new_records)}")

if len(duplicates) > 0:
    duplicates.to_csv(DUPLICATES_FILE, index=False)
    print(f"Duplicate report saved: {DUPLICATES_FILE}")

df = new_records.reset_index(drop=True)

print(f"Records to process: {len(df)}")

# ==============================
# FIELD HELPERS
# ==============================

def clean_field(val):
    """Convert a field value to a clean string, returning '' for nan/empty."""
    s = str(val).strip()
    return "" if s.lower() == "nan" or s == "" else s

def combine_description(row):
    """Get the best description from available fields."""
    parts = [
        clean_field(row.get("website_description", "")),
        clean_field(row.get("description", "")),
        clean_field(row.get("company_insights.description", "")),
    ]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    return max(parts, key=len)

def format_phone(phone):
    """Format phone number as (XXX) XXX-XXXX."""
    if pd.isna(phone):
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return ""

def _get_text_fields(row):
    """Combine common text fields for keyword matching."""
    return " ".join([
        clean_field(row.get("about", "")),
        clean_field(row.get("description", "")),
        clean_field(row.get("website_description", "")),
        clean_field(row.get("subtypes", "")),
        clean_field(row.get("company_insights.description", "")),
        clean_field(row.get("categories", "")),
    ]).lower()

def derive_specialties(row):
    """
    Derive advisor specialties from Outscraper text fields.
    Returns comma-separated values for Airtable multi-select.
    """
    SPECIALTY_KEYWORDS = {
        "Retirement Planning": ["retirement", "retire", "401k", "ira", "pension", "social security"],
        "Investment Management": ["investment management", "portfolio", "asset management", "wealth management", "asset allocation"],
        "Tax Strategy": ["tax planning", "tax strategy", "tax-loss", "tax efficient", "roth conversion", "tax optimization"],
        "Estate Planning": ["estate planning", "estate plan", "trust", "inheritance", "wealth transfer", "legacy"],
        "College Savings": ["college", "529", "education funding", "education planning"],
        "Insurance Planning": ["insurance planning", "life insurance", "long-term care insurance", "disability insurance", "risk management"],
        "Small Business": ["small business", "business owner", "succession planning", "business retirement", "sep ira", "solo 401k"],
        "Wealth Management": ["wealth management", "high net worth", "hnw", "ultra high", "family office"],
        "Debt Management": ["debt management", "student loan", "debt payoff", "credit"],
        "Social Security Planning": ["social security", "claiming strategy", "ssa", "social security optimization"],
    }

    text = _get_text_fields(row)

    specialties = set()
    for specialty, keywords in SPECIALTY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            specialties.add(specialty)

    return ", ".join(sorted(specialties))

def derive_services(row):
    """
    Derive services offered by the advisor.
    """
    SERVICE_KEYWORDS = {
        "Financial Planning": ["financial planning", "financial plan", "comprehensive plan"],
        "Investment Management": ["investment", "portfolio management", "asset management"],
        "Tax Planning": ["tax planning", "tax preparation", "tax strategy"],
        "Estate Planning": ["estate", "trust", "will", "inheritance"],
        "Retirement Planning": ["retirement", "401k", "ira", "pension"],
        "Insurance Analysis": ["insurance", "risk management", "life insurance"],
        "Social Security Optimization": ["social security"],
    }

    text = " ".join([
        clean_field(row.get("about", "")),
        clean_field(row.get("description", "")),
        clean_field(row.get("website_description", "")),
        clean_field(row.get("subtypes", "")),
        clean_field(row.get("company_insights.description", "")),
    ]).lower()

    services = set()
    for service, keywords in SERVICE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            services.add(service)

    return ", ".join(sorted(services))

def derive_fee_structure(row):
    """
    Derive fee structure from text.
    """
    FEE_KEYWORDS = {
        "Fee-Only": ["fee-only", "fee only"],
        "Fee-Based": ["fee-based", "fee based"],
        "Commission": ["commission"],
        "Flat Fee": ["flat fee", "fixed fee"],
        "Hourly": ["hourly", "per hour"],
    }

    text = " ".join([
        clean_field(row.get("about", "")),
        clean_field(row.get("description", "")),
        clean_field(row.get("website_description", "")),
        clean_field(row.get("company_insights.description", "")),
    ]).lower()

    fees = set()
    for option, keywords in FEE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            fees.add(option)

    return ", ".join(sorted(fees))

def derive_credentials(row):
    """
    Derive professional credentials from text.
    """
    CREDENTIAL_KEYWORDS = {
        "CFP": ["cfp", "certified financial planner"],
        "CFA": ["cfa", "chartered financial analyst"],
        "CPA": ["cpa", "certified public accountant"],
        "ChFC": ["chfc", "chartered financial consultant"],
        "RICP": ["ricp", "retirement income certified"],
        "CLU": ["clu", "chartered life underwriter"],
        "EA": ["enrolled agent"],
    }

    text = " ".join([
        clean_field(row.get("about", "")),
        clean_field(row.get("description", "")),
        clean_field(row.get("website_description", "")),
        clean_field(row.get("company_insights.description", "")),
        clean_field(row.get("name", "")),
    ]).lower()

    credentials = set()
    for credential, keywords in CREDENTIAL_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            credentials.add(credential)

    return ", ".join(sorted(credentials))

def derive_firm_type(row):
    """
    Derive firm type from text.
    """
    FIRM_TYPE_KEYWORDS = {
        "Independent RIA": ["ria", "registered investment advisor", "independent"],
        "Wirehouse": ["merrill lynch", "morgan stanley", "ubs", "wells fargo advisors", "edward jones"],
        "Insurance-Based": ["northwestern mutual", "new york life", "mass mutual", "prudential", "transamerica"],
        "Bank-Affiliated": ["bank", "trust company"],
    }

    text = " ".join([
        clean_field(row.get("about", "")),
        clean_field(row.get("description", "")),
        clean_field(row.get("website_description", "")),
        clean_field(row.get("company_insights.description", "")),
        clean_field(row.get("name", "")),
    ]).lower()

    for firm_type, keywords in FIRM_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return firm_type

    return ""

def derive_fiduciary(row):
    """
    Determine if the advisor is a fiduciary.
    Returns 'checked' if text contains fiduciary indicators.
    """
    text = " ".join([
        clean_field(row.get("about", "")),
        clean_field(row.get("description", "")),
        clean_field(row.get("website_description", "")),
        clean_field(row.get("company_insights.description", "")),
        clean_field(row.get("name", "")),
    ]).lower()

    fiduciary_terms = ["fiduciary", "fee-only", "ria"]
    if any(term in text for term in fiduciary_terms):
        return "checked"
    return ""

def derive_languages(row):
    """
    Derive languages spoken from text.
    """
    LANGUAGE_KEYWORDS = {
        "English": ["english"],
        "Spanish": ["spanish", "espanol", "habla espanol"],
        "Chinese": ["chinese", "mandarin", "cantonese"],
        "Vietnamese": ["vietnamese"],
        "Korean": ["korean"],
        "Tagalog": ["tagalog", "filipino"],
    }

    text = " ".join([
        clean_field(row.get("about", "")),
        clean_field(row.get("description", "")),
        clean_field(row.get("website_description", "")),
    ]).lower()

    languages = set()
    for lang, keywords in LANGUAGE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            languages.add(lang)

    # Default to English
    if not languages:
        languages.add("English")

    return ", ".join(sorted(languages))

def format_hours(hours_raw):
    """Format working hours from Outscraper data.
    Handles JSON dict format, raw strings, and encoding issues.
    Condenses repeated schedules (e.g., Mon-Fri: 9AM-5PM)."""
    if pd.isna(hours_raw):
        return ""

    raw = str(hours_raw).strip()
    if not raw or raw.lower() == "nan":
        return ""

    # Fix common encoding issues (Outscraper sometimes outputs garbled UTF-8)
    raw = raw.replace("\u2013", "-").replace("\u2014", "-")
    raw = raw.replace("\xc3\xa2\xe2\x82\xac\xe2\x80\x9c", "-")  # garbled en-dash
    raw = raw.replace("\xe2\x80\x93", "-")  # UTF-8 en-dash bytes
    # Also catch the common mojibake patterns as literal strings
    for bad in ["\u00e2\u0080\u0093", "\u00e2\u0080\u0094"]:
        raw = raw.replace(bad, "-")

    # Try to parse as JSON dict (Outscraper sometimes returns {'Monday': ['9AM-5PM'], ...})
    hours_dict = None
    try:
        hours_dict = json.loads(raw.replace("'", '"')) \
            if isinstance(raw, str) and raw.startswith("{") else None
    except:
        pass

    if isinstance(hours_dict, dict):
        formatted = []
        all_times = set()
        for day, times in hours_dict.items():
            if times:
                time_str = " & ".join(times)
                formatted.append(f"{day}: {time_str}")
                all_times.add(time_str)

        if len(all_times) == 1:
            return f"Daily: {list(all_times)[0]}"
        return ", ".join(formatted)

    # Already a string — clean it up and condense
    # Parse "Monday: 9AM-5PM, Tuesday: 9AM-5PM, ..." into condensed form
    DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    DAY_ABBREV = {"Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed", "Thursday": "Thu",
                  "Friday": "Fri", "Saturday": "Sat", "Sunday": "Sun"}

    day_hours = {}
    for part in raw.split(","):
        part = part.strip()
        if ":" in part:
            day, _, hours = part.partition(":")
            day = day.strip()
            hours = hours.strip()
            if day in DAY_ORDER:
                day_hours[day] = hours

    if not day_hours:
        # Can't parse — return cleaned raw string, truncated if too long
        clean = raw[:80] + "..." if len(raw) > 80 else raw
        return clean

    # Check if all weekdays are the same
    weekday_hours = [day_hours.get(d, "Closed") for d in DAY_ORDER[:5]]
    weekend_hours = [day_hours.get(d, "Closed") for d in DAY_ORDER[5:]]

    if len(set(weekday_hours)) == 1 and len(set(weekend_hours)) == 1:
        if weekday_hours[0] == weekend_hours[0]:
            if weekday_hours[0] == "Closed":
                return ""
            return f"Daily: {weekday_hours[0]}"
        elif weekend_hours[0] == "Closed":
            return f"Mon-Fri: {weekday_hours[0]}"
        else:
            return f"Mon-Fri: {weekday_hours[0]}, Sat-Sun: {weekend_hours[0]}"

    # Fall back to abbreviated day listing
    parts = []
    for day in DAY_ORDER:
        if day in day_hours and day_hours[day] != "Closed":
            parts.append(f"{DAY_ABBREV[day]}: {day_hours[day]}")
    return ", ".join(parts)

def normalize_state(state):
    """Convert state abbreviations to full names."""
    STATE_MAP = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
        "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
        "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
        "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
        "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
        "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
        "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
        "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
        "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
        "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
        "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
    }
    state = str(state).strip().upper()
    return STATE_MAP.get(state, state.title())

def generate_slug(row):
    """Generate a URL-friendly slug from name, city, and state abbreviation."""
    STATE_ABBREV = {
        "Alabama": "al", "Alaska": "ak", "Arizona": "az", "Arkansas": "ar",
        "California": "ca", "Colorado": "co", "Connecticut": "ct", "Delaware": "de",
        "District of Columbia": "dc", "Florida": "fl", "Georgia": "ga", "Hawaii": "hi",
        "Idaho": "id", "Illinois": "il", "Indiana": "in", "Iowa": "ia",
        "Kansas": "ks", "Kentucky": "ky", "Louisiana": "la", "Maine": "me",
        "Maryland": "md", "Massachusetts": "ma", "Michigan": "mi", "Minnesota": "mn",
        "Mississippi": "ms", "Missouri": "mo", "Montana": "mt", "Nebraska": "ne",
        "Nevada": "nv", "New Hampshire": "nh", "New Jersey": "nj", "New Mexico": "nm",
        "New York": "ny", "North Carolina": "nc", "North Dakota": "nd", "Ohio": "oh",
        "Oklahoma": "ok", "Oregon": "or", "Pennsylvania": "pa", "Rhode Island": "ri",
        "South Carolina": "sc", "South Dakota": "sd", "Tennessee": "tn", "Texas": "tx",
        "Utah": "ut", "Vermont": "vt", "Virginia": "va", "Washington": "wa",
        "West Virginia": "wv", "Wisconsin": "wi", "Wyoming": "wy"
    }
    name = clean_field(row.get("name", ""))
    city = clean_field(row.get("city", ""))
    state = normalize_state(str(row.get("state", "")))
    state_abbr = STATE_ABBREV.get(state, "")
    return slugify(f"{name} {city} {state_abbr}")

def col(name):
    """Get column from dataframe or return empty series."""
    return df[name] if name in df.columns else pd.Series([""] * len(df))

# ==============================
# BUILD OUTPUT
# ==============================

output = pd.DataFrame()

output["Name"] = col("name")
output["Slug"] = df.apply(generate_slug, axis=1)
output["Description"] = ""  # Left blank -- use auto_descriptions.py to generate
output["Address"] = col("street")
output["City"] = col("city")
output["State"] = col("state").apply(normalize_state)
output["Zip"] = col("postal_code")
output["Phone"] = col("phone").apply(format_phone)
output["Website URL"] = col("website")
output["Google Maps URL"] = col("location_link")
output["Photo URL"] = col("photo")
output["Hours"] = col("working_hours").apply(format_hours)
output["Specialties"] = df.apply(derive_specialties, axis=1)
output["Credentials"] = df.apply(derive_credentials, axis=1)
output["Services"] = df.apply(derive_services, axis=1)
output["Firm Type"] = df.apply(derive_firm_type, axis=1)
output["Minimum Investment"] = ""
output["Fee Structure"] = df.apply(derive_fee_structure, axis=1)
output["Fiduciary"] = df.apply(derive_fiduciary, axis=1)
output["SEC Registered"] = ""
output["Rating"] = col("rating")
output["Review Count"] = col("reviews")
output["Status"] = "Active"
output["Date Added"] = datetime.today().strftime("%Y-%m-%d")
output["Latitude"] = col("latitude")
output["Longitude"] = col("longitude")
output["Year Established"] = col("founded_year") if "founded_year" in df.columns else ""
output["Languages"] = df.apply(derive_languages, axis=1)

# Final column order matching Airtable schema exactly
FINAL_COLUMNS = [
    "Name",
    "Slug",
    "Description",
    "Address",
    "City",
    "State",
    "Zip",
    "Phone",
    "Website URL",
    "Google Maps URL",
    "Photo URL",
    "Hours",
    "Specialties",
    "Credentials",
    "Services",
    "Firm Type",
    "Minimum Investment",
    "Fee Structure",
    "Fiduciary",
    "SEC Registered",
    "Rating",
    "Review Count",
    "Status",
    "Date Added",
    "Latitude",
    "Longitude",
    "Year Established",
    "Languages",
]

for col_name in FINAL_COLUMNS:
    if col_name not in output.columns:
        output[col_name] = ""

output = output[FINAL_COLUMNS]

# Remove rows with no name or no city
output = output[output["Name"].str.strip() != ""]
output = output[output["City"].str.strip() != ""]

print(f"Final output row count: {len(output)}")

output.to_csv(OUTPUT_FILE, index=False)

print(f"New advisors file saved: {OUTPUT_FILE}")
print(f"\nNext steps:")
print(f"1. Open {OUTPUT_FILE} in Excel/Sheets to review")
print(f"2. Import to Airtable: Advisors table -> Import -> CSV")
