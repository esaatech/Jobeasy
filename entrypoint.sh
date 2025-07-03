#!/bin/sh
set -e

# Populate subscriptions plans
python manage.py setup_subscription_plans

# Populate home app testimonials and FAQs
python manage.py bulk_add_testimonials
python manage.py bulk_add_faq

# Usual Django setup
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Start the server with full Gunicorn options
exec gunicorn jobeas.wsgi:application \
  --bind 0.0.0.0:${PORT:-8009} \
  --workers 1 \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 