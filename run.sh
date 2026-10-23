#!/usr/bin/env bash
# Starts the SmartFarm backend (which also serves the frontend) on http://localhost:8000
set -e
cd "$(dirname "$0")/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
fi
[ -f .env ] || cp .env.example .env
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
