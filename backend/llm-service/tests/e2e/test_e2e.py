"""
End-to-end tests for LLM service
"""
import pytest
import requests
import time
import json
from typing import Dict, Any


class TestLLMServiceE2E:
    """End-to-end tests for the LLM service"""
    
    BASE_URL = "http://localhost:5005"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test - wait for service to be ready"""
        max_retries = 30
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(f"{self.BASE_URL}/health", timeout=2)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass
            
            retry_count += 1
            time.sleep(1)
        
        if retry_count >= max_retries:
            pytest.skip("LLM service not available for E2E tests")
    
    
    def test_service_health_check(self):
        """Test that the service is healthy and responding"""
        response = requests.get(f"{self.BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "llm-classification"
    
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = requests.get(f"{self.BASE_URL}/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "LLM Document Classification"
        assert data["status"] == "healthy"
    
    
    def test_full_prediction_workflow(self):
        """Test complete prediction workflow with all levels"""
        request_data = {
            "text": "Apple Inc. announced today that Tim Cook will step down as CEO, with Chief Operating Officer Jeff Williams taking over the role effective immediately. The transition comes as Apple continues to expand its services revenue and focuses on new product categories including augmented reality and autonomous vehicles.",
            "predict": ["primary", "secondary", "tertiary"],
            "context": {}
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "elapsed_seconds" in data
        assert "processed_text" in data
        assert "prediction" in data
        
        prediction = data["prediction"]
        
        # Should have all three levels
        assert "primary" in prediction
        assert "secondary" in prediction
        assert "tertiary" in prediction
        
        # Validate primary structure
        primary = prediction["primary"]
        assert "pred" in primary
        assert "confidence" in primary
        assert "key_evidence" in primary
        assert isinstance(primary["confidence"], (int, float))
        assert 0 <= primary["confidence"] <= 1
        
        # Validate secondary structure
        secondary = prediction["secondary"]
        assert "pred" in secondary
        assert "confidence" in secondary
        assert "primary" in secondary
        assert "key_evidence" in secondary
        
        # Validate tertiary structure
        tertiary = prediction["tertiary"]
        assert "pred" in tertiary
        assert "confidence" in tertiary
        assert "primary" in tertiary
        assert "secondary" in tertiary
        assert "key_evidence" in tertiary
    
    
    def test_partial_prediction_workflow(self):
        """Test prediction workflow with partial context"""
        request_data = {
            "text": "The Federal Reserve announced a 0.25% interest rate cut today, citing concerns about global economic growth and trade tensions. The decision was unanimous among voting members.",
            "predict": ["secondary", "tertiary"],
            "context": {
                "primary": "News"
            }
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        prediction = data["prediction"]
        
        # Should only have secondary and tertiary
        assert "primary" not in prediction
        assert "secondary" in prediction
        assert "tertiary" in prediction
        
        # Context should be preserved
        assert prediction["secondary"]["primary"] == "News"
        assert prediction["tertiary"]["primary"] == "News"
    
    
    def test_single_level_prediction(self):
        """Test prediction of single level only"""
        request_data = {
            "text": "Microsoft announces new AI capabilities in Office 365, including advanced natural language processing and automated document generation features.",
            "predict": ["tertiary"],
            "context": {
                "primary": "News",
                "secondary": "Company"
            }
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        prediction = data["prediction"]
        
        # Should only have tertiary
        assert "primary" not in prediction
        assert "secondary" not in prediction
        assert "tertiary" in prediction
        
        tertiary = prediction["tertiary"]
        assert tertiary["primary"] == "News"
        assert tertiary["secondary"] == "Company"
    
    
    def test_invalid_request_empty_text(self):
        """Test error handling for empty text"""
        request_data = {
            "text": "",
            "predict": ["primary"],
            "context": {}
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=request_data)
        
        assert response.status_code == 400
        assert "Text cannot be empty" in response.json()["detail"]
    
    
    def test_invalid_request_no_predict_levels(self):
        """Test error handling for missing prediction levels"""
        request_data = {
            "text": "Sample document text",
            "predict": [],
            "context": {}
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=request_data)
        
        assert response.status_code == 400
        assert "Must specify at least one prediction level" in response.json()["detail"]
    
    
    def test_invalid_request_bad_prediction_level(self):
        """Test error handling for invalid prediction levels"""
        request_data = {
            "text": "Sample document text",
            "predict": ["invalid_level"],
            "context": {}
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=request_data)
        
        assert response.status_code == 400
        assert "Invalid prediction level" in response.json()["detail"]
    
    
    def test_malformed_json(self):
        """Test error handling for malformed JSON"""
        response = requests.post(
            f"{self.BASE_URL}/predict",
            data="malformed json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    
    def test_missing_required_fields(self):
        """Test error handling for missing required fields"""
        request_data = {
            "predict": ["primary"],
            "context": {}
            # Missing 'text' field
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=request_data)
        
        assert response.status_code == 422
    
    
    def test_performance_timing(self):
        """Test that response times are reasonable"""
        request_data = {
            "text": "Amazon reported strong quarterly earnings, beating analyst expectations on both revenue and profit margins. The company's cloud computing division AWS continued to show robust growth.",
            "predict": ["primary", "secondary", "tertiary"],
            "context": {}
        }
        
        start_time = time.time()
        response = requests.post(f"{self.BASE_URL}/predict", json=request_data)
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Response should be reasonably fast (under 30 seconds for real LLM)
        actual_time = end_time - start_time
        assert actual_time < 30
        
        # Reported timing should be close to actual timing
        data = response.json()
        reported_time = data["elapsed_seconds"]
        assert abs(actual_time - reported_time) < 2  # Allow 2 second difference
    
    
    def test_evidence_quality(self):
        """Test that key evidence is provided in the expected format"""
        request_data = {
            "text": "Tesla stock surged 15% after the company announced record vehicle deliveries and plans for a new Gigafactory in Texas. CEO Elon Musk praised the engineering team's efforts.",
            "predict": ["primary", "secondary", "tertiary"],
            "context": {}
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        prediction = data["prediction"]
        
        # Check that all levels have key evidence
        for level in ["primary", "secondary", "tertiary"]:
            if level in prediction:
                evidence = prediction[level]["key_evidence"]
                assert "supporting" in evidence
                assert "opposing" in evidence
                
                # Evidence should be strings (LLM-generated explanations)
                assert isinstance(evidence["supporting"], str)
                assert isinstance(evidence["opposing"], str)
                
                # Evidence should not be empty
                assert len(evidence["supporting"].strip()) > 0
                assert len(evidence["opposing"].strip()) > 0
    
    
    def test_confidence_scores(self):
        """Test that confidence scores are reasonable"""
        request_data = {
            "text": "The World Health Organization announced new guidelines for pandemic preparedness, emphasizing the importance of international cooperation and rapid response mechanisms.",
            "predict": ["primary", "secondary", "tertiary"],
            "context": {}
        }
        
        response = requests.post(f"{self.BASE_URL}/predict", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        prediction = data["prediction"]
        
        # Check confidence scores for all levels
        for level in ["primary", "secondary", "tertiary"]:
            if level in prediction:
                confidence = prediction[level]["confidence"]
                assert isinstance(confidence, (int, float))
                assert 0 <= confidence <= 1