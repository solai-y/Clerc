import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory (which contains app.py) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import app
from services.database import DatabaseService

@pytest.fixture
def client():
    """Flask test client fixture"""
    print("\n[INFO] Setting up Flask test client for tag operations...")
    with app.test_client() as client:
        yield client
    print("[INFO] Flask test client teardown complete.")

@pytest.fixture
def mock_db_service():
    """Mock database service for unit testing"""
    with patch('routes.documents.db_service') as mock_service:
        yield mock_service

class TestTagUpdateOperations:
    """Unit tests for tag update operations"""
    
    def test_update_document_tags_valid_confirmed_tags(self, client, mock_db_service):
        """Test updating document with valid confirmed tags"""
        print("\n[TEST] Running PATCH /documents/{id}/tags with confirmed tags...")
        
        # Mock successful database response
        mock_processed_doc = {
            "process_id": 1,
            "document_id": 123,
            "confirmed_tags": ["invoice", "financial"],
            "user_added_labels": [],
            "suggested_tags": [
                {"tag": "invoice", "score": 0.95},
                {"tag": "financial", "score": 0.87}
            ],
            "processing_date": "2024-01-01T00:00:00Z",
            "status": "processed"
        }
        
        mock_db_service.update_document_tags.return_value = (mock_processed_doc, None)
        
        tag_data = {
            "confirmed_tags": ["invoice", "financial"]
        }
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        print(f"[DEBUG] Response status: {response.status_code}")
        data = response.get_json()
        print(f"[DEBUG] Response data: {data}")
        
        assert response.status_code == 200
        assert data["status"] == "success"
        assert data["message"] == "Document tags updated successfully"
        assert data["data"]["confirmed_tags"] == ["invoice", "financial"]
        
        # Verify database service was called with correct parameters
        mock_db_service.update_document_tags.assert_called_once_with(123, tag_data)
        
        print("[PASS] Confirmed tags updated successfully")
    
    def test_update_document_tags_valid_user_added_labels(self, client, mock_db_service):
        """Test updating document with valid user added labels"""
        print("\n[TEST] Running PATCH /documents/{id}/tags with user added labels...")
        
        mock_processed_doc = {
            "process_id": 1,
            "document_id": 123,
            "confirmed_tags": [],
            "user_added_labels": ["custom-tag", "user-category"],
            "suggested_tags": [],
            "processing_date": "2024-01-01T00:00:00Z",
            "status": "processed"
        }
        
        mock_db_service.update_document_tags.return_value = (mock_processed_doc, None)
        
        tag_data = {
            "user_added_labels": ["custom-tag", "user-category"]
        }
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["user_added_labels"] == ["custom-tag", "user-category"]
        
        print("[PASS] User added labels updated successfully")
    
    def test_update_document_tags_combined_tags(self, client, mock_db_service):
        """Test updating document with both confirmed tags and user labels"""
        print("\n[TEST] Running PATCH /documents/{id}/tags with combined tags...")
        
        mock_processed_doc = {
            "process_id": 1,
            "document_id": 123,
            "confirmed_tags": ["invoice", "financial"],
            "user_added_labels": ["urgent", "q1-2024"],
            "suggested_tags": [
                {"tag": "invoice", "score": 0.95},
                {"tag": "financial", "score": 0.87}
            ],
            "processing_date": "2024-01-01T00:00:00Z",
            "status": "processed"
        }
        
        mock_db_service.update_document_tags.return_value = (mock_processed_doc, None)
        
        tag_data = {
            "confirmed_tags": ["invoice", "financial"],
            "user_added_labels": ["urgent", "q1-2024"]
        }
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["confirmed_tags"] == ["invoice", "financial"]
        assert data["data"]["user_added_labels"] == ["urgent", "q1-2024"]
        
        print("[PASS] Combined tags updated successfully")
    
    def test_update_document_tags_invalid_no_fields(self, client, mock_db_service):
        """Test error when no tag fields are provided"""
        print("\n[TEST] Running PATCH /documents/{id}/tags with no tag fields...")
        
        tag_data = {
            "some_other_field": "value"
        }
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        print(f"[DEBUG] Response status: {response.status_code}")
        data = response.get_json()
        
        assert response.status_code == 400
        assert data["status"] == "error"
        assert "at least one" in data["message"].lower()
        
        # Database service should not be called
        mock_db_service.update_document_tags.assert_not_called()
        
        print("[PASS] Validation error returned for missing tag fields")
    
    def test_update_document_tags_invalid_array_type(self, client, mock_db_service):
        """Test error when tag fields are not arrays"""
        print("\n[TEST] Running PATCH /documents/{id}/tags with invalid array types...")
        
        tag_data = {
            "confirmed_tags": "not-an-array",
            "user_added_labels": ["valid-array"]
        }
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "must be an array" in data["message"]
        
        print("[PASS] Validation error returned for invalid array types")
    
    def test_update_document_tags_document_not_found(self, client, mock_db_service):
        """Test error when document is not found"""
        print("\n[TEST] Running PATCH /documents/{id}/tags for non-existent document...")
        
        mock_db_service.update_document_tags.return_value = (None, "Processed document for document_id 99999 not found")
        
        tag_data = {
            "confirmed_tags": ["test-tag"]
        }
        
        response = client.patch(
            '/documents/99999/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
        
        print("[PASS] 404 error returned for non-existent document")
    
    def test_update_document_tags_invalid_json(self, client, mock_db_service):
        """Test error when request body is not valid JSON"""
        print("\n[TEST] Running PATCH /documents/{id}/tags with invalid JSON...")
        
        response = client.patch(
            '/documents/123/tags',
            data="invalid json",
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        
        print("[PASS] Error returned for invalid JSON")
    
    def test_update_document_tags_empty_body(self, client, mock_db_service):
        """Test error when request body is empty"""
        print("\n[TEST] Running PATCH /documents/{id}/tags with empty body...")
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "at least one" in data["message"].lower()
        
        print("[PASS] Validation error returned for empty body")
    
    def test_update_document_tags_database_error(self, client, mock_db_service):
        """Test handling of database errors"""
        print("\n[TEST] Running PATCH /documents/{id}/tags with database error...")
        
        mock_db_service.update_document_tags.return_value = (None, "Database connection failed")
        
        tag_data = {
            "confirmed_tags": ["test-tag"]
        }
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        assert response.status_code == 500
        data = response.get_json()
        assert data["status"] == "error"
        assert "failed to update" in data["message"].lower()
        
        print("[PASS] Internal server error returned for database errors")
    
    def test_update_document_tags_with_user_removed_tags(self, client, mock_db_service):
        """Test updating document with user_removed_tags field"""
        print("\n[TEST] Running PATCH /documents/{id}/tags with user_removed_tags...")
        
        mock_processed_doc = {
            "process_id": 1,
            "document_id": 123,
            "confirmed_tags": ["invoice"],
            "user_added_labels": [],
            "user_removed_tags": ["old-tag", "deprecated"],
            "suggested_tags": [{"tag": "invoice", "score": 0.95}],
            "processing_date": "2024-01-01T00:00:00Z",
            "status": "processed"
        }
        
        mock_db_service.update_document_tags.return_value = (mock_processed_doc, None)
        
        tag_data = {
            "confirmed_tags": ["invoice"],
            "user_removed_tags": ["old-tag", "deprecated"]
        }
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["user_removed_tags"] == ["old-tag", "deprecated"]
        
        print("[PASS] User removed tags updated successfully")
    
    def test_update_document_tags_empty_arrays(self, client, mock_db_service):
        """Test updating document with empty tag arrays (clearing tags)"""
        print("\n[TEST] Running PATCH /documents/{id}/tags with empty arrays...")
        
        mock_processed_doc = {
            "process_id": 1,
            "document_id": 123,
            "confirmed_tags": [],
            "user_added_labels": [],
            "suggested_tags": [],
            "processing_date": "2024-01-01T00:00:00Z",
            "status": "processed"
        }
        
        mock_db_service.update_document_tags.return_value = (mock_processed_doc, None)
        
        tag_data = {
            "confirmed_tags": [],
            "user_added_labels": []
        }
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["confirmed_tags"] == []
        assert data["data"]["user_added_labels"] == []
        
        print("[PASS] Empty tag arrays (clearing tags) handled successfully")

class TestTagValidation:
    """Unit tests for tag validation logic"""
    
    def test_valid_tag_field_names(self, client, mock_db_service):
        """Test that only valid tag field names are accepted"""
        print("\n[TEST] Testing valid tag field names...")
        
        mock_processed_doc = {
            "process_id": 1,
            "document_id": 123,
            "confirmed_tags": ["test"],
            "user_added_labels": ["test"],
            "user_removed_tags": ["test"],
            "processing_date": "2024-01-01T00:00:00Z",
            "status": "processed"
        }
        
        mock_db_service.update_document_tags.return_value = (mock_processed_doc, None)
        
        # Test all valid fields
        tag_data = {
            "confirmed_tags": ["test"],
            "user_added_labels": ["test"],
            "user_removed_tags": ["test"],
            "user_id": 123  # This should be allowed but not required
        }
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        print("[PASS] All valid tag field names accepted")
    
    def test_tag_content_validation(self, client, mock_db_service):
        """Test validation of tag content (strings in arrays)"""
        print("\n[TEST] Testing tag content validation...")
        
        mock_processed_doc = {
            "process_id": 1,
            "document_id": 123,
            "confirmed_tags": ["valid-tag", "another-tag"],
            "processing_date": "2024-01-01T00:00:00Z",
            "status": "processed"
        }
        
        mock_db_service.update_document_tags.return_value = (mock_processed_doc, None)
        
        # Test with valid string tags
        tag_data = {
            "confirmed_tags": ["valid-tag", "another-tag"]
        }
        
        response = client.patch(
            '/documents/123/tags',
            data=json.dumps(tag_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        print("[PASS] Valid string tags accepted")