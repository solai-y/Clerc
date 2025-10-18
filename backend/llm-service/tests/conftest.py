"""
Test configuration and fixtures for LLM service tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from prediction_service import PredictionService


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_prediction_service():
    """Mock prediction service for unit tests"""
    mock_service = Mock(spec=PredictionService)
    
    # Mock successful prediction response
    mock_service.predict.return_value = {
        "elapsed_seconds": 1.23,
        "processed_text": "sample processed text",
        "prediction": {
            "primary": {
                "pred": "News",
                "confidence": 0.95,
                "key_evidence": {
                    "supporting": [{"token": "earnings", "impact": "high"}, {"token": "performance", "impact": "medium"}]
                }
            },
            "secondary": {
                "pred": "Company",
                "confidence": 0.87,
                "primary": "News",
                "key_evidence": {
                    "supporting": [{"token": "company", "impact": "high"}, {"token": "activities", "impact": "medium"}]
                }
            },
            "tertiary": {
                "pred": "Management_Change",
                "confidence": 0.82,
                "primary": "News",
                "secondary": "Company",
                "key_evidence": {
                    "supporting": [{"token": "executive", "impact": "high"}, {"token": "leadership", "impact": "high"}]
                }
            }
        }
    }
    
    return mock_service


@pytest.fixture
def sample_request_data():
    """Sample request data for testing"""
    return {
        "text": "Sample document text about company earnings and management changes",
        "predict": ["primary", "secondary", "tertiary"],
        "context": {}
    }


@pytest.fixture
def partial_request_data():
    """Sample partial request data for testing"""
    return {
        "text": "Sample document text about company earnings",
        "predict": ["secondary", "tertiary"],
        "context": {
            "primary": "News"
        }
    }


@pytest.fixture
def invalid_request_data():
    """Invalid request data for error testing"""
    return {
        "text": "",
        "predict": ["invalid_level"],
        "context": {}
    }


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response"""
    return {
        "primary": "News",
        "primary_confidence": 0.95,
        "primary_reasoning": "This document discusses earnings and company performance.",
        "secondary": "Company", 
        "secondary_confidence": 0.87,
        "secondary_reasoning": "Contains references to specific company activities.",
        "tertiary": "Management_Change",
        "tertiary_confidence": 0.82,
        "tertiary_reasoning": "Mentions executive appointments and leadership changes."
    }


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test_secret")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("CLAUDE_MODEL_ID", "test_model")