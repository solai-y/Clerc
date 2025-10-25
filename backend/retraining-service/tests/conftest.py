"""
Pytest configuration and fixtures for retraining service tests
"""
import os
import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.testclient import TestClient
from app import app

# Test database configuration
TEST_DB_CONFIG = {
    'host': os.getenv('TEST_DB_HOST', 'localhost'),
    'port': int(os.getenv('TEST_DB_PORT', 5432)),
    'database': os.getenv('TEST_DB_NAME', 'document_classification_test'),
    'user': os.getenv('TEST_DB_USER', 'postgres'),
    'password': os.getenv('TEST_DB_PASSWORD', 'postgres')
}

@pytest.fixture(scope="session")
def test_db():
    """Create test database connection"""
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    yield conn
    conn.close()

@pytest.fixture(scope="function")
def db_connection(test_db):
    """Provide a clean database connection for each test"""
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()

@pytest.fixture(scope="function")
def clean_db(db_connection):
    """Clean test data before each test"""
    cursor = db_connection.cursor()

    # Clean retraining_data table
    cursor.execute("DELETE FROM retraining_data")

    # Clean test documents and tags if they exist
    cursor.execute("DELETE FROM processed_documents WHERE document_id >= 9000")
    cursor.execute("DELETE FROM raw_documents WHERE document_id >= 9000")
    cursor.execute("DELETE FROM tags WHERE id >= 9000")

    db_connection.commit()
    yield db_connection

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def sample_document_data(clean_db):
    """Create sample document data for testing"""
    cursor = clean_db.cursor(cursor_factory=RealDictCursor)

    # Create a test raw document
    cursor.execute("""
        INSERT INTO raw_documents (document_id, document_name, document_type, link, status)
        VALUES (9001, 'test_document.pdf', 'PDF', 'https://example.com/test.pdf', 'uploaded')
        RETURNING document_id
    """)
    result = cursor.fetchone()
    document_id = result['document_id']

    clean_db.commit()

    return {
        'document_id': document_id,
        'document_name': 'test_document.pdf'
    }

@pytest.fixture
def sample_tags_hierarchy(clean_db):
    """Create sample tag hierarchy for testing"""
    cursor = clean_db.cursor(cursor_factory=RealDictCursor)

    # Create primary tag
    cursor.execute("""
        INSERT INTO tags (id, tag_name, parent_id)
        VALUES (9001, 'Test Primary', NULL)
        RETURNING id
    """)
    primary_id = cursor.fetchone()['id']

    # Create secondary tag
    cursor.execute("""
        INSERT INTO tags (id, tag_name, parent_id)
        VALUES (9002, 'Test Secondary', %s)
        RETURNING id
    """, (primary_id,))
    secondary_id = cursor.fetchone()['id']

    # Create tertiary tag
    cursor.execute("""
        INSERT INTO tags (id, tag_name, parent_id)
        VALUES (9003, 'Test Tertiary', %s)
        RETURNING id
    """, (secondary_id,))
    tertiary_id = cursor.fetchone()['id']

    clean_db.commit()

    return {
        'primary': {'id': primary_id, 'name': 'Test Primary'},
        'secondary': {'id': secondary_id, 'name': 'Test Secondary'},
        'tertiary': {'id': tertiary_id, 'name': 'Test Tertiary'}
    }

@pytest.fixture
def multiple_hierarchies(clean_db):
    """Create multiple tag hierarchies for testing"""
    cursor = clean_db.cursor(cursor_factory=RealDictCursor)

    # Hierarchy 1: News -> Press Release -> Q1 Earnings
    cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9010, 'News', NULL)")
    cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9011, 'Press Release', 9010)")
    cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9012, 'Q1 Earnings', 9011)")

    # Hierarchy 2: Disclosure -> Financial Report -> Annual Report
    cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9020, 'Disclosure', NULL)")
    cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9021, 'Financial Report', 9020)")
    cursor.execute("INSERT INTO tags (id, tag_name, parent_id) VALUES (9022, 'Annual Report', 9021)")

    clean_db.commit()

    return {
        'hierarchy1': {
            'primary': {'id': 9010, 'name': 'News'},
            'secondary': {'id': 9011, 'name': 'Press Release'},
            'tertiary': {'id': 9012, 'name': 'Q1 Earnings'}
        },
        'hierarchy2': {
            'primary': {'id': 9020, 'name': 'Disclosure'},
            'secondary': {'id': 9021, 'name': 'Financial Report'},
            'tertiary': {'id': 9022, 'name': 'Annual Report'}
        }
    }

@pytest.fixture
def sample_text():
    """Sample document text for testing"""
    return """
    This is a sample document text for testing the retraining service.
    It contains multiple sentences and paragraphs to simulate a real document.

    The document discusses quarterly earnings and financial performance.
    Key metrics include revenue growth, profit margins, and market share.

    This text will be stored in the retraining_data table for model training purposes.
    """
