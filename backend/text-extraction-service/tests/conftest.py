"""
Pytest configuration and fixtures for text-extraction-service tests
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app as fastapi_app

@pytest.fixture
def app():
    """Create and configure a FastAPI app instance for testing"""
    yield fastapi_app

@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def sample_pdf_url():
    """Sample PDF URL for testing"""
    return "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
