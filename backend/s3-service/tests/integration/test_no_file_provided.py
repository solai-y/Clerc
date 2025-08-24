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

def test_no_file_provided(client: FlaskClient):
    print("\n[TEST] Running POST /upload endpoint test without passing a file...")

    response = client.post('/upload')
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
        assert data['error'] == "No file provided"
        print("[PASS] Error message is 'No file provided'.")
    except AssertionError:
        print(f"[FAIL] Response error message is not as expected, got {data['error']}")
        raise

    print("[SUCCESS] POST /upload endpoint test completed successfully.")