import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory (which contains app.py) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import app

@pytest.fixture
def client():
    print("\n[INFO] Setting up FastAPI test client...")
    return TestClient(app)

def test_no_file_provided(client: TestClient):
    print("\n[TEST] Running POST /upload endpoint test without passing a file...")

    response = client.post('/upload')
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 422  # FastAPI returns 422 for validation errors
        print("[PASS] Status code is 422 (Validation Error).")
    except AssertionError:
        print(f"[FAIL] Expected status code 422, got {response.status_code}")
        raise

    data = response.json()
    print(f"[DEBUG] Response JSON data: {data}")

    # FastAPI validation error format
    try:
        assert 'detail' in data
        print("[PASS] Response contains 'detail' field.")
    except AssertionError:
        print(f"[FAIL] Response does not contain 'detail' field")
        raise

    print("[SUCCESS] POST /upload endpoint test completed successfully.")
