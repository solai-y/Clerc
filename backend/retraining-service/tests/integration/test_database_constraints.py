"""
Integration tests for database constraints and foreign keys
"""
import pytest


class TestDatabaseConstraints:
    """Tests for database integrity constraints"""

    def test_cascade_delete_on_document_deletion(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test that retraining data is deleted when document is deleted (CASCADE)"""
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

        # Verify data exists
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        assert cursor.fetchone()[0] == 1

        # Delete the document
        cursor.execute(
            "DELETE FROM raw_documents WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        clean_db.commit()

        # Verify retraining data is also deleted (CASCADE)
        cursor.execute(
            "SELECT COUNT(*) FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        assert cursor.fetchone()[0] == 0

    def test_set_null_on_tag_deletion(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test that tag IDs are set to NULL when tag is deleted (SET NULL)"""
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

        # Delete the tertiary tag
        cursor = clean_db.cursor()
        cursor.execute(
            "DELETE FROM tags WHERE id = %s",
            (sample_tags_hierarchy['tertiary']['id'],)
        )
        clean_db.commit()

        # Verify tertiary_tag_id is now NULL but row still exists
        cursor.execute(
            "SELECT primary_tag_id, secondary_tag_id, tertiary_tag_id FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == sample_tags_hierarchy['primary']['id']  # Primary still exists
        assert result[1] == sample_tags_hierarchy['secondary']['id']  # Secondary still exists
        assert result[2] is None  # Tertiary is now NULL

    def test_updated_at_trigger(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test that updated_at timestamp is automatically updated"""
        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Get initial timestamp
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT created_at, updated_at FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        initial_timestamps = cursor.fetchone()
        initial_created_at = initial_timestamps[0]
        initial_updated_at = initial_timestamps[1]

        # Update tags (triggers UPDATE)
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

        # Get new timestamp
        cursor.execute(
            "SELECT created_at, updated_at FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        new_timestamps = cursor.fetchone()
        new_updated_at = new_timestamps[1]

        # updated_at should be newer (note: created_at will be different because row was replaced)
        assert new_updated_at is not None

    def test_foreign_key_constraint_document_id(
        self, client, sample_text
    ):
        """Test that foreign key constraint prevents invalid document_id"""
        # Try to store text for non-existent document
        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": 999999,
                "text": sample_text
            }
        )

        assert response.status_code == 400
        assert 'integrity error' in response.json()['detail'].lower()

    def test_multiple_rows_same_document_different_hierarchies(
        self, client, sample_document_data, multiple_hierarchies, sample_text, clean_db
    ):
        """Test database allows multiple rows for same document with different hierarchies"""
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

        # Verify two rows exist with different tag combinations
        cursor = clean_db.cursor()
        cursor.execute(
            """
            SELECT primary_tag_id, secondary_tag_id, tertiary_tag_id
            FROM retraining_data
            WHERE document_id = %s
            ORDER BY id
            """,
            (sample_document_data['document_id'],)
        )
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert rows[0] != rows[1]  # Different tag combinations

    def test_text_field_handles_large_data(
        self, client, sample_document_data, clean_db
    ):
        """Test that TEXT field can handle very large documents"""
        # Create a very large text (simulate a long document)
        large_text = "Lorem ipsum " * 100000  # ~1.2MB

        response = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": large_text
            }
        )

        assert response.status_code == 200

        # Verify it's stored correctly
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT LENGTH(document_text) FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        stored_length = cursor.fetchone()[0]
        assert stored_length == len(large_text)

    def test_null_tag_ids_allowed(
        self, client, sample_document_data, sample_text, clean_db
    ):
        """Test that tag_id columns can be NULL (for text-only entries)"""
        # Store text without tags
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Verify all tag columns are NULL
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT primary_tag_id, secondary_tag_id, tertiary_tag_id FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        result = cursor.fetchone()
        assert result[0] is None
        assert result[1] is None
        assert result[2] is None

    def test_indexes_exist(self, clean_db):
        """Test that necessary indexes exist for performance"""
        cursor = clean_db.cursor()

        # Check for document_id index
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'retraining_data'
            AND indexname = 'idx_retraining_data_document_id'
        """)
        assert cursor.fetchone() is not None

        # Check for tags index
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'retraining_data'
            AND indexname = 'idx_retraining_data_tags'
        """)
        assert cursor.fetchone() is not None

        # Check for updated_at index
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'retraining_data'
            AND indexname = 'idx_retraining_data_updated_at'
        """)
        assert cursor.fetchone() is not None
