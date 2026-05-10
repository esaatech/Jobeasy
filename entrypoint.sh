#!/bin/sh
set -e

# Set Django settings module
export DJANGO_SETTINGS_MODULE=jobeas.settings

# Cloud Run always sets PORT (often 8080). Use it for uvicorn.
# For local Docker without PORT, default to 8080 to match Cloud Run conventions.
PORT="${PORT:-8080}"
export PORT

echo "[entrypoint] migrate"
python manage.py migrate --noinput

echo "[entrypoint] collectstatic"
python manage.py collectstatic --noinput

# Create Django admin user when all credentials are set (avoids shell-breaking passwords)
if [ -n "${ADMIN_USERNAME:-}" ] && [ -n "${ADMIN_EMAIL:-}" ] && [ -n "${ADMIN_PASSWORD:-}" ]; then
  echo "[entrypoint] ensure admin user"
  python manage.py shell <<'PY'
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

# Optional seeding (subscriptions, testimonials, FAQ, interview prep).
# Set SKIP_BOOTSTRAP_DATA=1 on Cloud Run after the DB is seeded once so cold starts
# only run migrate + collectstatic + uvicorn (faster, avoids startup timeout).
if [ "${SKIP_BOOTSTRAP_DATA:-0}" != "1" ]; then
  echo "[entrypoint] bootstrap data commands"
  python manage.py setup_subscription_plans
  python manage.py bulk_add_testimonials
  python manage.py bulk_add_faq
  python manage.py import_interview_prep
else
  echo "[entrypoint] SKIP_BOOTSTRAP_DATA=1 — skipping seed management commands"
fi

echo "[entrypoint] starting uvicorn on 0.0.0.0:${PORT}"
exec uvicorn jobeas.asgi:application \
  --host 0.0.0.0 \
  --port "$PORT" \
  --workers 1 \
  --timeout-keep-alive 120 \
  --access-log
