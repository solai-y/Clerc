import pytest
from flask.testing import FlaskClient
import sys
import os

# Add the parent directory (which contains app.py) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import app

@pytest.fixture
def client():
    print("\n[INFO] Setting up Flask test client...")
    with app.test_client() as client:
        yield client
    print("[INFO] Flask test client teardown complete.")

def test_non_pdf_upload(client: FlaskClient):
    print("\n[TEST] Running POST /upload endpoint test whilst passing an image...")

    with open("./mock/SMU_Logo.png", "rb") as image_file:
        response = client.post(
            '/upload',
            data={'file': (image_file, 'SMU_Logo.png')},
            content_type='multipart/form-data'
        )
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 400
        print("[PASS] Status code is 400 (Bad Request).")
    except AssertionError:
        print(f"[FAIL] Expected status code 400, got {response.status_code}")
        raise

    data = response.get_json()
    print(f"[DEBUG] Response JSON data: {data}")

    try:
        assert data['error'] == "File is not a PDF"
        print("[PASS] Error message is 'File is not a PDF'.")
    except AssertionError:
        print(f"[FAIL] Response error message is not as expected, got {data['error']}")
        raise

    print("[SUCCESS] POST /upload endpoint test of non image upload completed successfully.")