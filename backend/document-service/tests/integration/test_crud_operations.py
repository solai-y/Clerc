import pytest
import json
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

class TestDocumentCRUD:
    """Test suite for Document CRUD operations"""
    
    def test_create_document_valid(self, client: TestClient):
        """Test creating a document with valid data"""
        print("\n[TEST] Running POST /documents with valid data...")
        
        document_data = {
            "document_name": "Test Document",
            "document_type": "PDF",
            "link": "https://test.com/document.pdf",
            "uploaded_by": None  # Make it nullable to avoid foreign key constraint
        }
        
        response = client.post('/documents', json=document_data)
        
        print(f"[DEBUG] Response status: {response.status_code}")
        data = response.json()
        print(f"[DEBUG] Response data: {data}")
        
        assert response.status_code == 201
        assert data["status"] == "success"
        assert data["message"] == "Document created successfully"
        assert "data" in data
        assert data["data"]["document_name"] == "Test Document"
        assert data["data"]["document_type"] == "PDF"
        assert "document_id" in data["data"]
        
        print("[PASS] Document created successfully")
        return data["data"]["document_id"]  # Return ID for other tests
    
    def test_create_document_invalid_missing_fields(self, client: TestClient):
        """Test creating a document with missing required fields"""
        print("\n[TEST] Running POST /documents with missing fields...")
        
        document_data = {
            "document_name": "Test Document"
            # Missing required fields
        }
        
        response = client.post('/documents', json=document_data)
        
        data = response.json()
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response data: {data}")
        
        assert response.status_code == 400
        assert data["status"] == "error"
        assert "field is required" in data["message"].lower()
        
        print("[PASS] Validation error returned for missing fields")
    
    def test_create_document_invalid_json(self, client: TestClient):
        """Test creating a document with invalid JSON"""
        print("\n[TEST] Running POST /documents with invalid JSON...")
        
        response = client.post('/documents', content="invalid json", headers={"Content-Type": "application/json"})
        
        data = response.json()
        print(f"[DEBUG] Response status: {response.status_code}")
        
        assert response.status_code == 400
        assert data["status"] == "error"
        
        print("[PASS] Error returned for invalid JSON")
    
    def test_get_document_by_id_valid(self, client: TestClient):
        """Test getting a document by valid ID"""
        print("\n[TEST] Running GET /documents/{id} with valid ID...")
        
        # First create a document to test with
        create_payload = {
            "document_name": "Test Document for GET",
            "document_type": "PDF", 
            "link": "https://test.com/get-test.pdf",
            "uploaded_by": None
        }
        
        create_response = client.post('/documents', json=create_payload)
        if create_response.status_code != 201:
            pytest.skip("Cannot test GET without successful document creation")
            
        created_doc = create_response.json()
        document_id = created_doc["data"]["document_id"]
        
        # Now test getting the document by ID
        response = client.get(f'/documents/{document_id}')
        
        print(f"[DEBUG] Response status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["document_id"] == document_id
        
        print("[PASS] Document retrieved successfully by ID")
    
    def test_get_document_by_id_not_found(self, client: TestClient):
        """Test getting a document by non-existent ID"""
        print("\n[TEST] Running GET /documents/{id} with non-existent ID...")
        
        # Use a very high ID that shouldn't exist
        response = client.get('/documents/99999')
        
        print(f"[DEBUG] Response status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 404
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
        
        print("[PASS] 404 error returned for non-existent document")
    
    def test_update_document_valid(self, client: TestClient):
        """Test updating a document with valid data"""
        print("\n[TEST] Running PUT /documents/{id} with valid data...")
        
        # First create a document to update
        create_data = {
            "document_name": "Original Document",
            "document_type": "PDF",
            "link": "https://test.com/original.pdf",
            "uploaded_by": None
        }
        
        create_response = client.post('/documents', json=create_data)
        
        # Handle creation failure gracefully
        create_json = create_response.json()
        if create_response.status_code != 201 or "data" not in create_json:
            print(f"[ERROR] Failed to create document for update test: {create_json}")
            pytest.skip("Cannot test update without successful document creation")
        
        created_doc = create_json["data"]
        doc_id = created_doc["document_id"]
        
        # Now update the document
        update_data = {
            "document_name": "Updated Document",
            "document_type": "PDF",
            "link": "https://test.com/updated.pdf",
            "uploaded_by": None
        }
        
        response = client.put(f'/documents/{doc_id}', json=update_data)
        
        print(f"[DEBUG] Response status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["status"] == "success"
        assert data["data"]["document_name"] == "Updated Document"
        
        print("[PASS] Document updated successfully")
    
    def test_update_document_not_found(self, client: TestClient):
        """Test updating a non-existent document"""
        print("\n[TEST] Running PUT /documents/{id} with non-existent ID...")
        
        update_data = {
            "document_name": "Update Non-existent",
            "document_type": "PDF",
            "link": "https://test.com/test.pdf",
            "uploaded_by": 1
        }
        
        response = client.put('/documents/99999', json=update_data)
        
        print(f"[DEBUG] Response status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 404
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
        
        print("[PASS] 404 error returned for updating non-existent document")
    
    def test_delete_document_valid(self, client: TestClient):
        """Test deleting a document with valid ID"""
        print("\n[TEST] Running DELETE /documents/{id} with valid ID...")
        
        # First create a document to delete
        create_data = {
            "document_name": "Document to Delete",
            "document_type": "PDF",
            "link": "https://test.com/delete.pdf",
            "uploaded_by": None
        }
        
        create_response = client.post('/documents', json=create_data)
        
        # Handle creation failure gracefully
        create_json = create_response.json()
        if create_response.status_code != 201 or "data" not in create_json:
            print(f"[ERROR] Failed to create document for delete test: {create_json}")
            pytest.skip("Cannot test delete without successful document creation")
        
        created_doc = create_json["data"]
        doc_id = created_doc["document_id"]
        
        # Now delete the document
        response = client.delete(f'/documents/{doc_id}')
        
        print(f"[DEBUG] Response status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["status"] == "success"
        assert data["message"] == "Document deleted successfully"
        assert data["data"] is None
        
        # Verify the document is actually deleted
        get_response = client.get(f'/documents/{doc_id}')
        assert get_response.status_code == 404
        
        print("[PASS] Document deleted successfully")
    
    def test_delete_document_not_found(self, client: TestClient):
        """Test deleting a non-existent document"""
        print("\n[TEST] Running DELETE /documents/{id} with non-existent ID...")
        
        response = client.delete('/documents/99999')
        
        print(f"[DEBUG] Response status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 404
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
        
        print("[PASS] 404 error returned for deleting non-existent document")

    def test_pagination_functionality(self, client: TestClient):
        """Test pagination parameters"""
        print("\n[TEST] Testing pagination functionality...")
        
        # Test with limit
        response = client.get('/documents?limit=5')
        data = response.json()
        
        assert response.status_code == 200
        assert len(data["data"]) <= 5
        
        # Test with invalid limit
        response = client.get('/documents?limit=-1')
        data = response.json()
        
        assert response.status_code == 400
        assert data["status"] == "error"
        
        print("[PASS] Pagination functionality works correctly")

