#!/bin/sh
set -e

# Usual Django setup
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Create Django admin user if it doesn't exist
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$ADMIN_USERNAME').exists():
    User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')
    print('Admin user created successfully')
else:
    print('Admin user already exists')
"

# Populate subscriptions plans
python manage.py setup_subscription_plans

# Populate home app testimonials and FAQs
python manage.py bulk_add_testimonials
python manage.py bulk_add_faq

# Populate interview prep questions
python manage.py import_interview_prep

# Start the server with full Gunicorn options
exec gunicorn jobeas.wsgi:application \
  --bind 0.0.0.0:${PORT:-8009} \
  --workers 1 \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 