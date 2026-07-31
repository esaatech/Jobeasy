# Job Scraper Guide — Greenhouse, Lever & Ashby

| Field | Value |
|--------|--------|
| **Document ID** | `GUIDE-JOB-SCRAPE-001` |
| **Audience** | Product, ops, and engineers working on job ingestion |
| **Related plan** | `docs/architecture/ultimate-auto-apply-and-job-scraper.md` (`ARCH-ULTIMATE-AUTO-001`) |

This guide explains **how our job scraping works**, what Greenhouse / Lever / Ashby are, what we can and cannot do, and how to use admin scraping day to day.

---

## 1. The big picture (one minute)

We do **not** scrape “the entire internet of jobs.”

We scrape **one company at a time** from that company’s **public career board**, when the board is hosted on one of these hiring platforms:

| Platform | Example careers URL |
|----------|---------------------|
| **Greenhouse** | `https://boards.greenhouse.io/stripe` |
| **Lever** | `https://jobs.lever.co/spotify` |
| **Ashby** | `https://jobs.ashbyhq.com/notion` |

Each scrape downloads that company’s open roles and upserts them into our `Job` table (title, location, description, apply URL, date when available).

```text
Company career board (GH / Lever / Ashby)
        ↓
   Our scrapers (free public JSON APIs)
        ↓
   JobSource + Job + JobScrapingLog in Django
        ↓
   Later: match to Ultimate users (Phase 2)
```

---

## 2. Company vs hiring platform (admin columns)

In **Admin → Job sources** you see something like:

| Name | Source type | Board | Meaning |
|------|-------------|-------|---------|
| Spotify | API Integration | Lever | Company = Spotify; their careers site runs on **Lever** |
| Notion | API Integration | Ashby | Company = Notion; their careers site runs on **Ashby** |

### Plain language

- **Name** = the **company / business** that is hiring (Notion, Spotify, Stripe).
- **Board** = the **hiring software (ATS)** that hosts that company’s career page (Greenhouse, Lever, Ashby).
- **Source type** = *how* we fetch (`API Integration` for these boards).

### Analogy

| Concept | Everyday equivalent |
|---------|---------------------|
| Company | A store (Notion) |
| Greenhouse / Lever / Ashby | The store’s website platform |
| Indeed / LinkedIn / Seek | A shopping mall with many stores |

We are currently visiting **individual company stores** on known platforms — not the whole mall.

**Suggested mental labels for admin:**

- Name → **Company**
- Board → **ATS platform**

---

## 3. What Greenhouse, Lever, and Ashby are

They are **Applicant Tracking Systems (ATS)** / hiring platforms. Companies use them to:

- Host a public careers page
- Collect applications
- Manage candidates internally

### What we use (public, free)

Their **public job board APIs** — the same listings anyone can see on the careers page. No API key required for reading open jobs.

### What we do *not* use (private / employer-side)

Authenticated APIs that need a company’s API key (applicants, pipelines, scorecards). Those are employer tools, not for scraping other companies’ openings.

---

## 4. How a scrape works in Jobeasy

### Single pipeline (important)

Everything should call the same code path:

```text
job_service.services.ingestion.scrape_source() / run_scrape_cycle()
        ↑
   ┌────┴────────────────────────┐
   │                             │
Admin “Scrape jobs now”    manage.py scrape_jobs
                                   ↑
                         Cloud Run Job (later)
```

Do **not** invent a separate scrape path for Cloud Run. Admin manual runs and scheduled runs must stay identical.

### Per source

1. Read `JobSource.url`
2. Detect platform from hostname (`greenhouse.io`, `lever.co`, `ashbyhq.com`)
3. Call that platform’s public JSON API
4. Normalize into `ScrapedJob`
5. Upsert into `Job` by `(source, external_id)`
6. Write a `JobScrapingLog`

### IDs we store

| Platform | `external_id` example |
|----------|------------------------|
| Greenhouse | `greenhouse:7954688` |
| Lever | `lever:abc-123` |
| Ashby | `ashby:05e14247-17c4-...` |

---

## 5. Using admin to pull jobs manually

1. Go to **Admin → Job sources**
2. Click a company (e.g. Notion)
3. Scroll to **Fetch jobs from this board**
4. Click **Scrape jobs now**
5. Check the success message (`found` / `added` / `updated`)
6. Use **View jobs for this source** or **View scrape logs**

### Adding a new company

1. **Add job source**
2. **Name:** company name (e.g. `Monzo`)
3. **URL:** their public board URL  
   - Greenhouse: `https://boards.greenhouse.io/{token}`  
   - Lever: `https://jobs.lever.co/{site}`  
   - Ashby: `https://jobs.ashbyhq.com/{board}`
4. **Source type:** `API Integration`
5. Save, then **Scrape jobs now**

If the URL is wrong or the company left that platform, the scrape fails (often HTTP 404) and the error appears in **Job scraping logs**.

**Example:** Notion used to be on Greenhouse (`boards.greenhouse.io/notion` → 404). They moved to Ashby (`jobs.ashbyhq.com/notion`). Always verify the live careers URL.

---

## 6. What data we get (and quality)

Typical fields:

- Title, company, location  
- Description (often full JD text)  
- Direct **application URL** into the ATS  
- Tags (department / team when present)  
- **Posted / updated date** when the API provides it  

### How good is it?

**Strengths**

- Real employer jobs (not spam aggregators)
- Direct apply links
- Full descriptions (good for AI fit / cover letters later)
- Stable IDs for deduping on re-scrape

**Weaknesses**

- Only companies on these three platforms (with a public board)
- Location text is inconsistent (`SF` vs `San Francisco, CA` vs `US`)
- Board URLs go stale when companies switch ATS

### Typical size

Per company board: tens to hundreds of open roles (large tech boards can be 400–500+).

---

## 7. Country filter (USA vs UK, etc.)

**Question:** Can we ask Greenhouse/Lever/Ashby for “only USA” or “only UK”?

**Answer:** Not reliably at the API.

| Platform | Server-side country filter? |
|----------|------------------------------|
| Greenhouse | No useful country filter |
| Lever | Partial location query (city/text — not a clean country enum) |
| Ashby | Public board = all listed jobs |

**Recommended approach**

1. Fetch the full company board  
2. Filter in our code by location keywords / country allowlist  
3. Optionally store allowlist on `JobSource` (e.g. `US`, `UK`, `AU`) — not built as a field yet; matching can also filter by user prefs in Phase 2  

So: scrape broadly per company → keep or match only the geographies you care about.

---

## 8. Are we limited to companies on these platforms?

**Yes.**

| Situation | Can we scrape today? |
|-----------|----------------------|
| Company on Greenhouse / Lever / Ashby public board | Yes |
| Workday / Taleo / iCIMS / custom site only | Not yet |
| Only LinkedIn / Indeed / Seek | Not yet |
| No public board | No |

Many tech companies use GH/Lever/Ashby — good coverage for a first product — but it is **not** all employers worldwide.

---

## 9. “Do I need to know every company?” / “All jobs this week?”

### Do I need a company list?

With the current design: **yes, you need board URLs** (one per company you care about). There is no free official API that returns “every Greenhouse customer” or “every job posted this week on Earth.”

### “Download all jobs opened this week”

| Approach | Reality |
|----------|---------|
| Our ATS scrapers | Only for companies you’ve added; then filter by `posted_date` |
| Aggregator APIs (Indeed, Adzuna, JSearch, etc.) | Closer to search-by-country/date; usually **paid** / ToS-limited |
| Perfect global coverage | Not free, not complete |

### How people grow ATS coverage

1. **Curated list** — seed important companies (what we do now)  
2. **Community lists** of board slugs (incomplete, go stale — always verify)  
3. **Discover** from apply URLs that contain `greenhouse.io` / `lever.co` / `ashbyhq.com`  
4. **Paid ATS/company directories**  
5. **User-submitted job links** → auto-add Job Source  

There will never be a perfect free “all companies” list. Coverage is a growing, verified set of URLs.

---

## 10. Duplicate applications (same job twice)

### Same listing twice (same user)

Already designed around:

- `Job` unique on `(source, external_id)` — re-scrape updates, doesn’t duplicate the job row  
- `JobApplication` unique on `(user, job)` — one apply record per user per job  
- Phase 2 `ApplyTask` should use the same `(user, job)` uniqueness  

### Same company, different roles

Usually fine (Backend vs Sales at Stripe).

### Same role mirrored on LinkedIn + Indeed + ATS

Often the **same opening**. Job IDs differ across sites, so `(user, job)` alone won’t catch that. Future mitigation: remember **normalized company + title** for N days/weeks and skip near-duplicates when multi-source scraping grows.

### Same title at two different companies

Allowed — those are different jobs.

---

## 11. Regions (Europe, Australia, New Zealand)

Greenhouse / Lever / Ashby are **global**, not US-only. Location sits on each job.

What looks US-heavy today is mostly our **seed companies**, not the platforms.

| Region | Same free ATS approach | Local mega-boards |
|--------|------------------------|-------------------|
| Europe | Add EU company board URLs (e.g. Monzo on Greenhouse) | StepStone, Xing, etc. — usually harder / no free clean API |
| Australia / NZ | Add AU/NZ company boards when URL works | **Seek** dominates — separate scraper later |

To expand regionally: **add more company Job Sources**, then filter by location if needed.

---

## 12. CLI & Cloud Run (same pipeline)

```bash
# All active sources
poetry run python manage.py scrape_jobs

# One source by id
poetry run python manage.py scrape_jobs --source-id 1

# Seed default company boards (US + Canadian + European GH / Lever / Ashby)
poetry run python manage.py setup_job_sources
```

Default seed includes verified US boards plus Canadian (Cohere, 1Password, Hopper, Wealthsimple, Wattpad, Hootsuite, Lightspeed, Ritual, BenchSci) and European (Monzo, Spotify, SumUp, HelloFresh, Wolt, Celonis, Adyen, Elastic, Deliveroo, Doctolib, Tide, Alan, N26, Cabify, Trainline, DeepL, Bitpanda, Miro, Mollie, Qonto, GoCardless, Contentful, BlaBlaCar, Back Market, Typeform, Cleo, Trade Republic).

Cloud Run Job should run `scrape-entrypoint.sh` → `manage.py scrape_jobs` (same image as web, no separate scrape logic).

---

## 13. Code map

| Piece | Path |
|-------|------|
| Greenhouse scraper | `job_service/scrapers/greenhouse.py` |
| Lever scraper | `job_service/scrapers/lever.py` |
| Ashby scraper | `job_service/scrapers/ashby.py` |
| Registry (URL → scraper) | `job_service/scrapers/registry.py` |
| Ingestion / upsert / logs | `job_service/services/ingestion.py` |
| Management command | `job_service/management/commands/scrape_jobs.py` |
| Default company seeds | `job_service/management/commands/setup_job_sources.py` |
| Admin scrape button | `job_service/admin.py` + `templates/admin/job_service/jobsource/` |
| Cloud Run entry | `scrape-entrypoint.sh` |
| Models | `JobSource`, `Job`, `JobScrapingLog` in `job_service/models.py` |

---

## 14. FAQ

**Q: Are Greenhouse/Lever/Ashby free to scrape?**  
A: Public board read APIs need no key. Respect rate limits and ToS; don’t hammer them.

**Q: Why did Notion fail on Greenhouse?**  
A: They moved to Ashby. Old URL 404s. Use `https://jobs.ashbyhq.com/notion`.

**Q: Can we search the API by job title?**  
A: No for our use. We fetch all open jobs for that company; title matching happens later for Ultimate users.

**Q: Is “Board = Lever” a job board like Indeed?**  
A: No. Lever is the company’s ATS. The **Name** is the company.

**Q: What’s next for more coverage?**  
A: More Job Source URLs; optional country filter on ingest; later Seek/Workday/aggregators if needed.

---

## 15. Related docs

| Doc | Path |
|-----|------|
| Ultimate auto-apply plan | `docs/architecture/ultimate-auto-apply-and-job-scraper.md` |
| Dashboard AI apply pipeline | `docs/architecture/dashboard-job-application-pipeline.md` |
| AI platform | `ai_service/docs/AI_PLATFORM.md` |
