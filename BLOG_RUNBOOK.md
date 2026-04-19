# Blog Post Upload Runbook

**Purpose:** Operational guide for adding new blog posts to the Smart Investor blog. Covers writing the markdown, uploading to Airtable via `upload_blogposts.py`, adding featured images, and publishing.

**Use this when:** You have one or more new blog posts (markdown files) ready to publish.

**Time estimate:** ~10 minutes per batch of posts (most of it Netlify rebuild wait time).

**Risk level:** Low. The upload script only inserts new records; it never updates or deletes existing ones. Worst case: a duplicate (and the script skips duplicates by slug, so even that's hard to trigger).

---

## Prerequisites

Confirm before starting:

- [ ] `.env` at project root contains `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID`. Sanity check:
  ```bash
  grep -E "^AIRTABLE_(API_KEY|BASE_ID)=" .env
  ```
- [ ] `pyairtable` imports cleanly:
  ```bash
  python3 -c "import pyairtable; print(pyairtable.__version__)"
  ```
  If this errors with `multiple bases have instance lay-out conflict`, you're on a pinned old version. Fix:
  ```bash
  pip install --upgrade pyairtable
  ```
  (`requirements.txt` is now `pyairtable>=3.0.0` so a fresh `pip install -r requirements.txt` does this automatically.)

---

## Step 1 — Write the markdown post

Create a file in `content/blogposts/` named with the post's slug, e.g., `understanding-roth-conversions.md`. Same naming convention as existing posts.

**Frontmatter format** (between ``` markers, lowercase keys):

```markdown
` ` `
title: Understanding Roth Conversions: Is It Right for You?
slug: understanding-roth-conversions
category: Financial Planning
published date: 2026-04-18
author: Smart Investor Staff
excerpt: A 1-2 sentence excerpt shown on the blog hub and as the article deck.
meta description: SEO description, 150-160 characters, used in <meta name="description">.
status: Published
featured: true
` ` `

Body content here in markdown. ## H2 headings, ### H3 subheadings, normal paragraphs, **bold**, *italic*, lists, blockquotes, links.
```

(In real files, use three backticks without spaces — shown spaced here so this runbook renders.)

### Field reference

| Field | Required? | Notes |
|---|---|---|
| `title` | yes | Plain text. Drives `<h1>` and `<title>` tags. |
| `slug` | yes | URL slug, lowercase + hyphens. Determines `/blog/<slug>.html`. **Must be unique** — script skips if it already exists in Airtable. |
| `category` | yes | Single value, **must match an existing Airtable category option**. Current options: `Guides`, `Financial Planning`, `Retirement`, `Investing`. Adding new categories requires Airtable schema update first. |
| `published date` | yes | `YYYY-MM-DD` format. Used to sort the blog hub (newest first) and as the article byline date. The space-separated key (`published date`) is intentional — matches what `build.py load_local_blog_posts` expects. |
| `author` | yes | Defaults to `Smart Investor Staff` if missing. |
| `excerpt` | yes | 1-2 sentences. Renders as the deck/lede on the post page and the description on the blog hub. |
| `meta description` | yes | 150-160 chars. Goes into `<meta name="description">` for SEO. |
| `status` | yes | `Published` makes the post visible on the live site. Set to `Draft` if you want to upload but not publish yet (the build skips Status≠Published posts). |
| `featured` | optional | `true` or `false`. Featured posts get visual emphasis on the blog hub if you've wired that up. |

### Style conventions (informal but consistent across existing posts)

- ~1,500–2,000 words per post
- H2 sections, occasional H3 subsections
- Specific numbers and named tools where possible (Vanguard, Fidelity, real percentages, real timeframes)
- Reference FINRA BrokerCheck and SEC IAPD on YMYL-relevant topics
- Closing paragraph soft-pitches the advisor directory with a BrokerCheck verification reminder
- Avoid AI-slop phrases ("trusted partner," "tailored solutions," "holistic approach," "nestled," "boasting"). The `auto_descriptions.py` system prompt has the full prohibited-phrases list — same standards apply to blog content.

---

## Step 2 — Dry-run the upload

```bash
python3 upload_blogposts.py
```

**Expected output:**
```
Fetching existing posts from Airtable...
  Found N existing post(s).

Found M markdown file(s) in content/blogposts/

To upload: <new posts>
To skip:   <posts already in Airtable>

Skipped:
  - <filename>: already in Airtable (slug=...)
  ...

To upload:
  - [Category] Title
  ...

Dry run complete. Use --apply to actually upload to Airtable.
```

**Verify:**

- [ ] "To upload" count matches the number of new posts you wrote.
- [ ] Every existing post gets correctly skipped by slug match (no surprise duplicates).
- [ ] Each new post shows the right `[Category]` tag — if any show `[?]` or unexpected category, the frontmatter is malformed.

**Common dry-run issues:**

- *"missing slug or title in frontmatter"* — your frontmatter isn't enclosed in triple-backticks, or the keys are uppercase, or there's no value after the colon.
- *Skip message for a post you intended to upload* — slug collision with an existing post. Either change the slug in the markdown or delete the existing record from Airtable first.

---

## Step 3 — Apply the upload

```bash
python3 upload_blogposts.py --apply
```

**Expected output:** same as dry run, plus:

```
Uploading N post(s) to Airtable...
  Created N/N

Done! Uploaded N post(s).
Trigger a Netlify rebuild to publish them on the live site.
```

The script uses `batch_create` in chunks of 10. If you have more than 10 posts to upload, you'll see progress lines per batch.

**Verify in Airtable:**

- [ ] Open Blog Posts table.
- [ ] Filter by today's `Publish Date` (or use the most-recently-created sort).
- [ ] Spot-check one new record: Title, Slug, Content (markdown body), Excerpt, Category, Author, Status, Meta Description all populated.
- [ ] Status shows `Published` for all uploaded posts (unless you set `status: Draft` in the frontmatter).

---

## Step 4 — Add featured images (optional)

The script does **not** upload images. If you want a featured image:

1. In Airtable, open each post you just uploaded.
2. In the **Featured Image** field (which is an Airtable attachment field), drag in or upload an image file.
3. The build picks up the first attachment URL and uses it as both the inline `<img>` on the post page and the `og:image` for social sharing.
4. Recommended dimensions: ~1200×630 (works well for both inline display and Open Graph cards).

Posts work fine without a featured image — the post page renders without the image block, and `og:image` falls back to the site logo.

---

## Step 5 — Trigger Netlify rebuild

The data lives in Airtable; the build pulls it on every Netlify build.

**Option A — empty git commit:**
```bash
git commit --allow-empty -m "chore: trigger rebuild — N new blog posts"
git push origin main
```

**Option B — manual trigger in Netlify UI:**
- Site overview → Deploys → **Trigger deploy** → **Deploy site**

Build typically completes in 2–4 minutes for the current site size.

---

## Step 6 — Verify on production

After the build completes:

- [ ] Hit `/blog.html` — your new posts should appear at the top (sorted by `published date` descending).
- [ ] Click into one new post. Verify:
  - H1 = title
  - Deck = excerpt
  - Byline shows author + reading time + date
  - Body markdown renders correctly (headings, lists, links, blockquotes)
  - Disclaimer box at the bottom
  - Share row + back-to-blog link
  - Related posts row populates (3 most-recent other posts)
- [ ] Check the post URL directly: `https://smart-investor-financial-tools.com/blog/<your-slug>.html` returns 200.
- [ ] In Google Search Console, request indexing on the new post URLs (top search bar → Request indexing). Daily limit is ~10–15.

---

## Editing posts after upload

The script is **insert-only** by design — re-running it on a slug that already exists will skip the post, not overwrite it.

To edit an existing post:

1. **Edit the markdown locally** in `content/blogposts/` (so the source-of-truth file stays current).
2. **Edit the corresponding record in Airtable directly** — open the record, paste the new content into the Content field. Update Excerpt, Meta Description, etc., as needed.
3. **Trigger a Netlify rebuild** to publish the changes.

If you want a re-run-and-update workflow, that's an enhancement to `upload_blogposts.py` (add `--upsert` mode that updates by slug instead of skipping). Not implemented today — add when the manual pattern starts to bite.

---

## Common issues + fixes

| Symptom | Cause | Fix |
|---|---|---|
| `multiple bases have instance lay-out conflict` on script start | Old pinned `pyairtable==2.3.3` on Python 3.13 | `pip install --upgrade pyairtable` |
| `Error: AIRTABLE_API_KEY or AIRTABLE_BASE_ID not set in .env` | Missing or misnamed env vars | Check `.env` has both keys spelled exactly as shown |
| Post uploaded but Category field is empty in Airtable | Category value didn't match an existing single-select option | Add the new option to the Airtable Category field, then re-upload (or fix manually) |
| Post uploaded but doesn't show on the site after rebuild | Status field set to anything other than `Published` | Open the record in Airtable, change Status to `Published`, trigger another rebuild |
| `Publish Date` field shows blank in Airtable after upload | Date format wrong in frontmatter | Use `YYYY-MM-DD` exactly. The script reads `published date` (not `publish date` or `publishdate`). |
| Build error: `KeyError: 'Slug'` on a post | Frontmatter is missing slug | Add `slug:` to the markdown file, re-upload (will skip if it ran the first time) |

---

## Files this runbook references

| File | Created/used by |
|---|---|
| `content/blogposts/*.md` | Source markdown posts (gitignored — the directory is excluded). Treat as your local working copy. |
| `upload_blogposts.py` | The upload script. Run from project root. |
| `.env` | API credentials. Never commit. |
| Airtable Blog Posts table | The source of truth that `build.py` reads on every build. |

---

*Last updated: 2026-04-18.*
