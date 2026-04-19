#!/usr/bin/env python3
"""
upload_blogposts.py — Upload markdown blog posts in content/blogposts/ to Airtable.

Reads every .md file in content/blogposts/, parses the frontmatter (between
``` markers) into Airtable field values, and creates one record per post in
the Blog Posts table. Skips posts that already exist (matched by Slug).

Usage:
    python3 upload_blogposts.py            # Dry run — shows what would be uploaded
    python3 upload_blogposts.py --apply    # Actually write to Airtable

Requirements:
    - .env with AIRTABLE_API_KEY + AIRTABLE_BASE_ID
    - Airtable Blog Posts table with fields: Title, Slug, Content, Excerpt,
      Author, Publish Date, Meta Description, Status, Featured, Category
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_BLOG_TABLE_NAME", "Blog Posts")

CONTENT_DIR = Path(__file__).parent / "content" / "blogposts"
CHUNK_SIZE = 10  # Airtable batch_create limit


def parse_frontmatter(text):
    """Extract frontmatter dict + content body. Returns (meta, content)."""
    if not text.startswith("```"):
        return {}, text
    parts = text.split("```", 2)
    if len(parts) < 3:
        return {}, text
    meta = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip().lower()] = value.strip()
    return meta, parts[2].strip()


def build_record(meta, content):
    """Build an Airtable record dict from parsed frontmatter + body content."""
    record = {
        "Title": meta.get("title", "").strip(),
        "Slug": meta.get("slug", "").strip(),
        "Content": content,
        "Excerpt": meta.get("excerpt", "").strip(),
        "Author": meta.get("author", "Smart Investor Staff").strip(),
        "Publish Date": meta.get("published date", meta.get("publish date", "")).strip(),
        "Meta Description": meta.get("meta description", "").strip(),
        "Status": meta.get("status", "Published").strip(),
        "Featured": meta.get("featured", "").lower() == "true",
        "Category": meta.get("category", "").strip(),
    }
    # Drop empty optional values so Airtable doesn't reject (e.g., empty date field)
    return {k: v for k, v in record.items() if v not in ("", None)}


def main():
    apply_mode = "--apply" in sys.argv

    print(f"\n{'='*62}")
    print(f"  Upload Blog Posts to Airtable  [{'APPLY' if apply_mode else 'DRY RUN'}]")
    print(f"{'='*62}\n")

    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        print("Error: AIRTABLE_API_KEY or AIRTABLE_BASE_ID not set in .env")
        sys.exit(1)

    if not CONTENT_DIR.exists():
        print(f"Error: {CONTENT_DIR} does not exist")
        sys.exit(1)

    # Lazy-import pyairtable so the script doesn't fail on the env-check above
    from pyairtable import Api

    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, TABLE_NAME)

    print("Fetching existing posts from Airtable...")
    existing_slugs = set()
    for r in table.all():
        slug = (r.get("fields") or {}).get("Slug")
        if slug:
            existing_slugs.add(slug.strip())
    print(f"  Found {len(existing_slugs)} existing post(s).\n")

    files = sorted(CONTENT_DIR.glob("*.md"))
    print(f"Found {len(files)} markdown file(s) in {CONTENT_DIR}\n")

    to_upload = []
    skipped = []

    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception as e:
            skipped.append((f.name, f"read error: {e}"))
            continue

        meta, content = parse_frontmatter(text)
        record = build_record(meta, content)

        if not record.get("Slug") or not record.get("Title"):
            skipped.append((f.name, "missing slug or title in frontmatter"))
            continue

        if record["Slug"] in existing_slugs:
            skipped.append((f.name, f"already in Airtable (slug={record['Slug']})"))
            continue

        to_upload.append((f.name, record))

    print(f"To upload: {len(to_upload)}")
    print(f"To skip:   {len(skipped)}\n")

    if skipped:
        print("Skipped:")
        for name, reason in skipped:
            print(f"  - {name}: {reason}")
        print()

    if to_upload:
        print("To upload:")
        for name, record in to_upload:
            cat = record.get("Category", "?")
            print(f"  - [{cat}] {record['Title']}")
        print()

    if not apply_mode:
        print("Dry run complete. Use --apply to actually upload to Airtable.")
        return

    if not to_upload:
        print("Nothing to upload.")
        return

    records_only = [r for _, r in to_upload]
    print(f"Uploading {len(records_only)} post(s) to Airtable...")
    for i in range(0, len(records_only), CHUNK_SIZE):
        batch = records_only[i:i + CHUNK_SIZE]
        table.batch_create(batch)
        print(f"  Created {min(i + CHUNK_SIZE, len(records_only))}/{len(records_only)}")

    print(f"\nDone! Uploaded {len(to_upload)} post(s).")
    print("Trigger a Netlify rebuild to publish them on the live site.")


if __name__ == "__main__":
    main()
