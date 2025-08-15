import pytest
from flask.testing import FlaskClient
import sys
import os
import json

# Add the parent directory (which contains app.py) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import app

@pytest.fixture
def client():
    print("\n[INFO] Setting up Flask test client...")
    with app.test_client() as client:
        yield client
    print("[INFO] Flask test client teardown complete.")

def test_get_documents(client: FlaskClient):
    print("\n[TEST] Running GET /documents endpoint test...")

    response = client.get('/documents')
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 200
        print("[PASS] Status code is 200 (OK).")
    except AssertionError:
        print(f"[FAIL] Expected status code 200, got {response.status_code}")
        raise

    data = response.get_json()
    print(f"[DEBUG] Response JSON data keys: {list(data.keys()) if data else 'None'}")

    # Check new API response structure
    try:
        assert data.get("status") == "success"
        print("[PASS] Status is 'success'.")
    except AssertionError:
        print(f"[FAIL] Expected status 'success', got '{data.get('status')}'")
        raise

    try:
        assert isinstance(data.get("data"), list)
        print("[PASS] Response data is a list.")
    except AssertionError:
        print(f"[FAIL] Response data is not a list, got {type(data.get('data'))}")
        raise

    try:
        assert "message" in data
        assert "timestamp" in data
        print("[PASS] Required fields present.")
    except AssertionError:
        print("[FAIL] Missing required fields (message, timestamp)")
        raise

    print("[SUCCESS] GET /documents endpoint test completed successfully.")

def test_get_documents_with_pagination(client: FlaskClient):
    print("\n[TEST] Running GET /documents with pagination test...")

    response = client.get('/documents?limit=5&offset=0')
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 200
        print("[PASS] Status code is 200 (OK).")
    except AssertionError:
        print(f"[FAIL] Expected status code 200, got {response.status_code}")
        raise

    data = response.get_json()
    
    try:
        assert data.get("status") == "success"
        assert isinstance(data.get("data"), list)
        assert len(data.get("data", [])) <= 5  # Should not exceed limit
        print("[PASS] Pagination works correctly.")
    except AssertionError as e:
        print(f"[FAIL] Pagination test failed: {e}")
        raise

    print("[SUCCESS] GET /documents with pagination test completed successfully.")

def test_get_documents_with_search(client: FlaskClient):
    print("\n[TEST] Running GET /documents with search test...")

    response = client.get('/documents?search=Financial&limit=3')
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 200
        print("[PASS] Status code is 200 (OK).")
    except AssertionError:
        print(f"[FAIL] Expected status code 200, got {response.status_code}")
        raise

    data = response.get_json()
    
    try:
        assert data.get("status") == "success"
        assert isinstance(data.get("data"), list)
        print("[PASS] Search functionality works.")
    except AssertionError as e:
        print(f"[FAIL] Search test failed: {e}")
        raise

    print("[SUCCESS] GET /documents with search test completed successfully.")