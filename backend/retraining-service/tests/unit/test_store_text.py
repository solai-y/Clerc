"""
Unit tests for POST /retraining/store-text endpoint
"""
import pytest


class TestStoreText:
    """Tests for storing document text"""

    def test_store_text_success(self, client, sample_document_data, sample_text, clean_db):
        """Test successfully storing document text"""
        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'success'
        assert data['message'] == 'Document text stored for retraining'
        assert 'data' in data
        assert data['data']['document_id'] == sample_document_data['document_id']
        assert data['data']['text_length'] == len(sample_text)
        assert 'retraining_id' in data['data']
        assert 'created_at' in data['data']

        # Verify data in database
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT * FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result[2] == sample_text  # document_text column
        assert result[3] is None  # primary_tag_id should be NULL
        assert result[4] is None  # secondary_tag_id should be NULL
        assert result[5] is None  # tertiary_tag_id should be NULL

    def test_store_text_missing_document_id(self, client, sample_text):
        """Test storing text without document_id"""
        response = client.post(
            "/retraining/store-text",
            json={
                "text": sample_text
            }
        )

        assert response.status_code == 422  # Validation error

    def test_store_text_missing_text(self, client, sample_document_data):
        """Test storing text without text field"""
        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id']
            }
        )

        assert response.status_code == 422  # Validation error

    def test_store_text_empty_text(self, client, sample_document_data):
        """Test storing empty text"""
        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": ""
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert 'text is required' in data['detail']

    def test_store_text_nonexistent_document(self, client, sample_text):
        """Test storing text for non-existent document"""
        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": 999999,
                "text": sample_text
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert 'integrity error' in data['detail'].lower()

    def test_store_text_multiple_times_same_document(self, client, sample_document_data, sample_text, clean_db):
        """Test storing text multiple times for same document creates multiple rows"""
        # First insertion
        response1 = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )
        assert response1.status_code == 200

        # Second insertion
        response2 = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text + " Additional text."
            }
        )
        assert response2.status_code == 200

        # Verify two rows exist
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        count = cursor.fetchone()[0]
        assert count == 2

    def test_store_text_large_text(self, client, sample_document_data, clean_db):
        """Test storing very large text"""
        large_text = "A" * 1000000  # 1MB of text

        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": large_text
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['data']['text_length'] == len(large_text)

    def test_store_text_unicode_characters(self, client, sample_document_data, clean_db):
        """Test storing text with unicode characters"""
        unicode_text = "Test 测试 тест テスト 🔥 émojis and spëcial çharacters"

        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": unicode_text
            }
        )

        assert response.status_code == 200

        # Verify unicode is preserved
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT document_text FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        stored_text = cursor.fetchone()[0]
        assert stored_text == unicode_text

    def test_store_text_special_characters(self, client, sample_document_data):
        """Test storing text with special characters"""
        special_text = "Text with \n newlines \t tabs and \"quotes\" and 'apostrophes'"

        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": special_text
            }
        )

        assert response.status_code == 200

    def test_store_text_no_body(self, client):
        """Test endpoint with no request body"""
        response = client.post("/retraining/store-text")

        assert response.status_code == 422

    def test_store_text_invalid_json(self, client):
        """Test endpoint with invalid JSON"""
        response = client.post(
            "/retraining/store-text",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_store_text_wrong_data_types(self, client, sample_text):
        """Test endpoint with wrong data types"""
        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": "not_a_number",
                "text": sample_text
            }
        )

        assert response.status_code == 422

        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": 123,
                "text": 12345  # text should be string
            }
        )

        assert response.status_code == 422
