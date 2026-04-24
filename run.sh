#!/bin/bash

PORT="${FASTAPI_PORT:-8000}"

python -m uvicorn artificial_u.api.app:app \
  --reload \
  --reload-delay 1.0 \
  --reload-dir artificial_u \
  --reload-include "*.py" \
  --host 0.0.0.0 \
  --port "${PORT}"
