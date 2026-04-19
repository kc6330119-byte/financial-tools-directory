# Outscraper → Airtable → Site Runbook

**Purpose:** Operational guide for taking a fresh Outscraper Google Maps extract all the way through to indexed advisor pages on `smart-investor-financial-tools.com`.

**Use this when:** an Outscraper extract for a state (or batch of states) finishes and you have an `.xlsx` file ready to import.

**Time estimate:** ~45–60 minutes for a typical state batch (3,000–5,000 records). Validation + enrichment dominate; the actual scripts run in 1–3 min each.

**Risk level:** Medium. Steps 5b (`--remove-all`) and 7 (`--apply`) write to Airtable irreversibly. Take an Airtable export at Step 0 as your rollback snapshot.

---

## Prerequisites

Before starting, confirm:

- [ ] Outscraper extract is complete and saved locally (any name and path is fine — you'll rename in Step 0).
- [ ] `.env` at project root contains `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID`. Sanity-check:
  ```bash
  cd /Users/kevincollins/GitHub/financial-tools-directory
  grep -E "^AIRTABLE_(API_KEY|BASE_ID)=" .env
  ```
  Both lines should show values.
- [ ] Python environment imports `pyairtable` cleanly:
  ```bash
  python3 -c "import pyairtable; print(pyairtable.__version__)"
  ```
  - **If this errors** with `multiple bases have instance lay-out conflict`, you're on Python 3.13 with the pinned `pyairtable==2.3.3`. Either: (a) run with Python 3.9–3.12, or (b) `pip install --upgrade pyairtable` to get a 3.13-compatible release. Same fix for the `build.py` Airtable mode.
- [ ] Working tree is clean (no in-progress edits):
  ```bash
  git status
  ```

---

## Step 0 — Stage files + take rollback snapshot

**Time:** 2 min · **Risk:** none

1. **Take a fresh Airtable rollback snapshot** even if you exported recently. From the Airtable Advisors table → ⋯ → Download CSV. This is your "if everything goes wrong, we revert to here" file. Keep it somewhere safe — `~/Downloads/Advisors-rollback-YYYY-MM-DD.csv` is fine.

2. **Move + rename the Outscraper extract** into the project root with the exact filename the script expects:
   ```bash
   mv ~/Downloads/<your-outscraper-file>.xlsx \
      /Users/kevincollins/GitHub/financial-tools-directory/outscraper_advisors.xlsx
   ```

3. **Move + rename the Airtable export** the dedupe step will compare against:
   ```bash
   mv "~/Downloads/Advisors-Grid view.csv" \
      "/Users/kevincollins/GitHub/financial-tools-directory/Advisors Table-Grid view.csv"
   ```
   ⚠️ The space-separated filename `Advisors Table-Grid view.csv` is **load-bearing** — the script looks for that exact name. Quoting matters.

4. **Branch off main** so the data work is isolatable:
   ```bash
   cd /Users/kevincollins/GitHub/financial-tools-directory
   git checkout -b data/advisor-import-$(date +%Y-%m-%d)
   ```

---

## Step 1 — Run the dedupe + transform script

**Time:** 1–3 min · **Risk:** none (writes only to a new local CSV)

```bash
python3 outscraper_to_airtable.py
```

**Expected output:**
```
Original Outscraper rows: <N>
Existing Airtable records: <existing>
After internal dedupe: <N - internal dupes>
Removed existing records: <number caught vs Airtable>
New records to import: <new>
Records to process: <new>
Final output row count: <new minus rows missing name/city>
New advisors file saved: .../Advisors_NEW_ONLY.csv
```

**Two artifacts are written:**
- `Advisors_NEW_ONLY.csv` — what you'll import to Airtable in Step 3.
- `Advisors_DUPLICATES_SKIPPED.csv` — inspection-only, lets you verify dedupe didn't reject good records.

**Verify before continuing:**
- [ ] "New records to import" looks reasonable (not zero, not the entire input).
- [ ] If you ran a state that's already partially in Airtable, "Removed existing records" should be > 0. Texas re-runs catching ~424 dupes is normal.
- [ ] Open `Advisors_DUPLICATES_SKIPPED.csv` and spot-check 5 rows — they should genuinely match existing records (same name, same city, same coordinates).

**Common issue:** *"FileNotFoundError: outscraper_advisors.xlsx"* — Step 0 file rename didn't happen or used the wrong path.

---

## Step 2 — Inspect the import-ready CSV

**Time:** 5 min · **Risk:** none (just looking)

Open `Advisors_NEW_ONLY.csv` in Numbers / Excel / a CSV viewer. Spot-check at least 10 rows for:

- [ ] **Name** — looks like a financial advisor (not "Joe's Diner", not "Allstate Insurance")
- [ ] **City + State** — populated, state is full name (e.g., "Texas" not "TX")
- [ ] **Slug** — lowercase, hyphenated, includes city + state abbr (e.g., `smith-wealth-management-houston-tx`)
- [ ] **Phone** — formatted as `(XXX) XXX-XXXX`
- [ ] **Specialties** — comma-separated, mostly populated (the script derives from text; some will be blank, fixed in Step 6)
- [ ] **Description** — **intentionally blank** (filled in Step 7)
- [ ] **Status** — `Active`
- [ ] **Date Added** — today's date

**Red flags to fix before importing:**
- Most Specialty/Credentials/Fee fields blank → the source text might be too thin; fixable in steps 6+7 but worth noting now.
- Names containing obvious non-advisor terms (`Insurance`, `Bank`, `H&R Block`) → validation will catch these in Step 5, but if you see lots of them, your Outscraper search query may need tightening.
- Same advisor name appearing 5+ times across different cities → could be a chain (Edward Jones, Northwestern Mutual). Look at addresses to confirm they're real distinct offices.

---

## Step 3 — Import into Airtable

**Time:** 3–10 min depending on row count · **Risk:** medium (writes to Airtable; rollback = delete imported rows by Date Added)

1. Open the Airtable Advisors table.
2. Click **+ Add or import** → **CSV file** → upload `Advisors_NEW_ONLY.csv`.
3. **Field mapping:** Airtable should auto-match every column. Verify each maps to the correct field type — particularly:
   - Specialties / Credentials / Services / Fee Structure / Languages → multi-select (not text)
   - Fiduciary / SEC Registered → checkbox (the script writes the literal string `checked` for true; Airtable should interpret correctly)
   - Latitude / Longitude → number
   - Status → single-select (must be one of `Active`, `Featured`, `Draft`)
4. **Choose**: Add new records (don't overwrite). Confirm.
5. Wait for import to complete. Airtable shows `<N> records imported`.

**Verify before continuing:**
- [ ] New record count in Airtable = "Records to process" from Step 1's output.
- [ ] Filter by today's `Date Added` and spot-check 3 records by clicking through to the expanded view.
- [ ] No "field type mismatch" warnings.

**Rollback if Step 3 went wrong:** filter Airtable by today's `Date Added` and bulk-delete those records. Then re-import from `Advisors_NEW_ONLY.csv` after fixing whatever was off.

---

## Step 4 — Validate listings (scan only)

**Time:** 2–3 min · **Risk:** none (read-only scan)

```bash
python3 validate_listings.py
```

**Expected output:**
```
LIKELY ADVISOR:     <most of them>
REVIEW NEEDED:      <some>
LIKELY NOT ADVISOR: <few — these are clear non-advisors>
Total:              <total in Airtable, not just new batch>
```

Two artifacts:
- `validation_results.csv` — every record + classification
- `validation_flagged.csv` — only `REVIEW NEEDED` + `LIKELY NOT ADVISOR`

**Open `validation_flagged.csv` in your CSV viewer.** Sort by classification:

- **`LIKELY NOT ADVISOR`** rows are usually safe to delete (insurance agencies, banks, tax-prep chains). Spot-check 5 to confirm.
- **`REVIEW NEEDED`** rows are mixed-business cases — a CFP who also runs a tax-prep practice, or a firm whose name happens to contain "Insurance" but actually does fiduciary advising. **Manual review recommended** before deleting.

---

## Step 5 — Remove non-advisors (writes to Airtable)

**Time:** 1–5 min · **Risk:** medium (deletes rows from Airtable)

⚠️ **This is irreversible** without re-importing. The Airtable rollback snapshot from Step 0 is your safety net.

**Conservative path** (recommended for first runs):

```bash
python3 validate_listings.py --remove
```

Removes only `LIKELY NOT ADVISOR`. Outputs `Deleted N records.`

**Aggressive path** (use after you trust the validator on this dataset):

```bash
python3 validate_listings.py --remove-all
```

Removes both `LIKELY NOT ADVISOR` AND `REVIEW NEEDED`. Skips this if you haven't manually reviewed `REVIEW NEEDED` rows.

**Verify after:** Airtable record count drops by exactly the number reported.

---

## Step 6 — Backfill specialties

**Time:** 2–4 min · **Risk:** low (only writes to records that have empty Specialties)

**Dry run first:**
```bash
python3 backfill_specialties.py
```

Output shows how many records will get specialty assignments. Spot-check the preview ("Preview (first 5)") to confirm derived specialties match the description content.

**Apply:**
```bash
python3 backfill_specialties.py --apply
```

**Verify after:** in Airtable, filter by today's `Date Added` and a sample of records should now have at least one specialty tag.

---

## Step 7 — Enrich descriptions

**Time:** 5–10 min (template path) or 10–20 min (AI path) · **Risk:** low (only writes to thin/empty descriptions; doesn't touch good existing ones)

⚠️ **Order matters:** must run AFTER validation (Step 5). Enriched descriptions can mask non-advisor businesses by templating professional-sounding text over them.

**Two paths — pick one:**

### Path A — Template enrichment (`enrich_descriptions.py`)

- **Cost:** $0 (no API calls)
- **Speed:** Fast (~1 min for 3000 records)
- **Quality:** Deterministic. Same advisor → same description on every rebuild. ~32K unique sentence-pool combinations across the corpus, but every description follows the same skeleton.
- **Use when:** budget = 0, or you need bit-for-bit reproducibility across rebuilds.

```bash
python3 enrich_descriptions.py            # dry run
python3 enrich_descriptions.py --apply    # replace thin + irrelevant
python3 enrich_descriptions.py --append   # append to short (100–149 char) descs
```

### Path B — AI enrichment (`auto_descriptions.py`)

- **Cost:** ~$0.0015–$0.004 per record (uses Claude Haiku 4.5 with prompt caching on the system message; first call writes the cache, subsequent calls read at ~10% cost). For ~3000 records: **~$5–$12 total**.
- **Speed:** ~10–20 min for 3000 records (rate-limited to 0.25 s/record).
- **Quality:** Genuinely contextual — pulls from each advisor's actual data and writes natural prose. YMYL-aware prompt: no return claims, no guarantees, no income promises. Forbidden-phrase list drops the typical AI slop ("trusted partner," "tailored solutions," "holistic approach," etc.).
- **Two-pass design:** Pass 1 (free) strips junk — JSON blobs, advisor-CRM software lists ("MoneyGuide Pro · eMoney · Riskalyze"), regulatory boilerplate ("Securities offered through…", "Member FINRA/SIPC"), URLs/phones/emails masquerading as descriptions, and "nan" literals. Pass 2 sends only records still under 100 chars after cleaning to Claude.
- **Use when:** you have ~$10 of budget for a state batch and want descriptions that read like a person wrote them.

```bash
python3 auto_descriptions.py                   # dry run (shows estimated cost)
python3 auto_descriptions.py --apply           # Pass 1 cleanup only (free)
python3 auto_descriptions.py --apply --ai      # Pass 1 + AI generation
```

**Required for Path B:** `ANTHROPIC_API_KEY` in `.env` and `pip install anthropic` (or `pip install -r requirements.txt`).

**Recommendation:** Path B for the AdSense resubmission push (real, varied prose helps with content-quality signal). Path A if you ever need to rebuild without burning credits.

**Either way, the dry run is non-destructive** — both scripts default to dry run and require explicit `--apply` to write to Airtable.

---

## Step 8 — Rebuild the site locally + verify

**Time:** 1–2 min · **Risk:** none (local only)

```bash
python3 build.py
```

**Expected output:**
```
Fetching advisors...
  Fetched <N> advisor records so far...
  Fetched <total> advisors from Airtable.
Built: index.html (<total> advisors, <tools> tools)
Built: state/<each-state>.html
Built: state/<state>/<each-city>.html
Built: advisor/<each-slug>.html
...
Build complete!
```

**Verify in browser:**
```bash
cd dist && python3 -m http.server 8765
open http://localhost:8765/
```

Spot-check:
- [ ] Total advisor count on homepage hero stats matches Airtable.
- [ ] State page for one of the imported states (e.g., `/state/california.html`) shows the new advisors with proper metadata.
- [ ] At least 3 random advisor detail pages have full descriptions (no "nan", no obvious template gaps).
- [ ] Sitemap includes new advisor URLs (and excludes any city/state pages still under the 3-advisor threshold).

---

## Step 9 — Commit + push

**Time:** 2 min · **Risk:** medium (Netlify auto-deploys to production)

The Airtable change is already live for any new build. The build artifacts won't be committed (`dist/` is gitignored). What gets committed is just operational notes — and the local working files are gitignored too.

If you made any pipeline-script tweaks, commit them. Otherwise, the data import doesn't actually need a code commit.

**Trigger Netlify rebuild** (which will pull fresh Airtable data):
```bash
git checkout main
git merge --ff-only data/advisor-import-$(date +%Y-%m-%d) 2>/dev/null || true
git push origin main
git branch -d data/advisor-import-$(date +%Y-%m-%d)
```

If there were no commits on the branch (just data work), the merge is a no-op and that's fine.

**To force a Netlify rebuild without a code change:** in Netlify UI, Site overview → Trigger deploy → Deploy site.

---

## Step 10 — Post-deploy verification

**Time:** 5 min after Netlify finishes

- [ ] Hit production URL for a new advisor: `https://smart-investor-financial-tools.com/advisor/<a-new-slug>.html` → should return 200 with full content.
- [ ] Check the state hub page for one of the imported states → new advisors appear in the list.
- [ ] In Google Search Console, **Sitemaps** → re-submit `sitemap.xml` to nudge Google to recrawl. Not required (it'll find changes on its own crawl cycle), but speeds things along.
- [ ] After 3–7 days, check **Indexing → Pages** in GSC for new URL discovery + indexing status.

---

## Rollback procedures

| When you discover the problem | What to do |
|---|---|
| **During Step 1 (dedupe)** | Re-run the script — outputs are non-destructive. Or just delete `Advisors_NEW_ONLY.csv`. |
| **After Step 3 (Airtable import) but before Step 5** | In Airtable, filter by today's `Date Added` → bulk delete the filtered set. Re-import after fixing. |
| **After Step 5 (validator deleted records)** | Restore the deleted records from your Step 0 rollback snapshot CSV. Re-import only the rows that were deleted. |
| **After Step 7 (descriptions enriched)** | Most painful rollback. The script overwrites Description fields. Restore from Airtable's "snapshots" feature (Settings → Snapshots) if you took one before running, or restore from the Step 0 CSV by clearing all Description fields and re-importing only the Description column. |
| **After Step 9 (deployed)** | `git revert` doesn't help — the issue is in the data, not the code. Fix the data in Airtable (manually delete bad records or restore from snapshot), then trigger a Netlify redeploy. |

---

## Common issues + fixes

| Symptom | Cause | Fix |
|---|---|---|
| `FileNotFoundError: outscraper_advisors.xlsx` | Step 0 rename didn't run or used wrong path | Re-run the `mv` in Step 0 |
| Step 1 says "Existing Airtable records: 0" but you have records | Step 0 second `mv` didn't run, or filename has wrong spelling | Filename must be **`Advisors Table-Grid view.csv`** with the literal space; quote it in shell |
| `multiple bases have instance lay-out conflict` on script start | Python 3.13 + pinned `pyairtable==2.3.3` | `pip install --upgrade pyairtable` or run scripts with Python 3.9–3.12 |
| Airtable import warns "field type mismatch" on Specialties | CSV multi-select field has values not in the Airtable single-select options | Check the new Specialty values against `config.SPECIALTIES`; either update Airtable's allowed values or fix the CSV |
| `validate_listings.py` flags 50%+ as `LIKELY NOT ADVISOR` | Outscraper search query was too broad (pulled in non-advisor businesses) | Use `--remove`, then refine the Outscraper query for the next batch |
| `enrich_descriptions.py` reports 0 changes | All descriptions are already 150+ chars | Nothing to do; this is the success case |
| Site builds but new advisors missing on production | Netlify build using cached Airtable data | Trigger a manual deploy from Netlify UI |
| Build aborts with Airtable timeout | Too many records, paginated fetch hitting gateway timeout | Already mitigated in `build.py` with 0.2s sleep between pages, but if it persists, increase the sleep to 0.5s |

---

## Sequencing across multiple state imports

Per the AdSense resubmission plan, target order is:

1. **Tier 1** (highest population, do first): CA, TX, FL, NY, PA
2. **Tier 2**: IL, OH, GA, NC, NJ
3. **Tier 3**: remaining 40 states in batches of 10

**Recommended cadence:** one state per day during heavy import phase. Run Steps 1–8 each day. Build a streak so the validator's keyword tuning gets exercised on each new state's quirks.

**At the end of each batch:** request indexing on the top 5 newly-populated state pages in Google Search Console (top search bar → URL Inspection → Request indexing).

---

## Files this runbook references

| File | Created/used by | Gitignored? |
|---|---|---|
| `outscraper_advisors.xlsx` | Step 0 input | yes |
| `Advisors Table-Grid view.csv` | Step 0 input | yes |
| `Advisors_NEW_ONLY.csv` | Step 1 output, Step 3 input | yes |
| `Advisors_DUPLICATES_SKIPPED.csv` | Step 1 output (inspection only) | yes |
| `validation_results.csv` | Step 4 output | yes |
| `validation_flagged.csv` | Step 4 output | yes |

All of these are in `.gitignore` — they never get committed. Fresh runs overwrite them.

---

*Last updated: 2026-04-18. If a step fails or feels off, paste the error and the step number to Claude and ask for a debug pass.*
