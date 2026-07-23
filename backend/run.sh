#!/usr/bin/env bash
# Start the WholeWomanLab backend (development).
set -e
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
