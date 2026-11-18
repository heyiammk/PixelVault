# Image Privacy Cleaner

**Local-First Image Analysis, Personal Metadata Cleaning & Provenance Preservation Suite**  
Built with **Python 3.12+**, **Django**, **Django REST Framework (DRF)**, **Pillow**, **OpenCV**, **piexif**, and optional **ExifTool**.

---

## Core Architecture & Ethical Provenance Rules

1. **100% Local Offline Processing**: All image uploads, binary magic-byte checks, metadata inspections, and container-level metadata cleaning execute strictly on your local computer. Images are never uploaded to external third-party servers.
2. **Surgical Personal Metadata Cleaning**:
   - **Removes**: GPS coordinates, device serial numbers (`BodySerialNumber`, `LensSerialNumber`, `SerialNumber`), personal owner information (`CameraOwnerName`, `OwnerName`, `HostComputer`, `MakerNote`, `UserComment`), and personal contact details (`CreatorContactInfo`, email, phone, address).
   - **Strictly Preserves**: Copyright notices, Authorship/By-line, Licensing terms, AI generation disclosure (`DigitalSourceType`), and **C2PA Content Credentials** (`JUMBF` / `caBX` / `c2pa` manifests).
3. **100% Lossless Pixel Preservation**:
   - Operates at the binary container level for JPEG (`APP1`/`APP13`/`COM` markers without touching the `SOS` compressed pixel scan), PNG (`tEXt`/`iTXt`/`zTXt`/`eXIf` chunks without re-encoding `IDAT`), WEBP (`RIFF` chunks), and lossless TIFF.
   - Verifies before-and-after decoded pixel buffers using **SHA-256 pixel hashing** via Pillow and OpenCV.
4. **Honest SynthID Status Verification**:
   - Reports only `"Detected"`, `"Not detected"`, or `"Unable to verify"`.
   - Never fabricates detection results when an official Google DeepMind / Vertex AI SynthID detector is not configured locally, and **never removes watermarks**.

---

## Project Structure

```text
image_privacy_cleaner/
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── dashboard/          # Frontend SPA views & URLs (6 dashboard pages)
│   ├── image_upload/       # Binary signature validator, 40MB/40-file limits, POST /api/v1/upload/
│   ├── image_analyzer/     # EXIF/XMP/IPTC/PNG/GPS/Camera/Software/C2PA & SynthID, POST /api/v1/analyze/
│   ├── metadata_cleaner/   # Lossless personal metadata stripper, POST /api/v1/clean/
│   ├── batch_processor/    # Error-isolated batch runner, GET /api/v1/jobs/{job_id}/ & CLI command
│   ├── downloads/          # Path-traversal safe single & ZIP downloads
│   └── reports/            # Before/After JSON report generator, GET /api/v1/report/{job_id}/
├── templates/
│   ├── base.html
│   └── dashboard/
│       └── index.html
├── static/
│   ├── css/
│   │   └── app.css
│   └── js/
│       └── app.js
├── media/
│   ├── temp/
│   └── processed/
├── tests/
│   ├── test_services_and_pipeline.py
│   └── test_api_endpoints.py
├── .env.example
├── manage.py
├── requirements.txt
├── run.bat
├── run_windows.bat
├── run.sh
└── README.md
```

---

## Windows Installation, Migration, Testing & Running

### Option A: One-Click Windows Startup (`run.bat`)
Double-click `run.bat` (or run it from Command Prompt / PowerShell):
```cmd
run.bat
```

### Option B: Manual Step-by-Step Commands (Windows CMD / PowerShell)

1. **Create and activate a virtual environment**:
   - **Windows Command Prompt (CMD)**:
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```
   - **Windows PowerShell**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

2. **Install dependencies**:
   ```cmd
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Create your `.env` configuration**:
   ```cmd
   copy .env.example .env
   ```

4. **Create and apply SQLite database migrations**:
   ```cmd
   python manage.py makemigrations dashboard image_upload image_analyzer metadata_cleaner batch_processor downloads reports
   python manage.py migrate
   ```

5. **Run automated tests**:
   ```cmd
   python manage.py test tests
   ```

6. **Start the local development server**:
   ```cmd
   python manage.py runserver 127.0.0.1:8000 --insecure
   ```
   Open **http://127.0.0.1:8000/** in your browser.
