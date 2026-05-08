# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.7.1

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
COPY pyproject.toml poetry.lock* /app/

# Install dependencies (skip installing the current project).
# Full Poetry install pulls google-cloud-storage for ENABLE_GCS_PROFILE_UPLOAD (pyproject.toml).
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy project
COPY . /app/

# Install Playwright browsers (non-blocking)
RUN poetry run playwright install chromium || echo "Playwright installation failed, will install at runtime"

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose port 8009 to match Cloud Run configuration
EXPOSE 8009

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"] 