# Job Sources Guide — Greenhouse, Lever & Ashby

| Field | Value |
|--------|--------|
| **Document ID** | `GUIDE-JOB-SOURCES-001` |
| **Related plan** | `ARCH-ULTIMATE-AUTO-001` (`docs/architecture/ultimate-auto-apply-and-job-scraper.md`) |
| **Audience** | Product, ops, and engineers working on job scraping |

This guide explains how Jobeasy collects jobs today, what the admin “Job sources” screen means, and what we can (and cannot) do with free ATS board APIs.

---

## 1. The big picture (30 seconds)

Jobeasy does **not** scrape “the whole internet” or Indeed/LinkedIn as one feed.

We pull open roles from **individual company career boards** that run on hiring platforms (ATS):

| Platform | Example company careers URL | Public jobs API (no API key) |
|----------|----------------------------|------------------------------|
| **Greenhouse** | `https://boards.greenhouse.io/stripe` | `boards-api.greenhouse.io/v1/boards/{token}/jobs` |
| **Lever** | `https://jobs.lever.co/spotify` | `api.lever.co/v0/postings/{site}?mode=json` |
| **Ashby** | `https://jobs.ashbyhq.com/notion` | `api.ashbyhq.com/posting-api/job-board/{board}` |

**Flow:**

```text
Company posts jobs on Greenhouse / Lever / Ashby
        ↓
We add that company as a Job Source (name + careers URL)
        ↓
Scrape (admin button or `manage.py scrape_jobs` / Cloud Run)
        ↓
Jobs upserted into Job table (title, location, description, apply URL, date, …)
        ↓
Later: match Ultimate users’ job titles → AI packet → apply queue
```

---

## 2. What Greenhouse, Lever, and Ashby actually are

They are **hiring platforms (ATS)**, not job malls like Indeed.

- Companies use them to **host a careers site** and manage applicants.
- Candidates see a public list of openings and an apply form.
- We use only the **public read APIs** (same data you’d see on the careers page).
- We do **not** use private employer APIs (candidates, scorecards, etc. — those need company API keys).

**Analogy**

| Concept | Everyday analogy |
|---------|------------------|
| Company (Notion, Spotify) | The store |
| ATS (Ashby, Lever, Greenhouse) | The website software that powers the store |
| Indeed / LinkedIn / Seek | A shopping mall with many stores |

We visit **each store’s own site** (via its ATS). We are not crawling the mall (yet).

---

## 3. Reading the admin “Job sources” screen

Example rows:

| Name | Source type | Board | Meaning |
|------|-------------|-------|---------|
| Spotify | API Integration | Lever | Company = Spotify; careers hosted on Lever |
| Notion | API Integration | Ashby | Company = Notion; careers hosted on Ashby |

### Column meanings

| Column | Meaning |
|--------|---------|
| **Name** | The **company** (business hiring). Prefer thinking of this as “Company.” |
| **Source type** | How we fetch (`api`, future: `rss`, `website`, …). |
| **Board** | Detected **ATS platform** from the URL (Greenhouse / Lever / Ashby). |
| **Is active** | Whether scheduled/manual scrape will include this source. |
| **Last scraped** | Last successful/attempted scrape time. |
| **Jobs** | Count of `Job` rows linked to this source (click to filter). |

One **Job source** row ≈ one company board URL.

To cover more employers, **add more company rows** — not one row named “Ashby” that means every Ashby customer.

---

## 4. How scraping works in code

### Single pipeline (important)

All callers should use the same path:

```text
job_service.services.ingestion.scrape_source() / run_scrape_cycle()
        ↑
   manage.py scrape_jobs          ← Cloud Run Job (`scrape-entrypoint.sh`)
   Admin “Scrape jobs now”        ← manual pull per company
```

Do **not** invent a separate public HTTP scrape API for Cloud Run; keep Cloud Run on the management command.

### Per platform

| Scraper file | What it does |
|--------------|--------------|
| `job_service/scrapers/greenhouse.py` | Parse board token from URL → list jobs (optional detail fetch) |
| `job_service/scrapers/lever.py` | Parse site name → one JSON list |
| `job_service/scrapers/ashby.py` | Parse board name → one JSON list |
| `job_service/scrapers/registry.py` | Pick scraper from URL hostname |

### Deduping scraped jobs

- Each job gets an `external_id` like `greenhouse:123`, `lever:abc`, `ashby:uuid`.
- Upsert key: `(source, external_id)` — re-scrape updates; does not duplicate.
- Apply-once (same user + same `Job`): `JobApplication` / future `ApplyTask` `unique_together = (user, job)`.

Cross-posting the **same role** on LinkedIn + Indeed + careers site is a separate problem (company + title cooldown) — planned for matcher, not scrape.

---

## 5. Manual scrape in admin

1. Go to **Job sources**.
2. Open a company (e.g. Notion).
3. Click **Scrape jobs now**.
4. Jobs are upserted; a **Job scraping log** is written.
5. Use **View jobs for this source** / **View scrape logs**.

List action: select multiple sources → **Scrape selected job sources**.

Same code path as:

```bash
poetry run python manage.py scrape_jobs
poetry run python manage.py scrape_jobs --source-id=1
```

---

## 6. What we get from each job

Typically:

- Title, company, location  
- Description (plain / stripped HTML)  
- Application URL (direct apply link into the ATS)  
- Tags (department/team when provided)  
- Posted / published date when the API sends one (`Job.posted_date`)  
- Active flag (e.g. Lever `closed`)

**Size:** one company board is often tens to hundreds of jobs (e.g. large Greenhouse boards can be 400–500+). Quality is high for auto-apply (real company + real apply URL).

**Cost:** public board APIs are free and need no API key. Respect rate limits and ToS; scrape on a schedule, not continuously.

---

## 7. Country / “USA only” / “UK only”

### Can the API search by country?

Mostly **no**:

| Platform | Location filter on API? |
|----------|-------------------------|
| Greenhouse | Not useful (params often ignored) |
| Lever | Partial text `location=` filter (city-ish, not clean “UK”) |
| Ashby | Full board dump |

### What we should do

1. Fetch the full company board.  
2. Optionally **filter after fetch** by location keywords (`US`, `United Kingdom`, `London`, `Sydney`, …).  
3. Later: also filter at **user match** time using Ultimate location prefs.

A future `JobSource` field like `countries` / `location_filter` can store that allowlist for scrape + Cloud Run.

---

## 8. Europe, Australia, New Zealand

Greenhouse / Lever / Ashby are **global**, not US-only. Locations live on each job.

What felt US-heavy was our **seed companies** (Stripe, Datadog, Spotify, Notion), not the platforms.

| Region | With current scrapers | Typical local mega-boards |
|--------|----------------------|---------------------------|
| Europe | EU companies on GH/Lever/Ashby (e.g. Monzo on Greenhouse) | StepStone, Xing, etc. — usually no free clean API |
| Australia / NZ | AU/NZ companies on those ATS when the board URL works | **Seek** dominates — no simple free public API like GH |

To improve regional coverage: **add the right company board URLs**, don’t wait for a “Europe API.”

---

## 9. Limitations (read this carefully)

### We only cover companies on these ATS boards

| Situation | Can we scrape today? |
|-----------|----------------------|
| Public Greenhouse / Lever / Ashby board | Yes |
| Workday, Taleo, iCIMS, custom site | Not yet |
| Only LinkedIn / Indeed / Seek | Not yet |
| Private / no public board | No |

Many tech companies use GH/Lever/Ashby — good start, still a **subset** of all hiring.

### We must know (or discover) company board URLs

There is **no official free directory** of “every Greenhouse customer.”

You cannot today “download all jobs opened this week worldwide” from these APIs. Each call is: *this company’s open roles*.

**Ways to grow the company list**

1. Curated list in admin / `setup_job_sources` (current).  
2. Community GitHub/CSV board lists (verify — they go stale; Notion left Greenhouse for Ashby).  
3. Discover tokens from apply URLs on aggregators (legal/ToS care).  
4. Paid ATS/company mapping data.  
5. Auto-add when users paste GH/Lever/Ashby job links.

**Realistic product path**

| Phase | Approach |
|-------|----------|
| Now | Curated company boards + free APIs |
| Next | Larger verified seed + location filters |
| Later | Optional paid aggregator for breadth |

---

## 10. Cross-posted jobs (same role in many places)

One opening is often posted on:

- Company ATS board  
- LinkedIn  
- Indeed  
- Other sites  

It’s usually the **same hire**, not two jobs.

**Mitigations**

- Same `Job` twice for one user → blocked by `(user, job)` uniqueness.  
- Same company + similar title from different sources within N days → future matcher rule (normalize company/title; cooldown 7–30 days).  
- Still allow **different** roles at the same company.

---

## 11. When a board “fails” (Notion example)

Symptom: scrape error `HTTP 404` on Greenhouse for `notion`.

Cause: company **moved ATS** (Notion → Ashby). Old URL dies.

Fix:

1. Find new careers URL (`jobs.ashbyhq.com/notion`).  
2. Update Job source URL (and ensure we have that scraper — Ashby is supported).  
3. Scrape again.

Always verify board URLs periodically.

---

## 12. How to add a new company (ops checklist)

1. Open their careers page.  
2. Confirm host is Greenhouse, Lever, or Ashby.  
3. Admin → **Add job source**:  
   - Name = company name  
   - URL = board URL  
   - Source type = API Integration  
   - Active = yes  
4. Save → **Scrape jobs now**.  
5. Confirm jobs appear and apply URLs work.

Seed helper:

```bash
poetry run python manage.py setup_job_sources
```

---

## 13. Key files

| Path | Role |
|------|------|
| `job_service/models.py` | `JobSource`, `Job`, `JobScrapingLog`, `JobApplication` |
| `job_service/scrapers/` | Greenhouse, Lever, Ashby + registry |
| `job_service/services/ingestion.py` | Shared scrape + upsert |
| `job_service/management/commands/scrape_jobs.py` | CLI / Cloud Run |
| `job_service/management/commands/setup_job_sources.py` | Default company seeds |
| `job_service/admin.py` | Job sources admin + scrape action |
| `templates/admin/job_service/jobsource/change_form.html` | “Scrape jobs now” UI |
| `scrape-entrypoint.sh` | Cloud Run Job entry |

---

## 14. FAQ

**Are the APIs free?**  
Yes for public board read — no API key for listing jobs.

**Do jobs include dates?**  
When the platform sends them → `Job.posted_date`. Otherwise null.

**Can we throttle scrape to USA or UK only?**  
Not cleanly on the API; filter after fetch (or at match time).

**Do we need every company?**  
No. Coverage grows with the list you maintain. Quality of apply links from ATS boards is the win for auto-apply.

**What’s next after scraping?**  
Phase 2 of the Ultimate plan: match jobs to user job titles → AI fit / resume / cover letter → `ApplyTask` queue for human operators.

---

## 15. One-sentence summary

**Greenhouse, Lever, and Ashby host company career boards; we add companies one by one, scrape their public openings into our database, and use those jobs for Ultimate auto-apply matching — we are not (yet) pulling every job on the internet.**
