#!/bin/bash
set -e

echo "entrypoint | starting gunicorn (cookies handled by Python _resolve_cookies)"

# ── Run migrations (optional, uncomment as needed) ────────────────────────
# python manage.py migrate --noinput

# ── Start server ──────────────────────────────────────────────────────────
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
