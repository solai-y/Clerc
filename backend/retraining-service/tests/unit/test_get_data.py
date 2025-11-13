"""
Unit tests for GET /retraining/data/{document_id} endpoint
"""
import pytest


class TestGetData:
    """Tests for retrieving retraining data"""

    def test_get_data_success(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test successfully retrieving retraining data for a document"""
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

        # Get data
        response = client.get(f"/retraining/data/{sample_document_data['document_id']}")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'success'
        assert 'rows' in data['data']
        assert data['data']['count'] == 1
        assert len(data['data']['rows']) == 1

        row = data['data']['rows'][0]
        assert row['document_id'] == sample_document_data['document_id']
        assert row['text_length'] == len(sample_text)
        assert 'text_preview' in row
        assert row['hierarchy']['primary']['id'] == sample_tags_hierarchy['primary']['id']
        assert row['hierarchy']['primary']['name'] == sample_tags_hierarchy['primary']['name']
        assert row['hierarchy']['secondary']['id'] == sample_tags_hierarchy['secondary']['id']
        assert row['hierarchy']['tertiary']['id'] == sample_tags_hierarchy['tertiary']['id']

    def test_get_data_multiple_hierarchies(
        self, client, sample_document_data, multiple_hierarchies, sample_text, clean_db
    ):
        """Test retrieving data for document with multiple hierarchies"""
        # Store text and multiple hierarchies
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

        # Get data
        response = client.get(f"/retraining/data/{sample_document_data['document_id']}")

        assert response.status_code == 200
        data = response.json()

        assert data['data']['count'] == 2
        assert len(data['data']['rows']) == 2

    def test_get_data_no_data_found(self, client, sample_document_data):
        """Test retrieving data for document with no retraining data"""
        response = client.get(f"/retraining/data/{sample_document_data['document_id']}")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'success'
        assert data['data'] == []

    def test_get_data_text_only_no_tags(
        self, client, sample_document_data, sample_text, clean_db
    ):
        """Test retrieving data for document with text but no tags"""
        # Store text only
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Get data
        response = client.get(f"/retraining/data/{sample_document_data['document_id']}")

        assert response.status_code == 200
        data = response.json()

        assert data['data']['count'] == 1
        row = data['data']['rows'][0]
        assert row['hierarchy']['primary']['id'] is None
        assert row['hierarchy']['secondary']['id'] is None
        assert row['hierarchy']['tertiary']['id'] is None

    def test_get_data_text_preview_truncation(
        self, client, sample_document_data, clean_db
    ):
        """Test that long text is truncated in preview"""
        long_text = "A" * 500

        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": long_text
            }
        )

        # Get data
        response = client.get(f"/retraining/data/{sample_document_data['document_id']}")

        assert response.status_code == 200
        data = response.json()

        row = data['data']['rows'][0]
        assert len(row['text_preview']) == 203  # 200 chars + '...'
        assert row['text_preview'].endswith('...')
        assert row['text_length'] == 500

    def test_get_data_invalid_document_id(self, client):
        """Test retrieving data with invalid document ID"""
        response = client.get("/retraining/data/invalid")

        assert response.status_code == 422

    def test_get_data_includes_timestamps(
        self, client, sample_document_data, sample_text
    ):
        """Test that retrieved data includes timestamps"""
        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Get data
        response = client.get(f"/retraining/data/{sample_document_data['document_id']}")

        assert response.status_code == 200
        data = response.json()

        row = data['data']['rows'][0]
        assert 'created_at' in row
        assert 'updated_at' in row
        assert row['created_at'] is not None

    def test_get_data_ordering(
        self, client, sample_document_data, sample_text, clean_db
    ):
        """Test that results are ordered by ID"""
        # Store multiple entries
        for i in range(3):
            client.post(
                "/retraining/store-text",
                json={
                    "document_id": sample_document_data['document_id'],
                    "text": f"{sample_text} - Version {i}"
                }
            )

        # Get data
        response = client.get(f"/retraining/data/{sample_document_data['document_id']}")

        assert response.status_code == 200
        data = response.json()

        rows = data['data']['rows']
        assert len(rows) == 3

        # Verify ordering by ID (ascending)
        ids = [row['id'] for row in rows]
        assert ids == sorted(ids)
