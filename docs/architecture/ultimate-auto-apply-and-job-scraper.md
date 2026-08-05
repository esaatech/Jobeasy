# Ultimate Auto-Apply & Job Scraper — Implementation Plan

| Field | Value |
|--------|--------|
| **Document ID** | `ARCH-ULTIMATE-AUTO-001` |
| **Scope** | Job scraping (Phase 1), manual match → ApplyTask admin queue (Phase 2a), AI apply packets (Phase 2b), human ops UI (Phase 3), optional browser automation later (Phase 4+) |
| **Audience** | Engineers, product, and ops implementing scraper infrastructure, GCP scheduling, Ultimate automation, and the operator queue |

This document is the canonical plan for building **job ingestion**, **AI-prepared apply packets**, and **managed applications** (human operators submit forms on behalf of Ultimate users).

**Apply strategy (v1):** AI does matching, resume optimization, and cover letters; **human operators** fill employer web forms and submit. Full browser automation is deferred to a later phase.

---

## 1. Product summary

**Ultimate plan users** opt in to a **managed apply service**:

1. User registers and upgrades to **Ultimate**.
2. User completes resume, **application profile** (contact, work auth, LinkedIn, etc.), sets **target job titles**, location/remote preferences, and enables auto-apply with **explicit consent**.
3. A **job scraper** populates the `Job` table from external sources (Phase 1 — implemented).
4. User completes Ultimate setup: **job titles** + **preferences** (purpose, countries/states, work arrangement). Daily apply cap is **admin-managed**.
5. A **manual matcher** (CLI / admin action first; Cloud Scheduler later) finds Ultimate users, matches active scraped jobs to titles + location/work arrangement, and creates **`ApplyTask`** rows with the job apply URL.
6. Operators open each task’s URL, apply on the employer site, and mark **applied** / **skipped** in admin (v1). AI resume/cover packets and a dedicated ops UI come after this loop works.
7. User receives a digest notification when applications are recorded.

**Who qualifies:** users with an active `subscriptions.UserSubscription` where `plan.name == 'Ultimate'` and `status == 'ACTIVE'`.

### Manual-first Phase 2 (current next slice)

Prove human-in-the-loop **before** AI packets or Cloud Scheduler:

1. **`ApplyTask` model** — user, job, `application_url`, status (`queued` / `applied` / `skipped`), timestamps.
2. **`job_matcher`** — for each Ultimate user with setup done: match active jobs by titles + location/work arrangement; respect admin `max_applications_per_day`; skip already-queued/applied.
3. **Manual run** — `manage.py run_ultimate_auto_apply` and/or admin action (no Cloud Scheduler yet).
4. **Admin queue** — list tasks with link to open the job URL; mark applied / skipped.

That proves the loop end-to-end. **After it works:** AI packets (resume/cover letter), then ops UI polish, then Cloud Run.

### Why human-in-the-loop first

| Full browser automation | Human-in-the-loop (v1) |
|-------------------------|-------------------------|
| Breaks on every ATS change | Operators adapt to any form |
| CAPTCHA blocks bots | Human solves CAPTCHA |
| Months to build per-ATS adapters | Ops queue shippable in weeks |
| ~60–80% success on easy ATS | ~95%+ with trained operators |
| High engineering cost | Higher ops cost, predictable quality |

Automate submission (email, Playwright) only **after** the queue is running and you know which ATS patterns are worth automating.

---

## 2. Where code lives (app placement)

### Phase 1 — Job scraper → `job_service` (no new app)

Models already exist in `job_service`:

| Model | Purpose |
|-------|---------|
| `JobSource` | Websites, APIs, RSS feeds to scrape |
| `Job` | Normalized job postings |
| `JobScrapingLog` | Per-run scrape history |

Proposed file structure:

```
job_service/
  scrapers/
    base.py           # BaseScraper interface
    greenhouse.py     # First real source (API)
    lever.py          # Second source
    registry.py       # source_type → scraper class
  services/
    ingestion.py      # normalize, dedup, upsert Job rows
  management/commands/
    scrape_jobs.py    # CLI entry point
```

### Phase 2a — Manual match → ApplyTask → `automation` app (**next**)

Match Ultimate users to scraped jobs and queue URL tasks for operators (no AI yet):

```
automation/
  models.py                    # ApplyTask (minimal) + UltimateAutomationProfile
  data/locations.py            # US / CA / GB catalog (already shipped)
  services/
    job_matcher.py             # titles + location + work arrangement + daily cap
  management/commands/
    run_ultimate_auto_apply.py # manual CLI first; Scheduler later
  admin.py                     # ApplyTask queue: open URL, mark applied/skipped
```

### Phase 2b — AI apply packet → same `automation` app (after 2a)

```
automation/
  services/
    application_builder.py     # fit gate → cover letter → resume optimize
    apply_packet.py            # assemble operator-facing packet
  # Extend ApplyTask with PDF / short-answer fields; then Cloud Run schedule
```

### Phase 3 — Human operator queue → `automation` app

Staff dashboard for claiming tasks and recording submissions:

```
automation/
  views/
    ops_queue.py               # list / claim / complete / skip tasks
  templates/automation/ops/    # operator UI
  permissions.py               # Operator group, not full admin
```

### Phase 4+ — Optional automated submission (later)

Only after human queue is stable:

```
automation/
  adapters/
    base.py
    email_adapter.py
    greenhouse_adapter.py      # Playwright
    playwright_adapter.py
  services/
    application_submitter.py   # try bot first → fallback to human queue
```

| Phase | App | Responsibility |
|-------|-----|----------------|
| **1** | `job_service` | Scrape → write `Job` ✅ |
| **2a** | `automation` | Match → `ApplyTask` + admin queue (manual CLI) ← **next** |
| **2b** | `automation` | AI packets on tasks; then schedule Cloud Run |
| **3** | `automation` | Dedicated ops queue UI + proof + notify |
| **4+** | `automation` | Email/Playwright adapters to reduce human load |

---

## 3. End-to-end workflow (human-in-the-loop)

```mermaid
flowchart TD
    subgraph onboarding [User Onboarding]
        A[Register] --> B[Upgrade to Ultimate]
        B --> C[Complete resume + ApplicationProfile]
        C --> D[Set target job titles + preferences]
        D --> E[Enable auto-apply + consent]
    end

    subgraph scrape [Job Scraper - Phase 1]
        F[Cloud Scheduler triggers scrape job] --> G[Scrape active JobSources]
        G --> H[Upsert Job records + JobScrapingLog]
    end

    subgraph ai [AI Packet - Phase 2]
        I[Cloud Scheduler every 4hrs] --> J[Get active Ultimate users]
        J --> K[Match jobs to user targets]
        K --> L{Already applied or queued?}
        L -->|No| M[AI fit check]
        M --> N[Optimize resume + cover letter]
        N --> O[Create ApplyTask queued]
        L -->|Yes| P[Skip]
    end

    subgraph human [Human Operator - Phase 3]
        O --> Q[Ops dashboard queue]
        Q --> R[Operator claims task]
        R --> S[Open apply URL - optional VPN]
        S --> T[Fill form + upload PDFs]
        T --> U[Submit + upload screenshot]
        U --> V[Mark applied + notify user]
    end

    onboarding --> scrape
    scrape --> ai
    ai --> human
```

### Division of labor

| Step | Who |
|------|-----|
| Scrape jobs | Cron / Cloud Run Job |
| Match to user title/prefs | Rules + optional AI |
| Fit gate (skip bad matches) | AI |
| Resume optimize | AI |
| Cover letter + short answers | AI |
| Open apply URL | **Human operator** |
| Fill form fields | **Human operator** |
| CAPTCHA / login / multi-step forms | **Human operator** |
| Upload resume / cover letter PDFs | **Human operator** |
| Submit application | **Human operator** |
| Record proof + notify user | **Human operator** (via ops UI) |

Typical operator time: **2–5 minutes per application** with a complete apply packet.

---

## 4. Ultimate user requirements

Before automation runs, each Ultimate user must have:

| Requirement | Model / location | Status |
|-------------|------------------|--------|
| Active Ultimate plan | `subscriptions.UserSubscription` | Exists |
| At least one resume | `resume_builder.Resume` | Exists |
| **Application profile** (phone, address, LinkedIn, work auth) | **New `ApplicationProfile`** | Missing |
| Target job title(s) | **New field needed** | Missing |
| Auto-apply opt-in | **New field needed** | Missing |
| Default resume for automation | **New field needed** | Missing |
| Location / remote / salary prefs | `UserJobPreferences` | Exists |
| Explicit consent (authorize apply on user's behalf) | **New field or UI step** | Missing |

### New fields to add (Phase 2)

**Canonical model:** `automation.UltimateAutomationProfile` (created on Ultimate setup).

```python
primary_titles = models.JSONField(default=list)
# Core roles, e.g. ["Backend Engineer", "Software Engineer"]

related_titles = models.JSONField(default=list)
# Adjacent synonyms for Stage 2, e.g. ["Platform Engineer", "SWE"]

exclude_titles = models.JSONField(default=list)
# Never match, e.g. ["Data Scientist", "Engineering Manager"]

auto_apply_enabled = models.BooleanField(default=False)
default_resume = models.ForeignKey('resume_builder.Resume', ...)
title_family_confirmed = models.BooleanField(default=False)
max_applications_per_day = models.IntegerField(default=10)
```

**Stage 2 matching uses `title_family` = primary + related only.** Skills are not used to admit jobs (Stage 3 AI fit owns skills / JD). `exclude_titles` is a hard reject.

**Ultimate onboarding:** after checkout success → `/automation/ultimate/setup/`  
- Suggest titles from resume via AI (`suggest_title_family`)  
- User edits and confirms before `auto_apply_enabled`

### ApplicationProfile (Phase 2 — for operator form fill)

Web apply forms require more than a resume. Store once per user:

```python
class ApplicationProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    legal_first_name = models.CharField(max_length=100)
    legal_last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()  # may differ from login email
    address_line1 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    work_authorization = models.CharField(max_length=50)  # e.g. us_citizen, h1b, etc.
    requires_sponsorship = models.BooleanField(default=False)
    desired_salary_min = models.DecimalField(null=True, blank=True, ...)
    desired_salary_max = models.DecimalField(null=True, blank=True, ...)
    hear_about_us_default = models.CharField(max_length=100, default='Job board')
    eeo_opt_in = models.BooleanField(default=False)  # only fill EEO if user opts in
    apply_via_vpn_region = models.CharField(max_length=50, blank=True)  # e.g. US-CA
    consent_to_apply_on_behalf = models.BooleanField(default=False)
    consent_signed_at = models.DateTimeField(null=True, blank=True)
```

### ApplyTask (Phase 2a minimal → expand in 2b/3)

**Phase 2a (manual queue — ship first):**

```python
class ApplyTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey('job_service.Job', on_delete=models.CASCADE)
    application_url = models.URLField(max_length=500)  # snapshot of job.application_url
    status = models.CharField(max_length=20, choices=[
        ('queued', 'Queued'),
        ('applied', 'Applied'),
        ('skipped', 'Skipped'),
    ], default='queued')
    skip_reason = models.CharField(max_length=50, blank=True)
    operator_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'job']
```

**Later (Phase 2b/3):** add claim/assigned_to, AI packet fields (`resume_pdf`, `cover_letter_pdf`, `ai_short_answers`), proof screenshot, confirmation URL, priority.

On **applied**, also create `job_service.JobApplication` and notify the user.

### Ultimate subscription check

```python
from subscriptions.models import UserSubscription

def is_ultimate_subscriber(user):
    sub = UserSubscription.objects.filter(
        user=user,
        plan__name__iexact='Ultimate',
        status='ACTIVE',
    ).select_related('plan').first()
    return sub is not None and sub.is_active
```

---

## 5. Job matching logic

Matching uses `UltimateAutomationProfile` (not only legacy `UserJobPreferences`):

```python
def job_matches_user(job, profile: UltimateAutomationProfile):
    title_lower = job.title.lower()
    location_lower = (job.location or '').lower()

    # Title match: any title-family string appears in job title
    # (exclude_titles hard-reject if present in job title)
    if any(ex.lower() in title_lower for ex in (profile.exclude_titles or [])):
        return False

    title_match = any(
        target.lower() in title_lower
        for target in profile.title_family
    )
    if not title_match:
        return False

    # Location: country name/code or city substring in job.location
    # (preferred_countries from setup step 2; city optional)
    # Work arrangements: remote/hybrid/onsite heuristics on job.location / tags

    return True
```

Skip jobs already represented by an `ApplyTask` or `job_service.JobApplication` for that user.

Enforce daily cap per user (admin field on profile):

```python
today_count = ApplyTask.objects.filter(
    user=user,
    created_at__date=timezone.localdate(),
    status__in=['queued', 'applied'],
).count()
if today_count >= profile.max_applications_per_day:
    return  # stop creating more tasks for this user today
```

**Phase 2a:** matcher writes `ApplyTask(status='queued', application_url=job.application_url)` only.  
**Phase 2b:** after match, optionally run AI packet generation before operators pick up the task.

---

## 6. AI pipeline (reuse existing dashboard logic)

Extract from `dashboard/views.py` (`evaluate_job_fit`, `generate_job_application`) into `automation/services/application_builder.py`.

| Step | Existing service | Action |
|------|------------------|--------|
| Fit check | `ai_service.fit_gate` | Skip weak matches (optional) |
| Resume optimize | `ai_service.resume_optimization` | Create optimized `Resume` copy + PDF |
| Cover letter | `ai_service.cover_letter` | Generate text + optional PDF |
| Short answers | `ai_service` (new or why-apply) | Draft "Why this company?" etc. |
| Queue task | `automation.ApplyTask` | Status `queued` — **no auto-submit** |
| After human applies | `job_service.JobApplication` | Status `applied` + proof on `ApplyTask` |

See also: `docs/architecture/dashboard-job-application-pipeline.md` (`ARCH-DASH-JA-001`).

---

## 6b. Operator workflow (Phase 3)

### Apply packet contents

Each `ApplyTask` exposes one page for operators with:

- Job title, company, location, `application_url` (open in new tab)
- User `ApplicationProfile` (copy-paste fields)
- Optimized resume PDF + cover letter (text + PDF)
- AI-generated short answers for common free-text questions
- Checklist: work auth, sponsorship, salary range, VPN region if set

### Ops dashboard (wireframe)

```
┌─────────────────────────────────────────────────────────┐
│ Apply Queue (12 pending)                                │
├─────────────────────────────────────────────────────────┤
│ [P1] Jane D. → Senior Python Dev @ Stripe               │
│      URL: boards.greenhouse.io/...  |  Due: 2h          │
│      [Open packet] [Claim] [Mark applied] [Skip]        │
├─────────────────────────────────────────────────────────┤
│ [P2] John S. → Backend Engineer @ Datadog               │
│      ...                                                │
└─────────────────────────────────────────────────────────┘
```

### Operator steps

1. **Claim** task (prevents double work).
2. Open **apply packet** — all fields and files in one view.
3. Open `application_url` in browser (use VPN if `apply_via_vpn_region` is set).
4. Fill form, upload PDFs, submit.
5. **Mark applied** — paste confirmation URL, upload screenshot.
6. Or **Skip** with reason: `captcha`, `login_required`, `job_closed`, `geo_block`, `other`.

### Staff access

- Django users in an **Operator** group (`is_staff` optional).
- Permissions: view/claim/complete `ApplyTask` only — no access to billing or unrelated admin.
- Audit log: who claimed, who completed, timestamps.

### VPN / SOCKS / proxy (operator-side)

Operators use **their own browser** with VPN — not Playwright on Cloud Run.

| Scenario | Approach |
|----------|----------|
| Job requires US IP | Operator VPN to US (document in SOP) |
| User requested specific region | `ApplicationProfile.apply_via_vpn_region` shown on packet |
| Datacenter IP blocked | Residential VPN or dedicated VM with residential proxy |
| Scale ops team | Shared ops VMs with consistent US egress IP |

**Compliance:** Ultimate onboarding consent must state that Jobeasy (or its operators) may apply on the user's behalf, including via VPN matching the user's location when required. Do not misrepresent applicant location fraudulently.

### Skip reasons (track for automation prioritization)

| Reason | Meaning | Future automation |
|--------|---------|-------------------|
| `captcha` | Bot block | Stay human |
| `login_required` | Account needed | Human or credential vault (later) |
| `job_closed` | Listing removed | Auto-detect + deactivate `Job` |
| `geo_block` | Region restricted | VPN SOP |
| `email_only` | mailto: apply | Phase 4 email adapter |
| `other` | Free text in `operator_notes` | — |

---

## 7. Scrape frequency & cost

### What actually costs money

| Cost driver | Relative cost | Notes |
|-------------|---------------|-------|
| **AI per application** (fit + resume + cover letter) | **Highest** | ~$0.10–$0.50+ per job |
| **Browser scraping** (Playwright) | Medium–high | Memory, proxies, CAPTCHA |
| **Paid job APIs** (Adzuna, JSearch) | Medium | Per-request or monthly quota |
| **Free ATS APIs** (Greenhouse, Lever) | **Low** | Mostly compute + rate limits |
| **RSS / JSON feeds** | **Very low** | Cheap to poll often |

**Key insight:** scrape frequency matters, but **AI application volume** is the dominant cost for Ultimate users.

### Hourly vs daily

| Frequency | Verdict |
|-----------|---------|
| **Hourly (24×/day)** | Too aggressive for most sources; expensive with Playwright; many runs return zero new jobs |
| **Once daily** | Too slow for a premium auto-apply product (up to 24h delay) |
| **4×/day (recommended)** | Good balance of freshness and cost |

### Recommended tiered scraping

| Source type | Scrape frequency | Why |
|-------------|------------------|-----|
| **ATS APIs** (Greenhouse, Lever, Ashby) | Every 4–6 hours | Cheap, stable |
| **RSS / JSON feeds** | Every 2–4 hours | Very cheap to poll |
| **Paid aggregator API** | 2–4×/day | Respect quota |
| **Playwright / heavy scrape** | 1–2×/day (off-peak) | Expensive and fragile |

### Recommended production schedule

```
02:00 UTC  Full scrape (all sources)       — overnight batch
08:00 UTC  API + RSS refresh
14:00 UTC  API + RSS refresh
20:00 UTC  API + RSS refresh
```

Ultimate auto-apply runs **every 4 hours** (reads DB only; does not scrape):

```
00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC
```

Worst-case delay from job posting to apply attempt: **~4 hours** (after next scrape + apply cycle).

### Rough cost example

Assume **100 Ultimate users**, **10 applies/user/day**, **4 scrapes/day**:

| Item | Estimate |
|------|----------|
| Scraping (API-based, 4×/day) | ~$5–30/mo |
| Scraping (Playwright hourly) | $200–1000+/mo |
| AI (100 × 10 × ~$0.20) | **~$600/mo** |
| Human ops (100 × 10 × ~3 min × $5/hr) | **~$250/mo+** (varies by team) |

### Ultimate plan economics — caps are required

At **$49.99/mo** Ultimate, unlimited daily applies is not viable with human operators.

| Cap | Example |
|-----|---------|
| Per day | 5–10 applications per user |
| Per month | 50–100 included; overage as add-on |
| Positioning | "We apply for you" (managed), not unlimited spray |

Rough operator cost: **~$0.15–0.40 per apply** (3 min @ $3–8/hr). Model pricing and caps before scaling marketing.

---

## 8. GCP architecture

### Current state

- One **Cloud Run service** runs the web app (`uvicorn` via `entrypoint.sh`).
- Same Docker image (`Dockerfile` at repo root).

### Recommended pattern: Cloud Run Jobs + Cloud Scheduler

Use **Cloud Run Jobs** for batch/cron work — not a second always-on web service.

```mermaid
flowchart LR
    A[Cloud Scheduler] -->|schedule| B[Cloud Run Job]
    B -->|same Docker image| C[python manage.py scrape_jobs]
    C --> D[(Cloud SQL / Postgres)]
    E[Cloud Run Service - web] --> D
```

| Component | Role |
|-----------|------|
| **Cloud Run Service** (existing) | Web app for users |
| **Cloud Run Job** (new) | Runs scraper on schedule; exits when done |
| **Cloud Scheduler** | Triggers the job |
| **Same Docker image** | One build, different commands per job |

### Why Cloud Run Job > second Cloud Run service

| Approach | Pros | Cons |
|----------|------|------|
| **Cloud Run Job** | Built for batch; runs and exits; no HTTP endpoint to secure | Slightly different deploy from service |
| **Second Cloud Run service** + HTTP cron | Familiar HTTP model | Must secure endpoint; cold starts; wrong abstraction for one-shot tasks |
| **Celery on GCE/GKE** | Fine at scale | More infra than needed for Phase 1 |

### Target GCP layout

```
┌─────────────────────────────────────────────────────────┐
│                    GCP Project                          │
│                                                         │
│  Cloud Scheduler                                        │
│    ├── every 6hrs  → Cloud Run Job: scrape_jobs       │
│    └── every 4hrs  → Cloud Run Job: ultimate_apply    │
│                                                         │
│  Cloud Run Service (web)     Cloud SQL (Postgres)       │
│    └── uvicorn / users  ←──→  Job, JobSource, User...   │
│                                                         │
│  Same Docker image for Service + both Jobs              │
└─────────────────────────────────────────────────────────┘
```

### Phase 1: scrape job entrypoint

Lightweight entrypoint — skip web bootstrap on every scrape run:

```bash
#!/bin/sh
# scrape-entrypoint.sh
set -e
export DJANGO_SETTINGS_MODULE=jobeas.settings
export SKIP_BOOTSTRAP_DATA=1

python manage.py scrape_jobs "$@"
```

Cloud Run Job command override:

```yaml
command: ["python", "manage.py", "scrape_jobs"]
args: ["--source-type=api"]
```

### Cloud Scheduler example

```bash
# Trigger Cloud Run Job every 6 hours (good starting point)
gcloud scheduler jobs create http scrape-jobs-trigger \
  --schedule="0 */6 * * *" \
  --uri="https://REGION-run.googleapis.com/.../jobs/scrape-jobs:run" \
  --oauth-service-account-email=scheduler@PROJECT.iam.gserviceaccount.com
```

### Schedule recommendations by environment

| Environment | Scrape schedule | Apply schedule |
|-------------|-----------------|----------------|
| **Dev / testing** | Every 6 hours | Every 4 hours (or manual) |
| **Production v1** | 4×/day (02, 08, 14, 20 UTC) | Every 4 hours |
| **Hourly scrape** | Only after measuring empty runs on API/RSS sources | — |

---

## 9. Phased implementation checklist

### Phase 1 — Job scraper (start here)

**App:** `job_service`

- [x] Create `job_service/scrapers/` module with `BaseScraper` interface
- [x] Implement Greenhouse, Lever, and Ashby public board scrapers
- [x] Create `job_service/services/ingestion.py` (normalize, dedup by `external_id`, upsert)
- [x] Deactivate jobs whose `external_id` is missing from a successful scrape
- [x] Create `management/commands/scrape_jobs.py` + `setup_job_sources.py` (US + CA/EU seeds)
- [x] Wire `JobScrapingLog` on every run
- [x] Admin scrape actions + show `application_url` on Job admin
- [x] Add `scrape-entrypoint.sh` for Cloud Run Job
- [ ] Deploy Cloud Run Job + Cloud Scheduler (4–6×/day to start)
- [ ] Optional: verify jobs appear in public job listings UI

**GCP deliverables:**

- [ ] Cloud Run Job: `scrape-jobs`
- [ ] Cloud Scheduler trigger
- [ ] Same Docker image as web service
- [ ] Shared `DATABASE_URL_PROD` / Cloud SQL access

---

### Phase 2a — Manual match → ApplyTask queue (**next**)

**App:** `automation` — no AI packets, no Cloud Scheduler yet.

Goal: turn setup prefs + scraped jobs into apply tasks operators can work from admin.

- [x] Create `automation` app + register in `INSTALLED_APPS`
- [x] Ultimate setup wizard: title family (primary / related / exclude) + default resume
- [x] Ultimate setup step 2: search purpose, US/CA/UK locations API, work arrangements
- [x] `max_applications_per_day` admin-managed (not user-editable in setup)
- [x] Add **`ApplyTask`** model: user, job, `application_url`, status (`queued` / `applied` / `skipped`), timestamps; unique `(user, job)`
- [ ] Implement `automation/services/job_matcher.py`
  - Gate: Ultimate (or Test) `ACTIVE` + `auto_apply_enabled` + setup/titles confirmed
  - Match: title family vs active `Job.title`; location vs preferred countries/city; work arrangements vs job location text
  - Cap: admin `max_applications_per_day` (count queued + applied today)
  - Skip: already queued/applied for that user+job; inactive jobs
- [ ] Create `management/commands/run_ultimate_auto_apply.py` (manual CLI)
- [ ] Optional: JobSource/admin-style action to run matcher for one user or all
- [ ] **Admin queue:** list `ApplyTask` with openable job URL; actions to mark **applied** / **skipped**
- [ ] On applied: create `job_service.JobApplication` (minimal; notify later if needed)

**Exit criteria:** operator can run matcher manually, open a matched job URL, apply on the ATS site, and mark the task done in admin.

---

### Phase 2b — AI apply packet generation (after 2a works)

**App:** `automation`

- [ ] Add `ApplicationProfile` model + onboarding fields for form fill (phone, LinkedIn, work auth, consent)
- [ ] Extract dashboard AI pipeline → `automation/services/application_builder.py`
- [ ] Implement `apply_packet.py` (resume PDF, cover letter PDF, profile fields)
- [ ] Attach packet artifacts to `ApplyTask` before operator opens the URL
- [ ] Gate + daily cap already from 2a; keep enforcing them
- [ ] Deploy Cloud Run Job + Scheduler (every 4 hours) **only after** manual CLI path is trusted

**GCP deliverables (defer until 2a is solid):**

- [ ] Cloud Run Job: `ultimate-auto-apply`
- [ ] Cloud Scheduler: `0 */4 * * *`

---

### Phase 3 — Human operator queue (primary submit path)

**App:** `automation` — dedicated ops UI beyond Django admin

- [ ] Operator group + permissions
- [ ] Ops queue list view (filter by status, priority, SLA)
- [ ] Apply packet detail page (single-page copy/paste + file downloads)
- [ ] Claim / release task actions
- [ ] Mark applied (confirmation URL + screenshot upload)
- [ ] Skip with reason codes
- [ ] On applied: create `job_service.JobApplication`, notify user
- [ ] User-facing status: Queued → In progress → Applied / Skipped
- [ ] Operator SOP doc (VPN, PII handling, quality checks)
- [ ] Metrics: queue depth, time-to-apply, skip rate by reason

**Ops deliverables:**

- [ ] VPN SOP for geo-restricted jobs
- [ ] NDA / data handling for operators with PII access
- [ ] Spot-check process on submitted applications

---

### Phase 4 — Optional automated submission (reduce human load)

**App:** `automation`

- [ ] Email apply adapter (`email_utility`) for `mailto:` jobs
- [ ] Greenhouse / Lever Playwright adapters (bot tries first)
- [ ] On bot failure → re-queue for human (`ApplyTask` status `queued`)
- [ ] `AutomationRun` model for per-user daily run logs
- [ ] Unify subscription gating (`subscriptions.UserSubscription` vs `job_service.UserSubscription`)

**Only automate ATS patterns with high volume and high bot success rate** — use skip-reason analytics from Phase 3 to prioritize.

---

### Phase 5 — Hardening & scale

- [ ] Review-before-apply mode for new Ultimate users (optional)
- [ ] Browser extension for operators (auto-fill common fields; human still clicks Submit)
- [ ] Per-user proxy / region routing (advanced)
- [ ] Credential vault for login-required ATS (high risk — defer)

---

## 10. Scraper implementation sketch

### Management command

```python
# job_service/management/commands/scrape_jobs.py
class Command(BaseCommand):
    help = "Scrape active job sources and upsert into Job table"

    def add_arguments(self, parser):
        parser.add_argument('--source-type', choices=['api', 'rss', 'website', 'all'], default='all')
        parser.add_argument('--source-id', type=int, help='Scrape a single JobSource by ID')

    def handle(self, *args, **options):
        from job_service.services.ingestion import run_scrape_cycle
        run_scrape_cycle(
            source_type=options['source_type'],
            source_id=options.get('source_id'),
        )
```

### Ingestion service

```python
# job_service/services/ingestion.py
def run_scrape_cycle(source_type='all', source_id=None):
    qs = JobSource.objects.filter(is_active=True)
    if source_id:
        qs = qs.filter(pk=source_id)
    if source_type != 'all':
        qs = qs.filter(source_type=source_type)

    for source in qs:
        log = JobScrapingLog.objects.create(source=source, status='running')
        try:
            scraper = get_scraper(source)  # registry.py
            raw_jobs = scraper.fetch()
            added, updated = upsert_jobs(source, raw_jobs)
            log.jobs_found = len(raw_jobs)
            log.jobs_added = added
            log.jobs_updated = updated
            log.status = 'completed'
            source.last_scraped = timezone.now()
            source.save(update_fields=['last_scraped'])
        except Exception as exc:
            log.status = 'failed'
            log.error_message = str(exc)
        finally:
            log.completed_at = timezone.now()
            log.save()
```

### Source priority (implement in this order)

| Priority | Source | Method |
|----------|--------|--------|
| 1 | Greenhouse public boards | API |
| 2 | Lever public postings | API |
| 3 | RSS / JSON feeds | HTTP poll |
| 4 | Paid aggregator (Adzuna, JSearch) | Paid API |
| 5 | Generic ATS sites | Playwright (last resort) |

Avoid scraping LinkedIn/Indeed in v1 (ToS and anti-bot risk).

---

## 11. Apply submission strategy

### v1 (Phase 3): Human operator — all web forms

| URL / form type | Method | Phase |
|-----------------|--------|-------|
| Greenhouse / Lever / Workday / any ATS web form | **Human operator** via ops queue | **3** |
| `mailto:` links | Human or email adapter | 3 / 4 |
| CAPTCHA or login walls | Human | 3 |
| LinkedIn Easy Apply | Skip or human only | 3 |

### Later (Phase 4+): Bot-first with human fallback

```python
def submit_application(user, job, artifacts):
    adapter = get_apply_adapter(job.application_url)
    if adapter and adapter.can_automate(job.application_url):
        result = adapter.apply(user, job, artifacts)
        if result.success:
            return result
    # Fallback: create or re-queue ApplyTask for human
    return queue_for_operator(user, job, artifacts, reason=result.error)
```

| URL type | Automated method | Phase |
|----------|------------------|-------|
| `mailto:` links | `email_utility` | 4 |
| Greenhouse / Lever apply URLs | Playwright adapter | 4 |
| Generic ATS forms | Generic Playwright (low success) | 5 |
| LinkedIn Easy Apply | Skip | — |

---

## 12. Important constraints

1. **Legal / ToS** — prefer licensed APIs for job ingestion; operators apply manually on employer sites.
2. **CAPTCHA & 2FA** — human-in-the-loop handles these in v1; do not fight CAPTCHA with bots early.
3. **Quality over quantity** — daily cap + fit gate prevents spam applications.
4. **PII & operator access** — operators see real user data; require NDAs, least-privilege access, audit logs.
5. **VPN / location** — document in consent and SOP; apply honestly on behalf of the user.
6. **Duplicate subscriptions** — unify `subscriptions.UserSubscription` and `job_service.UserSubscription` before billing automation.
7. **Idempotency** — `unique_together` on `ApplyTask` and `JobApplication` for `(user, job)`; safe to retry cron.
8. **Two crons** — scraper and apply-packet generation are separate Cloud Run Jobs.
9. **Ops scale** — 100 Ultimate users × 10 applies/day = 1,000 human applies/day; staff accordingly.

---

## 13. Related documents & files

| Resource | Path |
|----------|------|
| **Job scraper guide (how GH/Lever/Ashby work)** | `docs/architecture/job-scraper-guide.md` |
| Dashboard AI pipeline | `docs/architecture/dashboard-job-application-pipeline.md` |
| Job service models | `job_service/models.py` |
| Subscription models | `subscriptions/models.py` |
| AI platform | `ai_service/docs/AI_PLATFORM.md` |
| Docker / Cloud Run entrypoint | `Dockerfile`, `entrypoint.sh` |
| Internal overview | `docs/INTERNAL_TECHNICAL_OVERVIEW.md` |

---

## 14. Quick reference

| Question | Answer |
|----------|--------|
| New app for Phase 1? | **No** — use `job_service` |
| New app for Phase 2–3? | **Yes** — `automation` |
| Next build slice? | **Phase 2a** — `ApplyTask` + `job_matcher` + manual CLI + admin queue (no AI packets / no Scheduler yet) |
| Who submits applications in v1? | **Human operators** (admin queue first, ops UI in Phase 3) |
| GCP pattern for scraper? | **Cloud Run Job** + **Cloud Scheduler** (same Docker image) |
| Scrape how often in prod? | **4×/day** to start (not hourly, not once daily) |
| Apply packet cron how often? | Manual CLI first; **every 4 hours** only after 2a is trusted |
| Who gets automation? | **Ultimate plan only** (`plan.name == 'Ultimate'`, `status == 'ACTIVE'`) |
| Daily apply cap? | Admin field `max_applications_per_day` on `UltimateAutomationProfile` |
| Biggest cost levers? | **Applications per user per day** (AI + human ops) |
| When to add Playwright apply? | **Phase 4** — after ops queue metrics show which ATS to automate |
| VPN for applies? | **Operator browser + VPN** per SOP; not server-side scraping |
