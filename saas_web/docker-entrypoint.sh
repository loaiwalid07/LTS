#!/bin/bash
set -e

# ── Write YouTube cookies from env var → file (if provided) ──────────────
if [ -n "$YT_CLIPS_COOKIES" ]; then
    echo "$YT_CLIPS_COOKIES" > /app/cookies.txt
    echo "entrypoint | wrote cookies.txt from YT_CLIPS_COOKIES"
    export YT_CLIPS_COOKIES_PATH=/app/cookies.txt
fi

# ── Run migrations (optional, uncomment as needed) ────────────────────────
# python manage.py migrate --noinput

# ── Start server ──────────────────────────────────────────────────────────
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
