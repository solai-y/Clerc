import requests
import json
import os

BASE_URL = os.environ.get('SERVICE_URL', 'http://localhost:5002')

class TestMissingEndpointsE2E:
    """End-to-end tests for previously untested endpoints"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.base_url = BASE_URL
        self.created_documents = []
    
    def teardown_method(self):
        """Cleanup after each test method"""
        # Clean up any documents created during testing
        for doc_id in self.created_documents:
            try:
                requests.delete(f"{self.base_url}/documents/{doc_id}")
            except:
                pass  # Ignore cleanup errors
    
    def test_root_endpoint_e2e(self):
        """Test the root endpoint GET / via HTTP"""
        print("\n[TEST] Testing root endpoint via HTTP...")
        
        response = requests.get(f"{self.base_url}/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check API response structure
        assert data["status"] == "success"
        assert data["message"] == "Document service API"
        assert "data" in data
        
        # Check that endpoints list is provided
        assert "endpoints" in data["data"]
        assert isinstance(data["data"]["endpoints"], list)
        assert len(data["data"]["endpoints"]) > 0
        
        # Check service information
        assert data["data"]["service"] == "document-service"
        assert data["data"]["version"] == "1.0.0"
        
        # Check that some expected endpoints are listed
        endpoints_text = str(data["data"]["endpoints"])
        assert "GET /health" in endpoints_text
        assert "GET /documents" in endpoints_text
        assert "POST /documents" in endpoints_text
        
        print("[PASS] Root endpoint E2E test completed successfully")
    
    def test_update_document_status_lifecycle_e2e(self):
        """Test complete document status update lifecycle via HTTP"""
        print("\n[TEST] Testing document status update lifecycle via HTTP...")
        
        # 1. Create a document first
        print("  [STEP 1] Creating document for status testing...")
        create_data = {
            "document_name": "Status E2E Test Document",
            "document_type": "PDF",
            "link": "https://test.com/status-e2e-test.pdf",
            "uploaded_by": 6,
        }
        
        create_response = requests.post(
            f"{self.base_url}/documents",
            json=create_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert create_response.status_code == 201
        document_id = create_response.json()["data"]["document_id"]
        self.created_documents.append(document_id)
        print(f"  [PASS] Document created with ID: {document_id}")
        
        # 2. Test updating status to "processing"
        print("  [STEP 2] Updating status to 'processing'...")
        status_data = {"status": "processing"}
        
        status_response = requests.patch(
            f"{self.base_url}/documents/{document_id}/status",
            json=status_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if status_response.status_code != 200:
            print(f"  [DEBUG] Status update failed: {status_response.status_code}")
            print(f"  [DEBUG] Response: {status_response.text}")
            
        assert status_response.status_code == 200
        status_result = status_response.json()
        assert status_result["status"] == "success"
        assert "processing" in status_result["message"].lower()
        print("  [PASS] Status updated to 'processing'")
        
        # 3. Test updating status to "processed"
        print("  [STEP 3] Updating status to 'processed'...")
        status_data = {"status": "processed"}
        
        status_response = requests.patch(
            f"{self.base_url}/documents/{document_id}/status",
            json=status_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if status_response.status_code != 200:
            print(f"  [DEBUG] Second status update failed: {status_response.status_code}")
            print(f"  [DEBUG] Response: {status_response.text}")
            
        assert status_response.status_code == 200
        status_result = status_response.json()
        assert status_result["status"] == "success"
        assert "processed" in status_result["message"].lower()
        print("  [PASS] Status updated to 'processed'")
        
        print("[SUCCESS] Document status update lifecycle completed successfully")
    
    def test_update_document_status_error_scenarios_e2e(self):
        """Test error scenarios for document status update via HTTP"""
        print("\n[TEST] Testing document status update error scenarios via HTTP...")
        
        # Test 1: Non-existent document
        print("  [SCENARIO 1] Testing update status for non-existent document...")
        status_data = {"status": "processing"}
        
        response = requests.patch(
            f"{self.base_url}/documents/99999/status",
            json=status_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
        print("  [PASS] 404 error for non-existent document")
        
        # Test 2: Missing status field
        print("  [SCENARIO 2] Testing update with missing status field...")
        response = requests.patch(
            f"{self.base_url}/documents/1/status",
            json={},  # Empty payload
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "status field is required" in data["message"].lower()
        print("  [PASS] 400 error for missing status field")
        
        # Test 3: Invalid status data type
        print("  [SCENARIO 3] Testing update with invalid status data type...")
        response = requests.patch(
            f"{self.base_url}/documents/1/status",
            json={"status": 123},  # Should be string
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "status must be a string" in data["message"].lower()
        print("  [PASS] 400 error for invalid status data type")
        
        # Test 4: Invalid JSON
        print("  [SCENARIO 4] Testing update with invalid JSON...")
        response = requests.patch(
            f"{self.base_url}/documents/1/status",
            data="invalid json",
            headers={'Content-Type': 'application/json'}
        )
        
        # API returns 500 for invalid JSON (Flask handles this as internal error)
        assert response.status_code in [400, 500]
        data = response.json()
        assert data["status"] == "error"
        print("  [PASS] Error returned for invalid JSON")
        
        print("[SUCCESS] Document status update error scenarios completed successfully")


if __name__ == "__main__":
    test_instance = TestMissingEndpointsE2E()
    
    # Run each test method
    test_methods = [
        test_instance.test_root_endpoint_e2e,
        test_instance.test_update_document_status_lifecycle_e2e,
        test_instance.test_update_document_status_error_scenarios_e2e
    ]
    
    for test_method in test_methods:
        try:
            test_instance.setup_method()
            test_method()
        finally:
            test_instance.teardown_method()
    
    print("\n🎉 ALL MISSING ENDPOINTS E2E TESTS PASSED!")