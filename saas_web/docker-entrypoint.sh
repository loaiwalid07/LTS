#!/bin/bash
set -e

# ── Write YouTube cookies from env var → file (if provided) ──────────────
if [ -n "$YT_CLIPS_COOKIES" ]; then
    if echo "$YT_CLIPS_COOKIES" > /app/cookies.txt; then
        echo "entrypoint | wrote /app/cookies.txt ($(wc -l < /app/cookies.txt) lines) from YT_CLIPS_COOKIES"
        chmod 600 /app/cookies.txt
        export YT_CLIPS_COOKIES_PATH=/app/cookies.txt
    else
        echo "entrypoint | ERROR: failed to write /app/cookies.txt"
    fi
fi

if [ -n "$YT_CLIPS_COOKIES_PATH" ] && [ -f "$YT_CLIPS_COOKIES_PATH" ]; then
    echo "entrypoint | cookies file ready at $YT_CLIPS_COOKIES_PATH"
else
    echo "entrypoint | WARNING: no cookies file — YouTube may ask for sign-in"
fi

# ── Run migrations (optional, uncomment as needed) ────────────────────────
# python manage.py migrate --noinput

# ── Start server ──────────────────────────────────────────────────────────
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
