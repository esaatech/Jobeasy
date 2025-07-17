# Jobeas

A comprehensive resume builder and job application platform with AI-powered features.

## Features

- AI-powered resume parsing and optimization
- Real-time chat interface for resume building
- Multiple resume templates
- WebSocket support for live updates
- PostgreSQL database with Redis for caching

## Development

```bash
# Install dependencies
poetry install

# Run development server
poetry run python manage.py runserver

# Run with uvicorn (for WebSocket support)
poetry run uvicorn jobeas.asgi:application --reload
```

## Environment Variables

- `OPENAI_API_KEY`: OpenAI API key for AI features
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string for WebSocket
- `SECRET_KEY`: Django secret key 