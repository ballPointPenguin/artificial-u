#!/bin/bash

PORT="${FASTAPI_PORT:-8000}"

python -m uvicorn artificial_u.api.app:app --host 0.0.0.0 --port "${PORT}" --reload
