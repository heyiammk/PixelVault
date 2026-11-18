#!/usr/bin/env bash
set -e
echo "============================================================================"
echo "  IMAGE PRIVACY CLEANER - LOCAL-FIRST METADATA & PROVENANCE SUITE"
echo "============================================================================"

if [ ! -d "venv" ]; then
    echo "[1/4] Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "[2/4] Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip >/dev/null 2>&1
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    cp .env.example .env
fi

echo "[3/4] Running database migrations..."
python manage.py makemigrations dashboard image_upload image_analyzer metadata_cleaner batch_processor downloads reports
python manage.py migrate

echo "[4/4] Starting local server at http://127.0.0.1:8000/ ..."
python manage.py runserver 127.0.0.1:8000 --insecure
