"""
Integration tests for prediction service flow
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app import app

@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)

@pytest.fixture
def sample_request():
    """Sample prediction request"""
    return {
        "text": "Apple Inc. announced today that Tim Cook will step down as CEO.",
        "predict_levels": ["primary", "secondary", "tertiary"],
        "confidence_thresholds": {
            "primary": 0.90,
            "secondary": 0.85,
            "tertiary": 0.80
        }
    }

@pytest.fixture
def mock_ai_response():
    """Mock AI service response"""
    return {
        "prediction": {
            "primary": {"pred": "News", "confidence": 0.95},
            "secondary": {"pred": "Company", "confidence": 0.80},  # Below threshold
            "tertiary": {"pred": "Announcement", "confidence": 0.75}
        },
        "elapsed_seconds": 2.1,
        "processed_text": "apple inc announced today tim cook step ceo",
        "duration": 2.1
    }

@pytest.fixture
def mock_llm_response():
    """Mock LLM service response"""
    return {
        "prediction": {
            "secondary": {
                "pred": "Technology", 
                "confidence": 0.92,
                "reasoning": "This is about a technology company CEO change."
            },
            "tertiary": {
                "pred": "Management_Change", 
                "confidence": 0.88,
                "reasoning": "This is about a management change at Apple."
            }
        },
        "elapsed_seconds": 5.8,
        "processed_text": "apple inc announced today tim cook step ceo",
        "duration": 5.8
    }

class TestPredictionFlow:
    """Test end-to-end prediction flow"""
    
    @patch('services.ai_client.AIServiceClient.predict')
    @patch('services.llm_client.LLMServiceClient.predict')
    async def test_prediction_flow_triggers_llm(self, mock_llm_predict, mock_ai_predict, 
                                                client, sample_request, mock_ai_response, 
                                                mock_llm_response):
        """Test prediction flow that triggers LLM due to low confidence"""
        # Setup mocks
        mock_ai_predict.return_value = mock_ai_response
        mock_llm_predict.return_value = mock_llm_response
        
        # Make request
        response = client.post("/classify", json=sample_request)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "prediction" in data
        assert "service_calls" in data
        assert "confidence_analysis" in data
        
        # Verify service calls
        assert data["service_calls"]["ai_service"]["called"] is True
        assert data["service_calls"]["llm_service"]["called"] is True
        
        # Verify confidence analysis
        assert data["confidence_analysis"]["triggered_llm"] is True
        assert data["confidence_analysis"]["trigger_level"] == "secondary"
        assert "secondary" in data["confidence_analysis"]["levels_below_threshold"]
        
        # Verify final predictions
        # Primary should use AI (above threshold)
        assert data["prediction"]["primary"]["source"] == "ai"
        assert data["prediction"]["primary"]["pred"] == "News"
        
        # Secondary should use LLM (below threshold)
        assert data["prediction"]["secondary"]["source"] == "llm"
        assert data["prediction"]["secondary"]["pred"] == "Technology"
        
        # Tertiary should use LLM (child of triggered level)
        assert data["prediction"]["tertiary"]["source"] == "llm"
        assert data["prediction"]["tertiary"]["pred"] == "Management_Change"
    
    @patch('services.ai_client.AIServiceClient.predict')
    async def test_prediction_flow_ai_only(self, mock_ai_predict, client, sample_request):
        """Test prediction flow that only uses AI (all confidence levels met)"""
        # AI response with all high confidence
        mock_ai_response = {
            "prediction": {
                "primary": {"pred": "News", "confidence": 0.95},
                "secondary": {"pred": "Company", "confidence": 0.90},  # Above threshold
                "tertiary": {"pred": "Announcement", "confidence": 0.85}  # Above threshold
            },
            "elapsed_seconds": 2.1,
            "processed_text": "processed text",
            "duration": 2.1
        }
        mock_ai_predict.return_value = mock_ai_response
        
        # Make request
        response = client.post("/classify", json=sample_request)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify LLM was not called
        assert data["service_calls"]["llm_service"]["called"] is False
        assert data["confidence_analysis"]["triggered_llm"] is False
        
        # Verify all predictions use AI
        assert data["prediction"]["primary"]["source"] == "ai"
        assert data["prediction"]["secondary"]["source"] == "ai" 
        assert data["prediction"]["tertiary"]["source"] == "ai"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # Might be degraded if services down
        
        data = response.json()
        assert "status" in data
        assert "downstream_services" in data
        assert "ai_service" in data["downstream_services"]
        assert "llm_service" in data["downstream_services"]
    
    def test_config_endpoint(self, client):
        """Test configuration endpoint"""
        response = client.get("/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "default_thresholds" in data
        assert "service_urls" in data
        assert "timeouts" in data
        
        assert "primary" in data["default_thresholds"]
        assert "secondary" in data["default_thresholds"]
        assert "tertiary" in data["default_thresholds"]
    
    def test_invalid_request_validation(self, client):
        """Test request validation"""
        # Empty text
        response = client.post("/classify", json={
            "text": "",
            "predict_levels": ["primary"]
        })
        assert response.status_code == 400
        
        # Invalid prediction level
        response = client.post("/classify", json={
            "text": "test text",
            "predict_levels": ["invalid_level"]
        })
        assert response.status_code == 400
        
        # No prediction levels
        response = client.post("/classify", json={
            "text": "test text",
            "predict_levels": []
        })
        assert response.status_code == 400