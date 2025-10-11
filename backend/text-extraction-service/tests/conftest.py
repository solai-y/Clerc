"""
Pytest configuration and fixtures for text-extraction-service tests
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app as flask_app

@pytest.fixture
def app():
    """Create and configure a Flask app instance for testing"""
    flask_app.config.update({
        "TESTING": True,
    })
    yield flask_app

@pytest.fixture
def client(app):
    """Create a test client for the Flask app"""
    return app.test_client()

@pytest.fixture
def sample_pdf_url():
    """Sample PDF URL for testing"""
    return "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
