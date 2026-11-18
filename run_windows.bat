@echo off
SETLOCAL EnableDelayedExpansion
TITLE Image Privacy Cleaner - Local Server

echo ============================================================================
echo   IMAGE PRIVACY CLEANER - LOCAL-FIRST METADATA ^& PROVENANCE SUITE
echo ============================================================================

IF NOT EXIST "venv\Scripts\python.exe" (
    echo [1/4] Creating Python virtual environment...
    python -m venv venv
    IF !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create virtual environment. Ensure Python 3.12+ is installed and in PATH.
        pause
        exit /b 1
    )
)

echo [2/4] Activating virtual environment and verifying dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

IF NOT EXIST ".env" (
    echo [INFO] Creating local .env from .env.example...
    copy .env.example .env >nul
)

echo [3/4] Running database migrations...
python manage.py makemigrations dashboard image_upload image_analyzer metadata_cleaner batch_processor downloads reports
python manage.py migrate

echo [4/4] Starting local server at http://127.0.0.1:8000/ ...
echo Press CTRL+C to stop the server.
python manage.py runserver 127.0.0.1:8000 --insecure
pause
