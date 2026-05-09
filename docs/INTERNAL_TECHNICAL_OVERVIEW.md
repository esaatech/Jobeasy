**Public-facing overview:** For customer-safe information about Jobeas (what we do, AI in plain language, privacy pointers), see [`JOBEAS_KNOWLEDGE_BASE.md`](./JOBEAS_KNOWLEDGE_BASE.md) in this folder.

---

# Jobeas — Internal technical overview

This document summarizes **Jobeas** for engineering, support, onboarding, and internal AI assistants. It is derived from the product codebase and is **not** intended for public distribution (no secrets, but includes implementation detail).

---

## 1. What is Jobeas?

**Jobeas** is a web application that helps people build **resumes** and **cover letters**, explore **job-related workflows**, and use **AI-assisted** tools for drafting and optimization. It is implemented as a **Django** project with multiple apps, optional **real-time chat** (WebSockets via **Django Channels**), and integrations with AI providers for assistant-style features.

**Production domains** (from project settings) include `jobeas.com` / `www.jobeas.com` and Cloud Run–style hosts used for development and deployment.

---

## 2. Technology stack (high level)

| Layer | Notes |
|--------|--------|
| **Backend** | Django 5.x, Django REST Framework |
| **Real-time** | Django Channels (WebSockets) for live chat-style flows |
| **Database** | PostgreSQL (typical production setup; see `README.md` for architecture notes) |
| **Caching / async** | Redis mentioned in project docs for caching and related use |
| **Static / ASGI** | ASGI deployment (e.g. Uvicorn); WhiteNoise for static files |
| **Frontend** | Server-rendered templates, Tailwind (CDN), HTMX, jQuery in places |
| **Rich text** | django-ckeditor-5 |
| **PDF** | Dedicated `pdf_generator` app |
| **Email** | `email_utility` app for outbound mail flows |

---

## 3. Major Django apps (what each area does)

| App | Purpose |
|-----|---------|
| **home** | Marketing site: home, about, contact, careers, legal pages, newsletter/contact APIs, **resume templates landing** (`/landing_page/resumes/`) |
| **resume_builder** | Create/edit resumes, templates, upload, optimize, AI assistant chat endpoints, downloads, previews |
| **coverletter** | Job-specific cover letter flow, PDFs, saved cover letters |
| **job_service** | Job listings, applications, interview prep, preferences, application status |
| **dashboard** | User dashboard and job-application aggregation |
| **authentication** | Login, registration, logout (`/auth/…`) |
| **subscriptions** | Plans and pricing |
| **settings** | User profile / account settings |
| **ai_service** | AI-related API routes under `/ai-service/` |
| **question_answer** | Q&A / chat-style UI (`/qa/`) |
| **email_utility** | Email-related endpoints (`/email/`) |
| **utils** | Shared utilities (`/utils/`) |
| **pdf_generator** | PDF generation support |

---

## 4. URL map (user-facing paths)

Prefix is the site root unless noted.

### Marketing & legal (home)

- `/` — Home / marketing landing  
- `/about/`, `/contact/`, `/careers/`  
- `/terms/`, `/privacy/`  
- `/landing_page/resumes/` — Featured resume templates marketing page  

### Resumes (`/resume/`)

- `/resume/` or `/resume/create-resume/` — Create resume  
- `/resume/edit-resume/<id>/` — Edit existing resume  
- `/resume/my-resumes/` — List user resumes  
- `/resume/resume_templates/` — Template gallery page  
- `/resume/preview/<template_id>/` — HTML preview of a template  
- `/resume/download/` — Download flows  
- `/resume/optimize/` — Resume optimization  
- `/resume/upload-resume/` — Upload resume  
- `/resume/ai-assistant/` — AI assistant UI (resume context)  

### Cover letters (`/coverletter/`)

- `/coverletter/job-cover-letter/` — Main job cover letter tool  
- `/coverletter/my-cover-letters/` — Saved cover letters  

### Jobs & applications (`/job-service/`)

- `/job-service/` — Main job application service entry  
- `/job-service/jobs/` — Job listings  
- `/job-service/interview-prep/` — Interview preparation  
- `/job-service/my-applications/` — User applications  

### Dashboard (`/dashboard/`)

- `/dashboard/` — User dashboard  

### Authentication (`/auth/`)

- Login, register, logout (exact paths live in `authentication/urls.py`)  

### Other

- `/subscriptions/` — Pricing / subscription flows  
- `/settings/` — User settings  
- `/qa/` — Question/answer or chat features  
- `/admin/` — Django admin  

---

## 5. Resume templates (product concept)

- Templates are defined in code (e.g. **`resume_builder/template_registry.py`**) with IDs such as **professional**, **modern**, **creative**.  
- Each template has metadata: name, description, optional **thumbnail** path under `static/` (gallery cards and marketing use `thumbnail_static`, often SVG), **featured** flags for marketing pages.  
- The marketing page **`/landing_page/resumes/`** shows up to a small number of **featured** templates with previews and “Use this template” actions that deep-link into resume creation with a `template` query parameter.

---

## 6. AI features (conceptual)

- **Resume builder**: chat/API endpoints for AI-assisted help while editing (see `resume_builder` URLs: `api/chat/`, AI assistant routes).  
- **Broader AI**: `ai_service` exposes additional AI workflows under `/ai-service/`.  
- Architecture diagrams in the repo **`README.md`** describe WebSocket flows, OpenAI-style assistants, and **function calling** (e.g. saving content, structured actions).  

*Exact models, API keys, and rate limits belong in ops/env documentation—not in this file.*

---

## 7. Subscriptions

- The **`subscriptions`** app manages plans; the UI can gate certain actions (e.g. resume updates) — see views such as `check_resume_update_access` in `resume_builder` and frontend scripts that read plan context.

---

## 8. Internationalization

- Client-side i18n (e.g. **i18next**) loads merged JSON from `job_service`, `home`, and `resume_builder` static language files for multiple locales.

---

## 9. Deployment notes (non-secret)

- **DEBUG** and **SECRET_KEY** come from environment variables.  
- **CSRF_TRUSTED_ORIGINS** includes production hosts and Cloud Run patterns.  
- **Static files**: WhiteNoise middleware is enabled.  
- Container / process: typical ASGI + workers; see `Dockerfile` / `entrypoint.sh` in the repo for this project’s pattern.

---

## 10. Support & troubleshooting topics

| Topic | Where to look |
|--------|----------------|
| Resume won’t save | `resume_builder` views, browser network tab, auth session |
| Template preview blank | Template ID valid in registry; `/resume/preview/<id>/` response |
| PDF issues | `pdf_generator`, `coverletter` download views |
| Email not sent | `email_utility`, SMTP/env in deployment |
| “Upgrade” or locked actions | `subscriptions`, `check_resume_update_access` |

---

## 11. Glossary

| Term | Meaning |
|------|---------|
| **Template** | HTML/CSS layout for a resume (`resume_templates/<id>.html` pattern in codebase). |
| **Featured template** | Template flagged for marketing landing; capped by `FEATURED_LANDING_MAX`. |
| **ATS** | Applicant Tracking System — layouts often described as ATS-friendly in copy. |

---

## 12. Document maintenance

- **Last aligned with codebase**: Django project layout and URL includes as of the commit that added this file.  
- When adding major features, update **§3**, **§4**, and **§5** so internal KB and bots stay accurate.

---

*This file is intentionally generic and contains no credentials, API keys, or private customer data.*
