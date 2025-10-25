"""
Unit tests for POST /retraining/update-tags endpoint
"""
import pytest


class TestUpdateTags:
    """Tests for updating document tags in retraining data"""

    def test_update_tags_single_hierarchy_success(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test successfully updating tags with a single hierarchy"""
        # First store the text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Update tags
        response = client.post(
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

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'success'
        assert 'hierarchies_count' in data['data']
        assert data['data']['hierarchies_count'] == 1
        assert len(data['data']['hierarchies']) == 1

        hierarchy = data['data']['hierarchies'][0]
        assert hierarchy['primary_tag_id'] == sample_tags_hierarchy['primary']['id']
        assert hierarchy['secondary_tag_id'] == sample_tags_hierarchy['secondary']['id']
        assert hierarchy['tertiary_tag_id'] == sample_tags_hierarchy['tertiary']['id']
        assert 'Test Primary' in hierarchy['hierarchy']
        assert 'Test Secondary' in hierarchy['hierarchy']
        assert 'Test Tertiary' in hierarchy['hierarchy']

        # Verify in database
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT * FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result[3] == sample_tags_hierarchy['primary']['id']
        assert result[4] == sample_tags_hierarchy['secondary']['id']
        assert result[5] == sample_tags_hierarchy['tertiary']['id']
        assert result[2] == sample_text  # Text should be preserved

    def test_update_tags_multiple_hierarchies(
        self, client, sample_document_data, multiple_hierarchies, sample_text, clean_db
    ):
        """Test updating tags with multiple hierarchies"""
        # Store text first
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Update with multiple hierarchies
        response = client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id'],
                "confirmed_tags": {
                    "tags": [
                        # Hierarchy 1
                        {"tag": "News", "level": "primary"},
                        {"tag": "Press Release", "level": "secondary"},
                        {"tag": "Q1 Earnings", "level": "tertiary"},
                        # Hierarchy 2
                        {"tag": "Disclosure", "level": "primary"},
                        {"tag": "Financial Report", "level": "secondary"},
                        {"tag": "Annual Report", "level": "tertiary"}
                    ]
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data['data']['hierarchies_count'] == 2
        assert len(data['data']['hierarchies']) == 2

        # Verify two rows in database
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        count = cursor.fetchone()[0]
        assert count == 2

    def test_update_tags_without_prior_text_storage(
        self, client, sample_document_data, sample_tags_hierarchy
    ):
        """Test updating tags without first storing text"""
        response = client.post(
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

        assert response.status_code == 404
        data = response.json()
        assert 'document text not found' in data['detail'].lower()

    def test_update_tags_replaces_old_tags(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test that updating tags replaces old tag data"""
        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # First update
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

        # Verify one row exists
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        assert cursor.fetchone()[0] == 1

        # Second update with same tags
        response = client.post(
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

        # Should still be one row (old deleted, new inserted)
        cursor.execute(
            "SELECT COUNT(*) FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        assert cursor.fetchone()[0] == 1

    def test_update_tags_preserves_text(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test that updating tags preserves the original text"""
        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Update tags
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

        # Verify text is preserved
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT document_text FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        stored_text = cursor.fetchone()[0]
        assert stored_text == sample_text

    def test_update_tags_invalid_hierarchy(
        self, client, sample_document_data, sample_text, clean_db
    ):
        """Test updating with tags that don't form valid hierarchy"""
        # Create tags that don't have parent-child relationship
        cursor = clean_db.cursor()
        cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9100, 'Orphan Tag', NULL)")
        clean_db.commit()

        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Try to update with invalid hierarchy
        response = client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id'],
                "confirmed_tags": {
                    "tags": [
                        {"tag": "Orphan Tag", "level": "primary"},
                        {"tag": "Orphan Tag", "level": "secondary"},
                        {"tag": "Orphan Tag", "level": "tertiary"}
                    ]
                }
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert 'no valid tag hierarchies' in data['detail'].lower()

    def test_update_tags_nonexistent_tag(
        self, client, sample_document_data, sample_text
    ):
        """Test updating with tag that doesn't exist in tags table"""
        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Try to update with non-existent tags
        response = client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id'],
                "confirmed_tags": {
                    "tags": [
                        {"tag": "NonExistent Primary", "level": "primary"},
                        {"tag": "NonExistent Secondary", "level": "secondary"},
                        {"tag": "NonExistent Tertiary", "level": "tertiary"}
                    ]
                }
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert 'no valid tag hierarchies' in data['detail'].lower()

    def test_update_tags_missing_level(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text
    ):
        """Test updating tags with missing hierarchy levels"""
        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Missing primary level
        response = client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id'],
                "confirmed_tags": {
                    "tags": [
                        {"tag": sample_tags_hierarchy['secondary']['name'], "level": "secondary"},
                        {"tag": sample_tags_hierarchy['tertiary']['name'], "level": "tertiary"}
                    ]
                }
            }
        )

        assert response.status_code == 400

    def test_update_tags_missing_document_id(self, client, sample_tags_hierarchy):
        """Test updating tags without document_id"""
        response = client.post(
            "/retraining/update-tags",
            json={
                "confirmed_tags": {
                    "tags": [
                        {"tag": sample_tags_hierarchy['primary']['name'], "level": "primary"}
                    ]
                }
            }
        )

        assert response.status_code == 422

    def test_update_tags_missing_confirmed_tags(self, client, sample_document_data):
        """Test updating tags without confirmed_tags"""
        response = client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id']
            }
        )

        assert response.status_code == 422

    def test_update_tags_empty_tags_array(self, client, sample_document_data, sample_text):
        """Test updating tags with empty tags array"""
        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        response = client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id'],
                "confirmed_tags": {
                    "tags": []
                }
            }
        )

        assert response.status_code == 400

    def test_update_tags_partial_hierarchy(
        self, client, sample_document_data, sample_text, clean_db
    ):
        """Test updating with partial hierarchy (primary -> secondary but no tertiary)"""
        # Create partial hierarchy
        cursor = clean_db.cursor()
        cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9200, 'Partial Primary', NULL)")
        cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9201, 'Partial Secondary', 9200)")
        clean_db.commit()

        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Try to update with partial hierarchy
        response = client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id'],
                "confirmed_tags": {
                    "tags": [
                        {"tag": "Partial Primary", "level": "primary"},
                        {"tag": "Partial Secondary", "level": "secondary"},
                        {"tag": "Partial Secondary", "level": "tertiary"}  # Secondary used as tertiary
                    ]
                }
            }
        )

        # Should fail because secondary doesn't have tertiary child
        assert response.status_code == 400
