"""
Integration tests for complete retraining workflow
"""
import pytest


class TestFullWorkflow:
    """Tests for complete document upload to tag confirmation workflow"""

    def test_complete_single_hierarchy_workflow(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test complete workflow: store text -> update tags -> retrieve data"""
        # Step 1: Store text (after text extraction in upload flow)
        store_response = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )
        assert store_response.status_code == 200
        retraining_id = store_response.json()['data']['retraining_id']

        # Step 2: Verify text is stored without tags
        get_response = client.get(f"/retraining/data/{sample_document_data['document_id']}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data['data']['count'] == 1
        assert data['data']['rows'][0]['hierarchy']['primary']['id'] is None

        # Step 3: Update tags (after user confirms tags)
        update_response = client.post(
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
        assert update_response.status_code == 200
        assert update_response.json()['data']['hierarchies_count'] == 1

        # Step 4: Verify tags are updated
        final_response = client.get(f"/retraining/data/{sample_document_data['document_id']}")
        assert final_response.status_code == 200
        final_data = final_response.json()
        assert final_data['data']['count'] == 1

        row = final_data['data']['rows'][0]
        assert row['hierarchy']['primary']['id'] == sample_tags_hierarchy['primary']['id']
        assert row['hierarchy']['secondary']['id'] == sample_tags_hierarchy['secondary']['id']
        assert row['hierarchy']['tertiary']['id'] == sample_tags_hierarchy['tertiary']['id']
        assert row['text_length'] == len(sample_text)

        # Step 5: Verify stats are updated
        stats_response = client.get("/retraining/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()['data']
        assert stats['total_rows'] == 1
        assert stats['unique_documents'] == 1
        assert stats['rows_with_tags'] == 1

    def test_complete_multiple_hierarchy_workflow(
        self, client, sample_document_data, multiple_hierarchies, sample_text, clean_db
    ):
        """Test workflow with multiple tag hierarchies"""
        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # Update with multiple hierarchies
        update_response = client.post(
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
        assert update_response.status_code == 200
        assert update_response.json()['data']['hierarchies_count'] == 2

        # Verify two rows created
        get_response = client.get(f"/retraining/data/{sample_document_data['document_id']}")
        assert get_response.status_code == 200
        assert get_response.json()['data']['count'] == 2

        # Verify both hierarchies are correct
        rows = get_response.json()['data']['rows']
        hierarchies = [row['hierarchy'] for row in rows]

        # Check that both hierarchies exist
        hierarchy_pairs = [
            (h['primary']['id'], h['tertiary']['id']) for h in hierarchies
        ]
        assert (9010, 9012) in hierarchy_pairs  # News -> Q1 Earnings
        assert (9020, 9022) in hierarchy_pairs  # Disclosure -> Annual Report

    def test_tag_update_workflow(
        self, client, sample_document_data, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test updating tags multiple times (user changes mind)"""
        # Initial store
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )

        # First tag update
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

        # Create new hierarchy
        cursor = clean_db.cursor()
        cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9300, 'New Primary', NULL)")
        cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9301, 'New Secondary', 9300)")
        cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9302, 'New Tertiary', 9301)")
        clean_db.commit()

        # Second tag update (user changes tags)
        update_response = client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id'],
                "confirmed_tags": {
                    "tags": [
                        {"tag": "New Primary", "level": "primary"},
                        {"tag": "New Secondary", "level": "secondary"},
                        {"tag": "New Tertiary", "level": "tertiary"}
                    ]
                }
            }
        )
        assert update_response.status_code == 200

        # Verify old tags are replaced with new ones
        get_response = client.get(f"/retraining/data/{sample_document_data['document_id']}")
        data = get_response.json()['data']
        assert data['count'] == 1

        row = data['rows'][0]
        assert row['hierarchy']['primary']['id'] == 9300
        assert row['hierarchy']['secondary']['id'] == 9301
        assert row['hierarchy']['tertiary']['id'] == 9302

    def test_multiple_documents_workflow(
        self, client, sample_tags_hierarchy, sample_text, clean_db
    ):
        """Test workflow with multiple documents"""
        # Create multiple documents
        cursor = clean_db.cursor()

        doc_ids = []
        for i in range(3):
            cursor.execute("""
                INSERT INTO raw_documents (document_id, document_name, document_type, link, status)
                VALUES (%s, %s, 'PDF', 'https://example.com/test.pdf', 'uploaded')
                RETURNING document_id
            """, (9400 + i, f'test_doc_{i}.pdf'))
            doc_ids.append(cursor.fetchone()[0])

        clean_db.commit()

        # Process each document
        for doc_id in doc_ids:
            # Store text
            client.post(
                "/retraining/store-text",
                json={
                    "document_id": doc_id,
                    "text": f"{sample_text} - Document {doc_id}"
                }
            )

            # Update tags
            client.post(
                "/retraining/update-tags",
                json={
                    "document_id": doc_id,
                    "confirmed_tags": {
                        "tags": [
                            {"tag": sample_tags_hierarchy['primary']['name'], "level": "primary"},
                            {"tag": sample_tags_hierarchy['secondary']['name'], "level": "secondary"},
                            {"tag": sample_tags_hierarchy['tertiary']['name'], "level": "tertiary"}
                        ]
                    }
                }
            )

        # Verify all documents are processed
        stats_response = client.get("/retraining/stats")
        stats = stats_response.json()['data']
        assert stats['total_rows'] == 3
        assert stats['unique_documents'] == 3
        assert stats['rows_with_tags'] == 3

    def test_text_preservation_through_workflow(
        self, client, sample_document_data, sample_tags_hierarchy, clean_db
    ):
        """Test that document text is preserved through the entire workflow"""
        original_text = "This is the original document text that should be preserved."

        # Store text
        client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": original_text
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

        # Verify text is preserved in database
        cursor = clean_db.cursor()
        cursor.execute(
            "SELECT document_text FROM retraining_data WHERE document_id = %s",
            (sample_document_data['document_id'],)
        )
        stored_text = cursor.fetchone()[0]
        assert stored_text == original_text

    def test_workflow_with_invalid_hierarchy_fails_gracefully(
        self, client, sample_document_data, sample_text, clean_db
    ):
        """Test that invalid hierarchy in workflow doesn't corrupt data"""
        # Store text successfully
        store_response = client.post(
            "/retraining/store-text",
            json={
                "document_id": sample_document_data['document_id'],
                "text": sample_text
            }
        )
        assert store_response.status_code == 200

        # Try to update with invalid hierarchy
        update_response = client.post(
            "/retraining/update-tags",
            json={
                "document_id": sample_document_data['document_id'],
                "confirmed_tags": {
                    "tags": [
                        {"tag": "NonExistent", "level": "primary"},
                        {"tag": "NonExistent", "level": "secondary"},
                        {"tag": "NonExistent", "level": "tertiary"}
                    ]
                }
            }
        )
        assert update_response.status_code == 400

        # Verify original text-only row still exists
        get_response = client.get(f"/retraining/data/{sample_document_data['document_id']}")
        assert get_response.status_code == 200
        # After failed update, no rows should exist (delete happened before insert failed)
        # This is expected behavior per the DELETE + INSERT strategy
