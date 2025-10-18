"""
Minimal test cases for multi-tier tag filtering feature
One test per acceptance criterion (6 tests total)

Acceptance Criteria:
AC1. Users can access filter options for each tag tier
AC2. Users can select one or more tags within each tier (OR logic)
AC3. Filtering supports multi-select across different tiers (AND logic)
AC4. Filter results update dynamically
AC5. Users can clear filters
AC6. Filtered document count is displayed
"""

import pytest
from flask import Flask


@pytest.fixture
def app():
    """Create test Flask app with mocked database service"""
    # Import the MockDBService from conftest
    from .conftest import MockDBService

    # Import routes AFTER conftest has set up the mock
    import routes.documents as doc_routes
    from routes.documents import documents_bp

    # Inject the mock AFTER module initialization (in case it failed to initialize)
    doc_routes.db_service = MockDBService()

    # Now create the app with the blueprint
    app = Flask(__name__)
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestTagFilteringMinimal:
    """Minimal test cases - one per acceptance criterion"""

    def test_ac1_filter_endpoint_accepts_tag_parameters(self, client):
        """
        AC1: Users can access filter options for each tag tier
        Verify: API endpoint accepts primary_tags[], secondary_tags[], tertiary_tags[]
        """
        response = client.get('/documents?primary_tags[]=News&secondary_tags[]=Industry&tertiary_tags[]=Healthcare')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        # If endpoint accepts parameters without error, AC1 is satisfied

    def test_ac2_or_logic_within_same_tier(self, client):
        """
        AC2: Users can select multiple tags within tier (OR logic)
        Verify: Selecting "News" OR "Disclosure" returns docs with either tag
        Expected: 3 docs (2 with News, 1 with Disclosure)
        """
        response = client.get('/documents?primary_tags[]=News&primary_tags[]=Disclosure')

        data = response.get_json()
        assert data['data']['pagination']['total'] == 3  # All 3 docs have News OR Disclosure

    def test_ac3_and_logic_across_different_tiers(self, client):
        """
        AC3: Multi-select across tiers with AND logic
        Verify: Primary="News" AND Secondary="Industry" returns only matching docs
        Expected: 2 docs (both have News AND Industry)
        """
        response = client.get('/documents?primary_tags[]=News&secondary_tags[]=Industry')

        data = response.get_json()
        assert data['data']['pagination']['total'] == 2  # Only docs 1 and 2

    def test_ac4_filter_updates_dynamically(self, client):
        """
        AC4: Filter results update dynamically
        Verify: Adding more filters reduces result count (more restrictive)
        """
        # First query: Primary="News" → 2 results
        response1 = client.get('/documents?primary_tags[]=News')
        count1 = response1.get_json()['data']['pagination']['total']

        # Second query: Primary="News" AND Tertiary="Healthcare" → 1 result
        response2 = client.get('/documents?primary_tags[]=News&tertiary_tags[]=Healthcare')
        count2 = response2.get_json()['data']['pagination']['total']

        assert count1 == 2
        assert count2 == 1
        assert count2 < count1  # More filters = fewer results (dynamic update)

    def test_ac5_clear_filters_returns_all_documents(self, client):
        """
        AC5: Users can clear filters
        Verify: No filter parameters returns all documents
        """
        # With filters
        response_filtered = client.get('/documents?primary_tags[]=News')
        filtered_count = response_filtered.get_json()['data']['pagination']['total']

        # Without filters (cleared)
        response_all = client.get('/documents')
        all_count = response_all.get_json()['data']['pagination']['total']

        assert filtered_count == 2  # Filtered
        assert all_count == 3  # All documents
        assert all_count > filtered_count  # Clearing filters shows more

    def test_ac6_filtered_document_count_displayed(self, client):
        """
        AC6: Filtered document count is displayed
        Verify: Response includes pagination.total with correct filtered count
        """
        response = client.get('/documents?primary_tags[]=News')

        data = response.get_json()
        assert 'pagination' in data['data']
        assert 'total' in data['data']['pagination']
        assert data['data']['pagination']['total'] == 2  # Correct count for "News"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
