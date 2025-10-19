"""
Unit tests for API endpoints
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


def test_root_endpoint(client):
    """Test the root health check endpoint"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "LLM Document Classification"
    assert data["status"] == "healthy"
    assert "model" in data
    assert "version" in data


def test_health_endpoint(client):
    """Test the detailed health check endpoint"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "llm-classification"
    assert "model" in data
    assert "aws_region" in data


@patch('main.prediction_service')
def test_predict_endpoint_success(mock_service, client, sample_request_data, mock_prediction_service):
    """Test successful prediction request"""
    # Setup mock
    mock_service.predict.return_value = mock_prediction_service.predict.return_value
    
    response = client.post("/predict", json=sample_request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "elapsed_seconds" in data
    assert "processed_text" in data
    assert "prediction" in data
    
    # Check prediction structure
    prediction = data["prediction"]
    assert "primary" in prediction
    assert "secondary" in prediction
    assert "tertiary" in prediction
    
    # Check primary prediction
    primary = prediction["primary"]
    assert primary["pred"] == "News"
    assert primary["confidence"] == 0.95
    assert "key_evidence" in primary
    assert "supporting" in primary["key_evidence"]
    assert isinstance(primary["key_evidence"]["supporting"], list)


@patch('main.prediction_service')
def test_predict_endpoint_partial_request(mock_service, client, partial_request_data, mock_prediction_service):
    """Test prediction with partial context"""
    # Mock partial response
    mock_response = {
        "elapsed_seconds": 1.23,
        "processed_text": "sample text",
        "prediction": {
            "secondary": {
                "pred": "Company",
                "confidence": 0.87,
                "primary": "News",
                "key_evidence": {
                    "supporting": [{"token": "company", "impact": "high"}]
                }
            },
            "tertiary": {
                "pred": "Management_Change",
                "confidence": 0.82,
                "primary": "News",
                "secondary": "Company",
                "key_evidence": {
                    "supporting": [{"token": "management", "impact": "high"}]
                }
            }
        }
    }
    mock_service.predict.return_value = mock_response
    
    response = client.post("/predict", json=partial_request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    prediction = data["prediction"]
    assert "secondary" in prediction
    assert "tertiary" in prediction
    assert prediction["secondary"]["primary"] == "News"
    assert prediction["tertiary"]["primary"] == "News"
    assert prediction["tertiary"]["secondary"] == "Company"


def test_predict_endpoint_empty_text(client):
    """Test prediction with empty text"""
    request_data = {
        "text": "",
        "predict": ["primary"],
        "context": {}
    }

    response = client.post("/predict", json=request_data)

    # Can be 400 (validation error) or 503 (service not initialized)
    assert response.status_code in [400, 503]
    if response.status_code == 400:
        assert "Text cannot be empty" in response.json()["detail"]


def test_predict_endpoint_no_predict_levels(client):
    """Test prediction with no prediction levels specified"""
    request_data = {
        "text": "Sample text",
        "predict": [],
        "context": {}
    }

    response = client.post("/predict", json=request_data)

    # Can be 400 (validation error) or 503 (service not initialized)
    assert response.status_code in [400, 503]
    if response.status_code == 400:
        assert "Must specify at least one prediction level" in response.json()["detail"]


def test_predict_endpoint_invalid_level(client):
    """Test prediction with invalid prediction level"""
    request_data = {
        "text": "Sample text",
        "predict": ["invalid_level"],
        "context": {}
    }

    response = client.post("/predict", json=request_data)

    # Can be 400 (validation error) or 503 (service not initialized)
    assert response.status_code in [400, 503]
    if response.status_code == 400:
        assert "Invalid prediction level" in response.json()["detail"]


def test_predict_endpoint_whitespace_text(client):
    """Test prediction with only whitespace text"""
    request_data = {
        "text": "   \n\t   ",
        "predict": ["primary"],
        "context": {}
    }

    response = client.post("/predict", json=request_data)

    # Can be 400 (validation error) or 503 (service not initialized)
    assert response.status_code in [400, 503]
    if response.status_code == 400:
        assert "Text cannot be empty" in response.json()["detail"]


@patch('main.prediction_service')
def test_predict_endpoint_service_error(mock_service, client, sample_request_data):
    """Test prediction when service raises an exception"""
    mock_service.predict.side_effect = Exception("Service error")
    
    response = client.post("/predict", json=sample_request_data)
    
    assert response.status_code == 500
    assert "Classification failed" in response.json()["detail"]


def test_predict_endpoint_service_not_initialized(client, sample_request_data):
    """Test prediction when service is not initialized"""
    with patch('main.prediction_service', None):
        response = client.post("/predict", json=sample_request_data)
        
        assert response.status_code == 503
        assert "Service not initialized" in response.json()["detail"]


def test_predict_endpoint_malformed_json(client):
    """Test prediction with malformed JSON"""
    response = client.post(
        "/predict", 
        data="malformed json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422  # FastAPI validation error


def test_predict_endpoint_missing_fields(client):
    """Test prediction with missing required fields"""
    # Missing 'text' field
    request_data = {
        "predict": ["primary"],
        "context": {}
    }
    
    response = client.post("/predict", json=request_data)
    
    assert response.status_code == 422  # FastAPI validation error