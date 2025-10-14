import pytest
from fastapi.testclient import TestClient
import sys
import os
import json

# Add the parent directory (which contains app.py) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import app

@pytest.fixture
def client():
    print("\n[INFO] Setting up FastAPI test client...")
    return TestClient(app)

def test_get_documents(client: TestClient):
    print("\n[TEST] Running GET /documents endpoint test...")

    response = client.get('/documents')
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 200
        print("[PASS] Status code is 200 (OK).")
    except AssertionError:
        print(f"[FAIL] Expected status code 200, got {response.status_code}")
        raise

    data = response.json()
    print(f"[DEBUG] Response JSON data keys: {list(data.keys()) if data else 'None'}")

    # Check new API response structure
    try:
        assert data.get("status") == "success"
        print("[PASS] Status is 'success'.")
    except AssertionError:
        print(f"[FAIL] Expected status 'success', got '{data.get('status')}'")
        raise

    try:
        # Check new API response structure with documents and pagination
        response_data = data.get("data")
        assert isinstance(response_data, dict)
        assert "documents" in response_data
        assert "pagination" in response_data
        assert isinstance(response_data["documents"], list)
        print("[PASS] Response data structure is correct (documents + pagination).")
    except AssertionError:
        print(f"[FAIL] Response data structure is incorrect, got {type(data.get('data'))}")
        raise

    try:
        assert "message" in data
        assert "timestamp" in data
        print("[PASS] Required fields present.")
    except AssertionError:
        print("[FAIL] Missing required fields (message, timestamp)")
        raise

    print("[SUCCESS] GET /documents endpoint test completed successfully.")

def test_get_documents_with_pagination(client: TestClient):
    print("\n[TEST] Running GET /documents with pagination test...")

    response = client.get('/documents?limit=5&offset=0')
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 200
        print("[PASS] Status code is 200 (OK).")
    except AssertionError:
        print(f"[FAIL] Expected status code 200, got {response.status_code}")
        raise

    data = response.json()
    
    try:
        assert data.get("status") == "success"
        response_data = data.get("data")
        assert isinstance(response_data, dict)
        assert "documents" in response_data
        assert "pagination" in response_data
        assert len(response_data["documents"]) <= 5  # Should not exceed limit
        assert response_data["pagination"]["limit"] == 5
        print("[PASS] Pagination works correctly.")
    except AssertionError as e:
        print(f"[FAIL] Pagination test failed: {e}")
        raise

    print("[SUCCESS] GET /documents with pagination test completed successfully.")

def test_get_documents_with_search(client: TestClient):
    print("\n[TEST] Running GET /documents with search test...")

    response = client.get('/documents?search=Financial&limit=3')
    print(f"[DEBUG] Received response with status code: {response.status_code}")

    try:
        assert response.status_code == 200
        print("[PASS] Status code is 200 (OK).")
    except AssertionError:
        print(f"[FAIL] Expected status code 200, got {response.status_code}")
        raise

    data = response.json()
    
    try:
        assert data.get("status") == "success"
        response_data = data.get("data")
        assert isinstance(response_data, dict)
        assert "documents" in response_data
        assert "pagination" in response_data
        print("[PASS] Search functionality works.")
    except AssertionError as e:
        print(f"[FAIL] Search test failed: {e}")
        raise

    print("[SUCCESS] GET /documents with search test completed successfully.")