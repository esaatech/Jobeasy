# Jobeas

A comprehensive resume builder and job application platform with AI-powered features.

## Features

- AI-powered resume parsing and optimization
- Real-time chat interface for resume building
- Multiple resume templates
- WebSocket support for live updates
- PostgreSQL database with Redis for caching

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

- `OPENAI_API_KEY`: OpenAI API key for AI features
- `DATABASE_URL_LOCAL`: local PostgreSQL connection string for development
- `DATABASE_URL_PROD`: production PostgreSQL connection string
- `REDIS_URL`: Redis connection string for WebSocket
- `SECRET_KEY`: Django secret key
- `MYAPP_STRIPE_SECRET_KEY`: Stripe secret key
- `MYAPP_STRIPE_PUBLISHABLE_KEY`: Stripe publishable key
- `STRIPE_BILLING_CURRENCY`: billing currency for plan catalog (`mxn`, `cad`, `usd`, etc.)