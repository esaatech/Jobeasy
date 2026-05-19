# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.8.5

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    wget \
    gnupg \
    # Playwright dependencies
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    # Font dependencies
    fonts-liberation \
    fonts-unifont \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache dependencies
COPY pyproject.toml poetry.lock /app/

# Install dependencies (skip installing the current project).
# poetry.lock must be in the image (do not list it in .dockerignore) for reproducible builds.
RUN poetry check \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy project
COPY . /app/

# Install Playwright Chromium for server-side PDF generation (required at runtime)
RUN poetry run playwright install chromium --with-deps

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Cloud Run sets $PORT at runtime (commonly 8080). The entrypoint binds uvicorn to $PORT.
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"] 