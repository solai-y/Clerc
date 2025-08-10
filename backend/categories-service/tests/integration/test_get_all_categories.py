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

def test_get_categories(client: FlaskClient):
    print("\n[TEST] Running GET /categories endpoint test...")

    response = client.get('/categories')
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
        assert isinstance(data, list)
        print("[PASS] Response data is a list.")
    except AssertionError:
        print(f"[FAIL] Response data is not a list, got {type(data)}")
        raise

    print("[SUCCESS] GET /categories endpoint test completed successfully.")
