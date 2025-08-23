import pytest
from flask.testing import FlaskClient
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
    print("\n[INFO] Setting up Flask test client...")
    with app.test_client() as client:
        yield client
    print("[INFO] Flask test client teardown complete.")

def test_file_upload(client: FlaskClient):
    print("\n[TEST] Running POST /upload endpoint test success...")

    pdf_path = MOCK_DIR / "TESTING_success.pdf"
    with open(pdf_path, "rb") as pdf_file:
        response = client.post(
            '/upload',
            data={'file': (pdf_file, 'TESTING_success.pdf')},
            content_type='multipart/form-data'
        )
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 200
        print("[PASS] Status code is 200 (OK).")
    except AssertionError:
        print(f"[FAIL] Expected status code 200, got {response.status_code}")
        raise

    data = response.get_json()
    print(f"[DEBUG] Response JSON data: {data}")

    try:
        assert data['message'] == "File uploaded successfully"
        print("[PASS] Success message is 'File uploaded successfully'.")
    except AssertionError:
        print(f"[FAIL] Response success message is not as expected, got {data['message']}")
        raise

    print("[SUCCESS] POST /upload endpoint test completed successfully.")