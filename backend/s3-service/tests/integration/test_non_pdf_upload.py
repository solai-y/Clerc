import pytest
from fastapi.testclient import TestClient
import sys
import os
from pathlib import Path

HERE = Path(__file__).parent.resolve()
MOCK_DIR = HERE / "mock"

# Add the parent directory (which contains app.py) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import app

@pytest.fixture
def client():
    print("\n[INFO] Setting up FastAPI test client...")
    return TestClient(app)

def test_non_pdf_upload(client: TestClient):
    print("\n[TEST] Running POST /upload endpoint test whilst passing an image...")

    img_path = MOCK_DIR / "SMU_Logo.png"
    with open(img_path, "rb") as image_file:
        response = client.post(
            '/upload',
            files={'file': ('SMU_Logo.png', image_file, 'image/png')}
        )
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 400
        print("[PASS] Status code is 400 (Bad Request).")
    except AssertionError:
        print(f"[FAIL] Expected status code 400, got {response.status_code}")
        raise

    data = response.json()
    print(f"[DEBUG] Response JSON data: {data}")

    try:
        assert data['detail'] == "File is not a PDF"
        print("[PASS] Error message is 'File is not a PDF'.")
    except AssertionError:
        print(f"[FAIL] Response error message is not as expected, got {data.get('detail')}")
        raise

    print("[SUCCESS] POST /upload endpoint test of non image upload completed successfully.")
