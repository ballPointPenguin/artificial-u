#!/bin/sh
set -e

echo "[entrypoint] Starting API container initialization..."

# Construct DATABASE_URL from components if they exist
if [ -n "$DB_HOST" ] && [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ] && [ -n "$DB_PORT" ] && [ -n "$DB_NAME" ]; then
    export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    echo "[entrypoint] Constructed DATABASE_URL from components."
fi

# Initialize database (create DB if needed, then run alembic migrations)
if [ -n "$DATABASE_URL" ]; then
  echo "[entrypoint] Initializing database with DATABASE_URL=$DATABASE_URL"
  python scripts/initialize_db.py -y
else
  echo "[entrypoint] WARNING: DATABASE_URL is not set; skipping DB initialization"
fi

# Optionally initialize voices if ElevenLabs is configured
if [ -n "$ELEVENLABS_API_KEY" ]; then
  echo "[entrypoint] ELEVENLABS_API_KEY detected; initializing voices (this may take a while)"
  # Do not fail hard if this step errors; it's non-critical for API boot
  python scripts/initialize_voices.py || echo "[entrypoint] Voice initialization failed; continuing"
else
  echo "[entrypoint] ELEVENLABS_API_KEY not set; skipping voice initialization"
fi

echo "[entrypoint] Starting Gunicorn..."
exec gunicorn artificial_u.api.app:app \
  -k uvicorn.workers.UvicornWorker \
  --workers ${GUNICORN_WORKERS} \
  --threads ${GUNICORN_THREADS} \
  --timeout ${GUNICORN_TIMEOUT} \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
