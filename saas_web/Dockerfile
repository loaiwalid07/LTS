# ---------------------------------------------------------------------------
# Stage 1 — build environment
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt gunicorn

# ---------------------------------------------------------------------------
# Stage 2 — runtime image (slim)
# ---------------------------------------------------------------------------
FROM python:3.12-slim

# Create a non-root user
RUN groupadd -r django && useradd -r -g django -m -d /app django

# Runtime system deps (psycopg2, Pillow, yt-dlp, ffmpeg codecs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    libwebp7 \
    ffmpeg \
    libavcodec-extra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from builder (includes gunicorn)
COPY --from=builder /root/.local /usr/local

# Copy project
COPY --chown=django:django . .

# ── Download YouTube cookies from Google Drive (optional) ──────────────
ARG GDRIVE_COOKIES_FILE_ID=12mytiLJiiBGNpRt2Sc50LL4HQaCQlRIh
RUN if [ -n "$GDRIVE_COOKIES_FILE_ID" ]; then \
        echo "Downloading cookies from Google Drive (file_id=$GDRIVE_COOKIES_FILE_ID)..." && \
        pip install --quiet gdown && \
        gdown "$GDRIVE_COOKIES_FILE_ID" -O /app/cookies.txt && \
        chmod 600 /app/cookies.txt && \
        pip uninstall -y gdown --quiet && \
        echo "Cookies downloaded to /app/cookies.txt"; \
    else \
        echo "No GDRIVE_COOKIES_FILE_ID set — skipping cookie download"; \
    fi

# Make entrypoint executable
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Collect static files
RUN mkdir -p /app/staticfiles && \
    python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Ensure clip output directory exists (writable for yt-dlp)
RUN mkdir -p /app/media/clips && chown -R django:django /app

USER django

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
