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

# Collect static files
RUN mkdir -p /app/staticfiles && \
    python manage.py collectstatic --noinput --clear

# Ensure clip output directory exists (writable for yt-dlp)
RUN mkdir -p /app/media/clips && chown -R django:django /app/media /app/staticfiles

USER django

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
