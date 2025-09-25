import pytest
import json
from flask.testing import FlaskClient
import sys
import os

# Add the parent directory (which contains app.py) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import app

def create_test_document(client, document_name="Test Document"):
    """Helper function to create a test document"""
    document_data = {
        "document_name": document_name,
        "document_type": "PDF",
        "link": f"https://test.com/{document_name.lower().replace(' ', '-')}.pdf",
        "uploaded_by": None,
    }
    
    response = client.post('/documents', data=json.dumps(document_data), content_type='application/json')
    response_json = response.get_json()
    
    if response.status_code != 201 or "data" not in response_json:
        pytest.skip(f"Cannot create test document: {response_json}")
    
    return response_json["data"]["document_id"]

@pytest.fixture
def client():
    print("\n[INFO] Setting up Flask test client for tag integration tests...")
    with app.test_client() as client:
        yield client
    print("[INFO] Flask test client teardown complete.")

class TestTagOperationsIntegration:
    """Integration tests for tag operations with real database"""
    
    def test_create_processed_document_and_update_tags(self, client: FlaskClient):
        """Test full workflow: create processed document -> update tags"""
        print("\n[TEST] Testing full processed document and tag update workflow...")
        
        # Step 1: Create a raw document first
        print("  [STEP 1] Creating raw document...")
        raw_document_data = {
            "document_name": "Integration Test Document",
            "document_type": "PDF",
            "link": "https://test.com/integration-test.pdf",
            "uploaded_by": None,
        }
        
        raw_doc_response = client.post(
            '/documents',
            data=json.dumps(raw_document_data),
            content_type='application/json'
        )
        
        # Handle creation failure gracefully
        raw_doc_json = raw_doc_response.get_json()
        if raw_doc_response.status_code != 201 or "data" not in raw_doc_json:
            print(f"  [ERROR] Failed to create raw document: {raw_doc_json}")
            pytest.skip("Cannot test tag operations without successful document creation")
        
        document_id = raw_doc_json["data"]["document_id"]
        print(f"  [PASS] Raw document created with ID: {document_id}")
        
        # Step 2: Create processed document entry
        print("  [STEP 2] Creating processed document entry...")
        processed_doc_data = {
            "document_id": document_id,
            "model_id": 1,
            "threshold_pct": 80,
            "suggested_tags": [
                {"tag": "invoice", "score": 0.95},
                {"tag": "financial", "score": 0.87},
                {"tag": "quarterly", "score": 0.72}
            ],
            "ocr_used": True,
            "processing_ms": 1500
        }
        
        processed_response = client.post(
            '/documents/processed',
            data=json.dumps(processed_doc_data),
            content_type='application/json'
        )
        
        assert processed_response.status_code == 201
        processed_data = processed_response.get_json()
        print(f"  [PASS] Processed document created")
        
        # Step 3: Update tags - confirm some AI tags
        print("  [STEP 3] Confirming AI-generated tags...")
        tag_update_data = {
            "confirmed_tags": ["invoice", "financial"]
        }
        
        tag_response = client.patch(
            f'/documents/{document_id}/tags',
            data=json.dumps(tag_update_data),
            content_type='application/json'
        )
        
        assert tag_response.status_code == 200
        tag_data = tag_response.get_json()
        assert tag_data["status"] == "success"
        assert tag_data["data"]["confirmed_tags"] == ["invoice", "financial"]
        print(f"  [PASS] AI tags confirmed successfully")
        
        # Step 4: Add user tags
        print("  [STEP 4] Adding user custom tags...")
        user_tag_data = {
            "confirmed_tags": ["invoice", "financial"],
            "user_added_labels": ["urgent", "q1-2024", "client-xyz"]
        }
        
        user_tag_response = client.patch(
            f'/documents/{document_id}/tags',
            data=json.dumps(user_tag_data),
            content_type='application/json'
        )
        
        assert user_tag_response.status_code == 200
        user_tag_result = user_tag_response.get_json()
        assert user_tag_result["status"] == "success"
        assert user_tag_result["data"]["confirmed_tags"] == ["invoice", "financial"]
        assert user_tag_result["data"]["user_added_labels"] == ["urgent", "q1-2024", "client-xyz"]
        print(f"  [PASS] User tags added successfully")
        
        # Step 5: Verify by retrieving the document from processed documents
        print("  [STEP 5] Verifying final document state...")
        get_response = client.get('/documents')
        assert get_response.status_code == 200
        
        # Find our document in the processed documents
        documents = get_response.get_json()["data"]["documents"]
        final_doc = None
        for doc in documents:
            if doc["document_id"] == document_id:
                final_doc = doc
                break
        
        assert final_doc is not None, f"Document {document_id} not found in processed documents"
        assert final_doc["confirmed_tags"] == ["invoice", "financial"]
        assert final_doc["user_added_labels"] == ["urgent", "q1-2024", "client-xyz"]
        assert len(final_doc["suggested_tags"]) == 3  # Original AI suggestions preserved
        print(f"  [PASS] Final document state verified")
        
        # Step 6: Clean up
        print("  [STEP 6] Cleaning up test document...")
        delete_response = client.delete(f'/documents/{document_id}')
        assert delete_response.status_code == 200
        print(f"  [PASS] Test document cleaned up")
        
        print("[SUCCESS] Full integration workflow completed successfully")
    
    def test_tag_update_with_removal_workflow(self, client: FlaskClient):
        """Test workflow including tag removal operations"""
        print("\n[TEST] Testing tag update with removal workflow...")
        
        # Create document and processed entry
        raw_doc_data = {
            "document_name": "Tag Removal Test Document",
            "document_type": "PDF",
            "link": "https://test.com/tag-removal-test.pdf",
            "uploaded_by": None,
        }
        
        raw_response = client.post('/documents', data=json.dumps(raw_doc_data), content_type='application/json')
        raw_response_json = raw_response.get_json()
        if raw_response.status_code != 201 or "data" not in raw_response_json:
            pytest.skip("Cannot test tag operations without successful document creation")
        document_id = raw_response_json["data"]["document_id"]
        
        processed_data = {
            "document_id": document_id,
            "suggested_tags": [
                {"tag": "contract", "score": 0.88},
                {"tag": "legal", "score": 0.76},
                {"tag": "outdated", "score": 0.65}
            ]
        }
        
        client.post('/documents/processed', data=json.dumps(processed_data), content_type='application/json')
        
        # Initial tag confirmation
        initial_tags = {
            "confirmed_tags": ["contract", "legal", "outdated"],
            "user_added_labels": ["important", "review-needed"]
        }
        
        client.patch(f'/documents/{document_id}/tags', data=json.dumps(initial_tags), content_type='application/json')
        
        # Update with removal
        print("  [STEP] Removing some tags...")
        updated_tags = {
            "confirmed_tags": ["contract", "legal"],  # Removed "outdated"
            "user_added_labels": ["important"],  # Removed "review-needed"
            "user_removed_tags": ["outdated", "review-needed"]
        }
        
        update_response = client.patch(
            f'/documents/{document_id}/tags',
            data=json.dumps(updated_tags),
            content_type='application/json'
        )
        
        assert update_response.status_code == 200
        result = update_response.get_json()
        assert result["data"]["confirmed_tags"] == ["contract", "legal"]
        assert result["data"]["user_added_labels"] == ["important"]
        
        print("  [PASS] Tag removal workflow completed")
        
        # Cleanup
        client.delete(f'/documents/{document_id}')
    
    def test_tag_operations_with_special_characters(self, client: FlaskClient):
        """Test tag operations with special characters and edge cases"""
        print("\n[TEST] Testing tag operations with special characters...")
        
        # Create test document
        raw_doc_data = {
            "document_name": "Special Characters Test",
            "document_type": "PDF",
            "link": "https://test.com/special-chars.pdf",
            "uploaded_by": None,
        }
        
        raw_response = client.post('/documents', data=json.dumps(raw_doc_data), content_type='application/json')
        document_id = raw_response.get_json()["data"]["document_id"]
        
        processed_data = {"document_id": document_id}
        client.post('/documents/processed', data=json.dumps(processed_data), content_type='application/json')
        
        # Test with special characters
        special_tags = {
            "user_added_labels": [
                "tag-with-hyphens",
                "tag_with_underscores",
                "tag.with.dots",
                "tag with spaces",
                "tag/with/slashes",
                "tag@email.com",
                "tag#hashtag",
                "tag$money",
                "tag&ampersand"
            ]
        }
        
        response = client.patch(
            f'/documents/{document_id}/tags',
            data=json.dumps(special_tags),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        result = response.get_json()
        assert len(result["data"]["user_added_labels"]) == 9
        
        print("  [PASS] Special characters in tags handled correctly")
        
        # Cleanup
        client.delete(f'/documents/{document_id}')
    
    def test_concurrent_tag_updates(self, client: FlaskClient):
        """Test concurrent tag updates to the same document"""
        print("\n[TEST] Testing concurrent tag updates...")
        
        # Create test document
        raw_doc_data = {
            "document_name": "Concurrent Updates Test",
            "document_type": "PDF",
            "link": "https://test.com/concurrent.pdf",
            "uploaded_by": None,
        }
        
        raw_response = client.post('/documents', data=json.dumps(raw_doc_data), content_type='application/json')
        document_id = raw_response.get_json()["data"]["document_id"]
        
        processed_data = {
            "document_id": document_id,
            "suggested_tags": [{"tag": "base-tag", "score": 0.9}]
        }
        client.post('/documents/processed', data=json.dumps(processed_data), content_type='application/json')
        
        # Simulate concurrent updates (sequential for testing)
        updates = [
            {"confirmed_tags": ["base-tag"], "user_added_labels": ["update1"]},
            {"confirmed_tags": ["base-tag"], "user_added_labels": ["update1", "update2"]},
            {"confirmed_tags": ["base-tag"], "user_added_labels": ["update1", "update2", "update3"]}
        ]
        
        for i, update_data in enumerate(updates):
            print(f"  [STEP {i+1}] Applying update {i+1}...")
            response = client.patch(
                f'/documents/{document_id}/tags',
                data=json.dumps(update_data),
                content_type='application/json'
            )
            assert response.status_code == 200
        
        # Verify final state
        get_response = client.get('/documents')
        assert get_response.status_code == 200
        
        # Find our document in processed documents
        documents = get_response.get_json()["data"]["documents"]
        final_doc = None
        for doc in documents:
            if doc["document_id"] == document_id:
                final_doc = doc
                break
        
        assert final_doc is not None, f"Document {document_id} not found in processed documents"
        assert final_doc["confirmed_tags"] == ["base-tag"]
        assert final_doc["user_added_labels"] == ["update1", "update2", "update3"]
        
        print("  [PASS] Concurrent updates handled correctly")
        
        # Cleanup
        client.delete(f'/documents/{document_id}')
    
    def test_tag_operations_error_scenarios(self, client: FlaskClient):
        """Test various error scenarios in tag operations"""
        print("\n[TEST] Testing tag operation error scenarios...")
        
        # Test 1: Update tags for non-existent document
        print("  [SCENARIO 1] Non-existent document...")
        response = client.patch(
            '/documents/99999/tags',
            data=json.dumps({"confirmed_tags": ["test"]}),
            content_type='application/json'
        )
        assert response.status_code == 404
        print("  [PASS] 404 for non-existent document")
        
        # Test 2: Create document but don't create processed entry, then try to update tags
        print("  [SCENARIO 2] Document without processed entry...")
        raw_doc_data = {
            "document_name": "No Processed Entry Test",
            "document_type": "PDF",
            "link": "https://test.com/no-processed.pdf",
            "uploaded_by": None,
        }
        
        raw_response = client.post('/documents', data=json.dumps(raw_doc_data), content_type='application/json')
        document_id = raw_response.get_json()["data"]["document_id"]
        
        # Try to update tags without creating processed entry
        response = client.patch(
            f'/documents/{document_id}/tags',
            data=json.dumps({"confirmed_tags": ["test"]}),
            content_type='application/json'
        )
        
        # This should fail because there's no processed document entry
        assert response.status_code == 404
        print("  [PASS] 404 for document without processed entry")
        
        # Cleanup
        client.delete(f'/documents/{document_id}')
        
        # Test 3: Invalid data types
        print("  [SCENARIO 3] Invalid data types...")
        raw_doc_data = {
            "document_name": "Invalid Data Test",
            "document_type": "PDF",
            "link": "https://test.com/invalid-data.pdf",
            "uploaded_by": None,
        }
        
        raw_response = client.post('/documents', data=json.dumps(raw_doc_data), content_type='application/json')
        document_id = raw_response.get_json()["data"]["document_id"]
        
        processed_data = {"document_id": document_id}
        client.post('/documents/processed', data=json.dumps(processed_data), content_type='application/json')
        
        # Try to update with invalid data types
        invalid_data = {
            "confirmed_tags": "not-an-array",
            "user_added_labels": 123
        }
        
        response = client.patch(
            f'/documents/{document_id}/tags',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        print("  [PASS] 400 for invalid data types")
        
        # Cleanup
        client.delete(f'/documents/{document_id}')
        
        print("[SUCCESS] All error scenarios handled correctly")
    
    def test_tag_persistence_across_operations(self, client: FlaskClient):
        """Test that tags persist correctly across multiple operations"""
        print("\n[TEST] Testing tag persistence across operations...")
        
        # Create document
        raw_doc_data = {
            "document_name": "Persistence Test Document",
            "document_type": "PDF",
            "link": "https://test.com/persistence.pdf",
            "uploaded_by": None,
        }
        
        raw_response = client.post('/documents', data=json.dumps(raw_doc_data), content_type='application/json')
        document_id = raw_response.get_json()["data"]["document_id"]
        
        processed_data = {
            "document_id": document_id,
            "suggested_tags": [
                {"tag": "persistent-tag1", "score": 0.9},
                {"tag": "persistent-tag2", "score": 0.8}
            ]
        }
        client.post('/documents/processed', data=json.dumps(processed_data), content_type='application/json')
        
        # Operation 1: Confirm some tags
        print("  [OPERATION 1] Confirming initial tags...")
        client.patch(
            f'/documents/{document_id}/tags',
            data=json.dumps({"confirmed_tags": ["persistent-tag1"]}),
            content_type='application/json'
        )
        
        # Operation 2: Add user tags
        print("  [OPERATION 2] Adding user tags...")
        client.patch(
            f'/documents/{document_id}/tags',
            data=json.dumps({
                "confirmed_tags": ["persistent-tag1"],
                "user_added_labels": ["user-tag1", "user-tag2"]
            }),
            content_type='application/json'
        )
        
        # Operation 3: Modify tags
        print("  [OPERATION 3] Modifying tags...")
        client.patch(
            f'/documents/{document_id}/tags',
            data=json.dumps({
                "confirmed_tags": ["persistent-tag1", "persistent-tag2"],
                "user_added_labels": ["user-tag1", "user-tag3"]  # Changed user-tag2 to user-tag3
            }),
            content_type='application/json'
        )
        
        # Verify final state
        print("  [VERIFICATION] Checking final state...")
        get_response = client.get('/documents')
        assert get_response.status_code == 200
        
        # Find our document in processed documents
        documents = get_response.get_json()["data"]["documents"]
        final_doc = None
        for doc in documents:
            if doc["document_id"] == document_id:
                final_doc = doc
                break
        
        assert final_doc is not None, f"Document {document_id} not found in processed documents"
        assert set(final_doc["confirmed_tags"]) == {"persistent-tag1", "persistent-tag2"}
        assert set(final_doc["user_added_labels"]) == {"user-tag1", "user-tag3"}
        assert len(final_doc["suggested_tags"]) == 2  # AI suggestions preserved
        
        print("  [PASS] Tags persisted correctly across operations")
        
        # Cleanup
        client.delete(f'/documents/{document_id}')
        
        print("[SUCCESS] Tag persistence test completed")