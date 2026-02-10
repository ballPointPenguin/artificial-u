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

# Seed foundational data (faculties, etc.)
if [ -n "$DATABASE_URL" ]; then
  echo "[entrypoint] Seeding database with foundational data..."
  python scripts/seed_data.py || echo "[entrypoint] Data seeding failed; continuing"
else
  echo "[entrypoint] DATABASE_URL not set; skipping data seeding"
fi

# Optionally initialize voices if ElevenLabs is configured
if [ -n "$ELEVENLABS_API_KEY" ]; then
  echo "[entrypoint] ELEVENLABS_API_KEY detected; initializing voices (this may take a while)"
  # Do not fail hard if this step errors; it's non-critical for API boot
  python scripts/initialize_voices.py || echo "[entrypoint] Voice initialization failed; continuing"
else
  echo "[entrypoint] ELEVENLABS_API_KEY not set; skipping voice initialization"
fi

# Optionally run ID3 backfill on existing audio (simple toggle)
if [ "${RUN_BACKFILL_ID3}" = "1" ]; then
  if [ -n "$DATABASE_URL" ]; then
    echo "[entrypoint] RUN_BACKFILL_ID3=1 detected; running audio ID3 backfill..."
    python scripts/backfill_audio_id3_tags.py --fix-headers || echo "[entrypoint] ID3 backfill failed; continuing"
  else
    echo "[entrypoint] DATABASE_URL not set; skipping ID3 backfill"
  fi
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
