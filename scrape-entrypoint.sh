#!/bin/sh
# Cloud Run Job entrypoint for job scraping (Phase 1).
# Uses the same image as the web service but skips web bootstrap.
set -e

export DJANGO_SETTINGS_MODULE=jobeas.settings
export SKIP_BOOTSTRAP_DATA=1

log() {
  printf '[scrape-entrypoint] %s %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*"
}

log "running scrape_jobs $*"
exec python manage.py scrape_jobs "$@"
