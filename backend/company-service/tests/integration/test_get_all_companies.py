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

def test_get_companies(client: TestClient):
    print("\n[TEST] Running GET /companies endpoint test...")

    response = client.get('/companies')
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 200
        print("[PASS] Status code is 200 (OK).")
    except AssertionError:
        print(f"[FAIL] Expected status code 200, got {response.status_code}")
        raise

    data = response.json()
    print(f"[DEBUG] Response JSON data: {data}")

    try:
        assert isinstance(data, list)
        print("[PASS] Response data is a list.")
    except AssertionError:
        print(f"[FAIL] Response data is not a list, got {type(data)}")
        raise

    print("[SUCCESS] GET /categories endpoint test completed successfully.")
