"""
Unit tests for GET /retraining/stats endpoint
"""
import pytest


class TestStats:
    """Tests for retrieving retraining statistics"""

    def test_stats_empty_database(self, client, clean_db):
        """Test stats with no data in database"""
        response = client.get("/retraining/stats")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'success'
        assert data['data']['total_rows'] == 0
        assert data['data']['unique_documents'] == 0
        assert data['data']['rows_with_tags'] == 0
        assert data['data']['avg_text_length'] == 0

    def test_stats_with_text_only(
        self, client, sample_document_data, sample_text, clean_db
    ):
        """Test stats with text but no tags"""
        # Store text for one document
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        response = client.get("/retraining/stats")

        assert response.status_code == 200
        data = response.json()

        assert data['data']['total_rows'] == 1
        assert data['data']['unique_documents'] == 1
        assert data['data']['rows_with_tags'] == 0  # No tags yet
        assert data['data']['avg_text_length'] > 0

    def test_stats_with_tags(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test stats with complete retraining data"""
        # Store text and tags
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id'],
                "confirmed_tags": {
                    "tags": [
                        {"tag": sample_tags_hierarchy['primary']['name'], "level": "primary"},
                        {"tag": sample_tags_hierarchy['secondary']['name'], "level": "secondary"},
                        {"tag": sample_tags_hierarchy['tertiary']['name'], "level": "tertiary"}
                    ]
                }
            }
        )

        response = client.get("/retraining/stats")

        assert response.status_code == 200
        data = response.json()

        assert data['data']['total_rows'] == 1
        assert data['data']['unique_documents'] == 1
        assert data['data']['rows_with_tags'] == 1
        assert data['data']['avg_text_length'] == len(sample_text)

    def test_stats_multiple_documents(
        self, client, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test stats with multiple documents"""
        # Create multiple documents
        cursor = clean_db.cursor()

        doc_ids = []
        for i in range(3):
            cursor.execute("""
                INSERT INTO raw_documents (document_id, document_name, document_type, link, status)
                VALUES (%s, %s, 'PDF', 'https://example.com/test.pdf', 'uploaded')
                RETURNING document_id
            """, (9500 + i, f'test_doc_{i}.pdf'))
            doc_ids.append(cursor.fetchone()[0])

        clean_db.commit()

        # Store text for each document
        for doc_id in doc_ids:
            client.post(
                "/retraining/store-text",
                json={
                    "document_id": doc_id,
                    "text": sample_text * (doc_id - 9500 + 1)  # Different text lengths
                }
            )

        response = client.get("/retraining/stats")

        assert response.status_code == 200
        data = response.json()

        assert data['data']['total_rows'] == 3
        assert data['data']['unique_documents'] == 3

    def test_stats_multiple_hierarchies_same_document(
        self, client, sample_document_data, multiple_hierarchies, sample_text, clean_db
    ):
        """Test stats when one document has multiple tag hierarchies"""
        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Update with multiple hierarchies
        client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id'],
                "confirmed_tags": {
                    "tags": [
                        {"tag": "News", "level": "primary"},
                        {"tag": "Press Release", "level": "secondary"},
                        {"tag": "Q1 Earnings", "level": "tertiary"},
                        {"tag": "Disclosure", "level": "primary"},
                        {"tag": "Financial Report", "level": "secondary"},
                        {"tag": "Annual Report", "level": "tertiary"}
                    ]
                }
            }
        )

        response = client.get("/retraining/stats")

        assert response.status_code == 200
        data = response.json()

        assert data['data']['total_rows'] == 2  # Two hierarchies
        assert data['data']['unique_documents'] == 1  # Same document
        assert data['data']['rows_with_tags'] == 2

    def test_stats_average_text_length_calculation(
        self, client, sample_text, clean_db
    ):
        """Test that average text length is calculated correctly"""
        # Create documents with known text lengths
        cursor = clean_db.cursor()

        doc1_id = 9600
        doc2_id = 9601

        cursor.execute("""
            INSERT INTO raw_documents (document_id, document_name, document_type, link, status)
            VALUES (%s, 'doc1.pdf', 'PDF', 'https://example.com/1.pdf', 'uploaded')
        """, (doc1_id,))

        cursor.execute("""
            INSERT INTO raw_documents (document_id, document_name, document_type, link, status)
            VALUES (%s, 'doc2.pdf', 'PDF', 'https://example.com/2.pdf', 'uploaded')
        """, (doc2_id,))

        clean_db.commit()

        # Store texts of different lengths
        text1 = "A" * 100
        text2 = "B" * 200

        client.post("/retraining/store-text", json={"document_id": doc1_id, "text": text1})
        client.post("/retraining/store-text", json={"document_id": doc2_id, "text": text2})

        response = client.get("/retraining/stats")

        assert response.status_code == 200
        data = response.json()

        # Average should be (100 + 200) / 2 = 150
        assert data['data']['avg_text_length'] == 150

    def test_stats_partial_tags(
        self, client, sample_text, clean_db
    ):
        """Test stats when some documents have tags and some don't"""
        # Create two documents
        cursor = clean_db.cursor()

        cursor.execute("""
            INSERT INTO raw_documents (document_id, document_name, document_type, link, status)
            VALUES (9700, 'doc_with_tags.pdf', 'PDF', 'https://example.com/1.pdf', 'uploaded')
        """)

        cursor.execute("""
            INSERT INTO raw_documents (document_id, document_name, document_type, link, status)
            VALUES (9701, 'doc_without_tags.pdf', 'PDF', 'https://example.com/2.pdf', 'uploaded')
        """)

        clean_db.commit()

        # Store text for both
        client.post("/retraining/store-text", json={"document_id": 9700, "text": sample_text})
        client.post("/retraining/store-text", json={"document_id": 9701, "text": sample_text})

        # Only add tags for first document
        cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9700, 'Test P', NULL)")
        cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9701, 'Test S', 9700)")
        cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9702, 'Test T', 9701)")
        clean_db.commit()

        client.post(
            "/retraining/update-tags",
            json={
                "document_id": 9700,
                "confirmed_tags": {
                    "tags": [
                        {"tag": "Test P", "level": "primary"},
                        {"tag": "Test S", "level": "secondary"},
                        {"tag": "Test T", "level": "tertiary"}
                    ]
                }
            }
        )

        response = client.get("/retraining/stats")

        assert response.status_code == 200
        data = response.json()

        assert data['data']['total_rows'] == 2
        assert data['data']['unique_documents'] == 2
        assert data['data']['rows_with_tags'] == 1  # Only one has tags

    def test_stats_response_format(self, client, clean_db):
        """Test that stats response has correct format"""
        response = client.get("/retraining/stats")

        assert response.status_code == 200
        data = response.json()

        assert 'status' in data
        assert 'message' in data
        assert 'data' in data
        assert isinstance(data['data'], dict)
        assert 'total_rows' in data['data']
        assert 'unique_documents' in data['data']
        assert 'rows_with_tags' in data['data']
        assert 'avg_text_length' in data['data']
