#!/bin/bash

python -m uvicorn artificial_u.api.app:app --host 0.0.0.0 --port 8000 --reload
