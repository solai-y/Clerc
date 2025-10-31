"""
Unit test configuration - mocks DatabaseService for isolated unit tests

This conftest must execute BEFORE parent conftest to properly mock the database service.
"""
import pytest
import sys
import os

# CRITICAL: Add parent directory to path FIRST, before any imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class MockDBService:
    """Mock database service with 3 sample documents for tag filtering tests"""
    def get_total_documents_count(self, **kwargs):
        docs = self._filter_docs(**kwargs)
        return len(docs), None

    def query_documents(self, **kwargs):
        docs = self._filter_docs(**kwargs)
        limit = kwargs.get('limit') or 50
        offset = kwargs.get('offset') or 0
        return docs[offset:offset + limit], None

    def _filter_docs(self, **kwargs):
        """Sample documents with tags"""
        all_docs = [
            {'document_id': 1, 'confirmed_tags': {'confirmed_tags': {'tags': [
                {'tag': 'News', 'level': 'primary'},
                {'tag': 'Industry', 'level': 'secondary'},
                {'tag': 'Healthcare', 'level': 'tertiary'}
            ]}}},
            {'document_id': 2, 'confirmed_tags': {'confirmed_tags': {'tags': [
                {'tag': 'News', 'level': 'primary'},
                {'tag': 'Industry', 'level': 'secondary'},
                {'tag': 'Energy', 'level': 'tertiary'}
            ]}}},
            {'document_id': 3, 'confirmed_tags': {'confirmed_tags': {'tags': [
                {'tag': 'Disclosure', 'level': 'primary'},
                {'tag': 'Annual_Reports', 'level': 'secondary'},
                {'tag': 'Buy', 'level': 'tertiary'}
            ]}}}
        ]

        # Apply filters
        primary_tags = kwargs.get('primary_tags', [])
        secondary_tags = kwargs.get('secondary_tags', [])
        tertiary_tags = kwargs.get('tertiary_tags', [])

        filtered = []
        for doc in all_docs:
            tags = doc['confirmed_tags']['confirmed_tags']['tags']
            doc_primary = {t['tag'] for t in tags if t['level'] == 'primary'}
            doc_secondary = {t['tag'] for t in tags if t['level'] == 'secondary'}
            doc_tertiary = {t['tag'] for t in tags if t['level'] == 'tertiary'}

            # OR within tier, AND across tiers
            if primary_tags and not any(t in doc_primary for t in primary_tags):
                continue
            if secondary_tags and not any(t in doc_secondary for t in secondary_tags):
                continue
            if tertiary_tags and not any(t in doc_tertiary for t in tertiary_tags):
                continue

            filtered.append(doc)

        return filtered


def pytest_configure(config):
    """
    Pytest hook that runs BEFORE fixtures and test collection.
    This is the only reliable way to mock before parent conftest runs.
    """
    # Mock the services.database module at the earliest possible moment
    from unittest.mock import MagicMock

    mock_database_module = MagicMock()
    mock_database_module.DatabaseService = lambda: MockDBService()
    sys.modules['services.database'] = mock_database_module


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """Override parent conftest's fixture - do nothing for unit tests"""
    yield
