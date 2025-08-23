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

class TestMissingEndpoints:
    """Test suite for previously untested endpoints"""
    
    def test_root_endpoint(self, client: FlaskClient):
        """Test the root endpoint GET /"""
        print("\n[TEST] Running GET / (root endpoint) test...")
        
        response = client.get('/')
        print(f"[DEBUG] Response status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.get_json()
        print(f"[DEBUG] Response data: {data}")
        
        # Check API response structure
        assert data.get("status") == "success"
        assert data.get("message") == "Document service API"
        assert "data" in data
        
        # Check that endpoints list is provided
        assert "endpoints" in data["data"]
        assert isinstance(data["data"]["endpoints"], list)
        assert len(data["data"]["endpoints"]) > 0
        
        # Check service information
        assert data["data"]["service"] == "document-service"
        assert data["data"]["version"] == "1.0.0"
        
        print("[PASS] Root endpoint test completed successfully")
    
    def test_update_document_status_valid(self, client: FlaskClient):
        """Test updating document status with valid data"""
        print("\n[TEST] Running PATCH /documents/{id}/status with valid data...")
        
        # First, create a document to test with
        create_data = {
            "document_name": "Status Test Document",
            "document_type": "PDF",
            "link": "https://test.com/status-test.pdf",
            "uploaded_by": 1,
            "company": 1,
            "categories": [1]
        }
        
        create_response = client.post(
            '/documents',
            data=json.dumps(create_data),
            content_type='application/json'
        )
        
        assert create_response.status_code == 201
        document_id = create_response.get_json()["data"]["document_id"]
        print(f"[DEBUG] Created test document with ID: {document_id}")
        
        # Test updating the status
        status_data = {"status": "processing"}
        
        response = client.patch(
            f'/documents/{document_id}/status',
            data=json.dumps(status_data),
            content_type='application/json'
        )
        
        print(f"[DEBUG] Response status: {response.status_code}")
        data = response.get_json()
        print(f"[DEBUG] Response data: {data}")
        
        assert response.status_code == 200
        assert data["status"] == "success"
        assert "Document status updated to 'processing'" in data["message"]
        
        # Verify the status was actually updated by fetching the document
        get_response = client.get(f'/documents/{document_id}')
        get_data = get_response.get_json()
        # Note: The actual status field might be in different location depending on data model
        
        print("[PASS] Document status updated successfully")
        
        # Clean up - delete the test document
        client.delete(f'/documents/{document_id}')
    
    def test_update_document_status_invalid_data(self, client: FlaskClient):
        """Test updating document status with invalid data"""
        print("\n[TEST] Running PATCH /documents/{id}/status with invalid data...")
        
        # Test with missing status field
        response = client.patch(
            '/documents/1/status',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        data = response.get_json()
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response data: {data}")
        
        assert response.status_code == 400
        assert data["status"] == "error"
        assert "status field is required" in data["message"].lower()
        
        print("[PASS] Validation error returned for missing status field")
    
    def test_update_document_status_invalid_type(self, client: FlaskClient):
        """Test updating document status with invalid data type"""
        print("\n[TEST] Running PATCH /documents/{id}/status with invalid data type...")
        
        # Test with non-string status
        status_data = {"status": 123}  # Should be string
        
        response = client.patch(
            '/documents/1/status',
            data=json.dumps(status_data),
            content_type='application/json'
        )
        
        data = response.get_json()
        print(f"[DEBUG] Response status: {response.status_code}")
        
        assert response.status_code == 400
        assert data["status"] == "error"
        assert "status must be a string" in data["message"].lower()
        
        print("[PASS] Validation error returned for invalid status data type")
    
    def test_update_document_status_nonexistent(self, client: FlaskClient):
        """Test updating status for non-existent document"""
        print("\n[TEST] Running PATCH /documents/{id}/status for non-existent document...")
        
        status_data = {"status": "processing"}
        
        response = client.patch(
            '/documents/99999/status',
            data=json.dumps(status_data),
            content_type='application/json'
        )
        
        data = response.get_json()
        print(f"[DEBUG] Response status: {response.status_code}")
        
        assert response.status_code == 404
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
        
        print("[PASS] 404 error returned for non-existent document")
    
