#!/bin/sh
# Cloud Run / container startup
#
# If the revision fails with "failed to listen on PORT", the process never reached
# `uvicorn` or exited before bind. Check Cloud Logging for the last "[entrypoint]" line.
#
# Common causes:
#   - DJANGO_ENV not set to "production" → DB points at localhost inside the container (hang)
#   - Missing DATABASE_URL_PROD in production
#   - migrate / collectstatic / bootstrap commands slow or failing
#
# Debug:
#   - Set ENTRYPOINT_TRACE=1 for `set -x` (very verbose)
#   - Set SKIP_BOOTSTRAP_DATA=1 after first successful seed to shorten cold start
#
# Logs (replace SERVICE and region):
#   gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="SERVICE"' --limit=100 --format='table(timestamp,textPayload)' --freshness=1h

set -e

_ts() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

log() {
  printf '[entrypoint] %s %s\n' "$(_ts)" "$*"
}

die() {
  printf '[entrypoint] %s FATAL %s\n' "$(_ts)" "$*" >&2
  exit 1
}

if [ -n "${ENTRYPOINT_TRACE:-}" ]; then
  set -x
fi

export DJANGO_SETTINGS_MODULE=jobeas.settings

PORT="${PORT:-8080}"
export PORT

log "boot PORT=${PORT} DJANGO_ENV=${DJANGO_ENV:-development} PWD=$(pwd) PYTHON=$(command -v python)"

case "$PORT" in
  ''|*[!0-9]*) die "PORT must be a number, got: $PORT" ;;
esac

if [ "${UVICORN_ONLY:-0}" = "1" ]; then
  log "UVICORN_ONLY=1 — skipping migrate/bootstrap (diagnostic only; do not use in prod)"
  exec uvicorn jobeas.asgi:application \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 1 \
    --timeout-keep-alive 120 \
    --access-log
fi

if [ "${DJANGO_ENV:-development}" = "production" ] && [ -z "${DATABASE_URL_PROD:-}" ]; then
  die "DJANGO_ENV=production but DATABASE_URL_PROD is unset (empty). Set it in Cloud Run env."
fi

if [ "${DJANGO_ENV:-development}" != "production" ]; then
  log "WARNING: DJANGO_ENV is not production (got ${DJANGO_ENV:-development}). Database config uses development defaults (often localhost) and will usually fail or hang inside Cloud Run. Set DJANGO_ENV=production and DATABASE_URL_PROD."
fi

log "django import + setup + DB target (no migrate yet)"
python -c "
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
import django
django.setup()
from django.conf import settings
db = settings.DATABASES['default']
engine = db.get('ENGINE', '')
host = db.get('HOST') or '(empty — may be socket)'
name = db.get('NAME', '')
print('[entrypoint] django.setup OK')
print(f'[entrypoint] DATABASE engine={engine} HOST={host} NAME={name}')
" || die "django.setup() failed (see Python traceback above). Check SECRET_KEY and DATABASE_* env vars."

log "migrate"
MIG_SEC="${MIGRATE_TIMEOUT_SEC:-180}"
if command -v timeout >/dev/null 2>&1 && [ -n "$MIG_SEC" ]; then
  log "using timeout ${MIG_SEC}s for migrate"
  timeout "$MIG_SEC" python manage.py migrate --noinput \
    || die "migrate failed or exceeded ${MIG_SEC}s (DB unreachable? wrong DJANGO_ENV/DATABASE_URL_PROD?)"
else
  python manage.py migrate --noinput || die "migrate failed (see output above)"
fi

log "collectstatic"
python manage.py collectstatic --noinput || die "collectstatic failed"

if [ -n "${ADMIN_USERNAME:-}" ] && [ -n "${ADMIN_EMAIL:-}" ] && [ -n "${ADMIN_PASSWORD:-}" ]; then
  log "ensure admin user"
  python manage.py shell <<'PY' || die "admin user creation failed"
import os
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.environ.get("ADMIN_USERNAME", "").strip()
e = os.environ.get("ADMIN_EMAIL", "").strip()
p = os.environ.get("ADMIN_PASSWORD", "")
if u and e and p:
    if not User.objects.filter(username=u).exists():
        User.objects.create_superuser(u, e, p)
        print("Admin user created successfully")
    else:
        print("Admin user already exists")
PY
fi

if [ "${SKIP_BOOTSTRAP_DATA:-0}" != "1" ]; then
  # Seeds subscription plans/durations in Postgres (Plus/Ultimate: Weekly + Monthly USD amounts,
  # yearly durations inactive). Optional Stripe Price IDs: STRIPE_*_PRICE_ID env vars (see
  # setup_subscription_plans). Does NOT call Stripe API — use provision_stripe_catalog locally/CI
  # when you need to create new Prices and write IDs (or set env vars in Cloud Run / secrets).
  log "bootstrap: setup_ai_models"
  python manage.py setup_ai_models || die "setup_ai_models failed"
  log "bootstrap: setup_resume_job_evaluation"
  python manage.py setup_resume_job_evaluation || die "setup_resume_job_evaluation failed"
  log "bootstrap: setup_job_fit_gate"
  python manage.py setup_job_fit_gate || die "setup_job_fit_gate failed"
  log "bootstrap: setup_why_should_i_apply"
  python manage.py setup_why_should_i_apply || die "setup_why_should_i_apply failed"
  log "bootstrap: setup_professional_summary"
  python manage.py setup_professional_summary || die "setup_professional_summary failed"
  log "bootstrap: setup_cover_letter"
  python manage.py setup_cover_letter || die "setup_cover_letter failed"
  log "check_ai_platform (migrations + admin + AIModel catalog)"
  python manage.py check_ai_platform || die "check_ai_platform failed — see output above"
  log "bootstrap: setup_subscription_plans"
  python manage.py setup_subscription_plans || die "setup_subscription_plans failed"
  log "bootstrap: bulk_add_testimonials"
  python manage.py bulk_add_testimonials || die "bulk_add_testimonials failed"
  log "bootstrap: bulk_add_faq"
  python manage.py bulk_add_faq || die "bulk_add_faq failed"
  log "bootstrap: import_interview_prep"
  python manage.py import_interview_prep || die "import_interview_prep failed"
else
  log "SKIP_BOOTSTRAP_DATA=1 — skipping seed management commands"
fi

log "starting uvicorn bound on 0.0.0.0:${PORT}"
exec uvicorn jobeas.asgi:application \
  --host 0.0.0.0 \
  --port "$PORT" \
  --workers 1 \
  --timeout-keep-alive 120 \
  --access-log
