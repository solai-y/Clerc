# tests/integration/test_file_upload.py
from pathlib import Path
import os
import sys
import tempfile
from unittest.mock import patch
from fastapi.testclient import TestClient

# --- Locate fixtures relative to this test file ---
HERE = Path(__file__).resolve().parent
MOCK_DIR = HERE / "mock"
PDF_FIXTURE = MOCK_DIR / "TESTING_success.pdf"


def _prime_env():
    """Provide safe defaults so no None hits regex/string checks anywhere."""
    os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
    os.environ.setdefault("SUPABASE_KEY", "test_key")
    os.environ.setdefault("AWS_REGION", "ap-southeast-1")
    os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")


# Prime environment variables before importing app (app reads them at module load)
_prime_env()

# --- Import the FastAPI app (app.py lives two levels up from tests/integration) ---
S3_SERVICE_ROOT = HERE.parent.parent  # .../s3-service
sys.path.append(str(S3_SERVICE_ROOT))
from app import app  # noqa: E402


class _FakeS3Client:
    """Mock S3 client to avoid real AWS calls."""
    def upload_file(self, *a, **k): return True
    def upload_fileobj(self, *a, **k): return True
    def put_object(self, *a, **k): return {"ResponseMetadata": {"HTTPStatusCode": 200}}


def test_file_upload():
    print("\n[TEST] Running POST /upload endpoint test success...")

    assert PDF_FIXTURE.exists(), f"Missing fixture: {PDF_FIXTURE}"

    # Use a fresh, absolute upload dir so path/CWD differences can't 500
    tmp_root = Path(tempfile.mkdtemp())
    upload_dir = tmp_root / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Patch the s3_client that was already created in app.py
    with patch("app.s3_client", _FakeS3Client()):
        client = TestClient(app)
        with PDF_FIXTURE.open("rb") as pdf_file:
            # FastAPI TestClient multipart file upload
            response = client.post(
                "/upload",
                files={"file": ("TESTING_success.pdf", pdf_file, "application/pdf")},
            )

    print(f"[DEBUG] Received response with status code: {response.status_code}")
    try:
        data = response.json()
        print(f"[DEBUG] Response JSON data: {data}")
    except Exception:
        data = None
        print("[DEBUG] Response body (non-JSON):", response.text)

    assert response.status_code in (200, 201), (
        f"Expected 200/201, got {response.status_code} with body={data}"
    )
    print("[SUCCESS] POST /upload (PDF) completed successfully.")
