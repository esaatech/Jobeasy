# Jobeas

A comprehensive resume builder and job application platform with AI-powered features.

## Features

- AI-powered resume parsing and optimization
- Resume–job fit evaluation (Gemini) with dashboard pre-flight gate before generate
- Job applications: fit review vs completed states with score on list and full metrics on detail
- Configurable AI prompts and model catalog per task (see documentation below)
- Real-time chat interface for resume building
- Multiple resume templates
- WebSocket support for live updates
- PostgreSQL database with Redis for caching

## Documentation

| Topic | Location |
|-------|----------|
| **AI platform** (prompts, models, resume–job evaluation, PDF extract, multi-provider catalog) | [`ai_service/docs/AI_PLATFORM.md`](ai_service/docs/AI_PLATFORM.md) |
| **User FAQ** (plans, upload, job fit, dashboard flow) | [`docs/JOBEAS_FAQ.md`](docs/JOBEAS_FAQ.md) |
| Dashboard job application pipeline (fit gate → generate) | [`docs/architecture/dashboard-job-application-pipeline.md`](docs/architecture/dashboard-job-application-pipeline.md) |
| AI module overview (parsing, OpenAI assistant, legacy flows) | [`ai_service/README.md`](ai_service/README.md) |

**Quick setup (evaluation + model catalog):**

```bash
poetry run python manage.py setup_ai_models
poetry run python manage.py setup_resume_job_evaluation
poetry run python manage.py setup_job_fit_gate
```

Admin: **Resume-job evaluations** (playground), **Job fit gate settings**, **AI Prompt Configurations**, **AI models**.

## System Architecture Flow for generating Resume using chatbot 

### AI Assistant Communication Flow

```
┌─────────────────┐    WebSocket Connection    ┌─────────────────┐
│   Frontend      │◄──────────────────────────►│   Backend       │
│   (Browser)     │                            │   (Django)      │
└─────────────────┘                            └─────────────────┘
         │                                              │
         │ 1. User types message                       │
         │    "Help me write an email"                 │
         │                                              │
         ▼                                              │
┌─────────────────┐                            ┌─────────────────┐
│ WebSocket       │                            │ WebSocket       │
│ Consumer        │                            │ Consumer        │
│ (JavaScript)    │                            │ (Python)        │
└─────────────────┘                            └─────────────────┘
         │                                              │
         │ 2. Send message via WebSocket               │
         │                                              │
         │                                              ▼
         │                                    ┌─────────────────┐
         │                                    │ OpenAI          │
         │                                    │ Assistant       │
         │                                    │ Manager         │
         │                                    └─────────────────┘
         │                                              │
         │                                              │ 3. Create/Get Assistant
         │                                              │    & Thread
         │                                              │
         │                                              ▼
         │                                    ┌─────────────────┐
         │                                    │ OpenAI API      │
         │                                    │ (GPT-4)         │
         │                                    └─────────────────┘
         │                                              │
         │                                              │ 4. Process message
         │                                              │    with function calling
         │                                              │
         │                                              ▼
         │                                    ┌─────────────────┐
         │                                    │ Function        │
         │                                    │ Handlers        │
         │                                    │ (save_email,    │
         │                                    │  reply_email)   │
         │                                    └─────────────────┘
         │                                              │
         │                                              │ 5. Execute function
         │                                              │    (e.g., save_email)
         │                                              │
         │                                              ▼
         │                                    ┌─────────────────┐
         │                                    │ Django Models   │
         │                                    │ (Email, Resume) │
         │                                    └─────────────────┘
         │                                              │
         │                                              │ 6. Save to database
         │                                              │
         │                                              ▼
         │                                    ┌─────────────────┐
         │                                    │ Response        │
         │                                    │ Generation      │
         │                                    └─────────────────┘
         │                                              │
         │                                              │ 7. Format response
         │                                              │    with function results
         │                                              │
         │                                              ▼
         │                                    ┌─────────────────┐
         │                                    │ WebSocket       │
         │                                    │ Consumer        │
         │                                    │ (Python)        │
         │                                    └─────────────────┘
         │                                              │
         │                                              │ 8. Send response
         │                                              │    via WebSocket
         │                                              │
         ▼                                              │
┌─────────────────┐                            ┌─────────────────┐
│ WebSocket       │                            │ WebSocket       │
│ Consumer        │                            │ Consumer        │
│ (JavaScript)    │                            │ (Python)        │
└─────────────────┘                            └─────────────────┘
         │                                              │
         │ 9. Receive response                        │
         │    "I've saved your email draft"           │
         │                                              │
         ▼                                              │
┌─────────────────┐                            ┌─────────────────┐
│ UI Update       │                            │ (Connection     │
│ (Display        │                            │  maintained     │
│  response)      │                            │  for real-time  │
└─────────────────┘                            │  chat)          │
                                               └─────────────────┘
```

### Detailed Function Calling Flow

```
┌─────────────────┐
│ User Input      │
│ "Write an email │
│  to John about  │
│  the meeting"   │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ OpenAI GPT-4    │
│ Processes       │
│ Message         │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Function Call   │
│ Detected        │
│ save_email()    │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Function        │
│ Parameters      │
│ Extracted:      │
│ - recipient     │
│ - subject       │
│ - content       │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Function        │
│ Handler         │
│ Executes        │
│ save_email()    │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Database        │
│ Operation       │
│ (Save email     │
│  draft)         │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Function        │
│ Result          │
│ Returned:       │
│ {success: true, │
│  message: "..."}│
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ OpenAI          │
│ Formats         │
│ Response        │
│ with result     │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ WebSocket       │
│ Response        │
│ Sent to         │
│ Frontend        │
└─────────────────┘
```

### Resume Builder Specific Flow

```
┌─────────────────┐
│ User: "I want   │
│  to create a    │
│  resume"        │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ AI Assistant    │
│ Guides through  │
│ resume sections │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Function Calls  │
│ Triggered:      │
│ - save_personal_info()
│ - save_experience()
│ - save_education()
│ - save_skills()
│ - save_additional()
│ - finalize_resume()
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Resume Data     │
│ Saved to        │
│ Django Models   │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Resume          │
│ Generated with  │
│ Selected        │
│ Template        │
└─────────────────┘
```

## Development

```bash
# Install dependencies
poetry install

# Run development server
poetry run python manage.py runserver

# Run with uvicorn (for WebSocket support)
poetry run uvicorn jobeas.asgi:application --reload
```

## PostgreSQL Dump / Restore (Laptop A -> Laptop B)

Use this when moving your local data to another machine.

```bash
# Laptop A: create a dump
pg_dump -h localhost -p 5432 -U postgres -d jobeas_local -Fc -f jobeas_local.dump
```

Copy `jobeas_local.dump` to Laptop B (AirDrop, scp, cloud drive, etc.), then:

```bash
# Laptop B: create DB (if needed)
createdb -h localhost -p 5432 -U postgres jobeas_local

# Laptop B: restore dump
pg_restore -h localhost -p 5432 -U postgres -d jobeas_local --clean --if-exists --no-owner --no-privileges jobeas_local.dump

# Run migrations in case schema changed since dump was created
poetry run python manage.py migrate
```

Quick verify:

```bash
poetry run python manage.py showmigrations | rg '\[ \]'
```

## Environment Variables

Copy `.env.example` to `.env` and fill in real values.

- `OPENAI_API_KEY`: OpenAI API key (resume parsing, cover letter, optimization, assistant, AI summary)
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: **required in production** for resume–job evaluation (set one; see `.env.example`)
- `DEEPSEEK_API_KEY`: optional; DeepSeek models are seeded in admin catalog for future use (not wired in app code yet)
- Model id and temperature for evaluation: configure in admin (**AI models**, **AI Prompt Configurations**), not env. Optional `GEMINI_RESUME_JOB_EVAL_MODEL` / `GEMINI_RESUME_JOB_EVAL_TEMPERATURE` are code fallbacks only if a prompt has no model linked (defaults: `gemini-2.5-flash`, `0.35`)
- `DATABASE_URL_LOCAL`: local PostgreSQL connection string for development
- `DATABASE_URL_PROD`: production PostgreSQL connection string
- `REDIS_URL`: Redis connection string for WebSocket
- `SECRET_KEY`: Django secret key
- `MYAPP_STRIPE_SECRET_KEY`: Stripe secret key
- `MYAPP_STRIPE_PUBLISHABLE_KEY`: Stripe publishable key
- `STRIPE_BILLING_CURRENCY`: billing currency for plan catalog (`mxn`, `cad`, `usd`, etc.)