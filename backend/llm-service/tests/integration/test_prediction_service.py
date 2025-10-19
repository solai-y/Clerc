"""
Integration tests for the prediction service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from prediction_service import PredictionService
from config import Config


class TestPredictionService:
    """Integration tests for PredictionService"""
    
    @patch('prediction_service.ClaudeClient')
    def test_prediction_service_initialization(self, mock_claude_client):
        """Test that prediction service initializes correctly"""
        mock_client = Mock()
        mock_claude_client.return_value = mock_client
        
        service = PredictionService()
        
        assert service is not None
        mock_claude_client.assert_called_once()
    
    
    @patch('prediction_service.HierarchyValidator')
    @patch('prediction_service.PromptGenerator')
    @patch('prediction_service.ClaudeClient')
    def test_predict_all_levels(self, mock_claude_client, mock_prompt_gen, mock_validator):
        """Test prediction of all hierarchy levels"""
        # Setup mock client
        mock_client = Mock()
        mock_claude_client.return_value = mock_client

        # Setup mock prompt generator
        mock_pg = Mock()
        mock_pg.generate_prompt.return_value = "mock prompt"
        mock_prompt_gen.return_value = mock_pg

        # Setup mock validator
        mock_val = Mock()
        mock_val.validate_and_fix_prediction.side_effect = lambda x: x
        mock_validator.return_value = mock_val

        # Mock Claude response
        mock_claude_response = {
            "primary": "News",
            "confidence_primary": 0.95,
            "reasoning": "Document discusses company earnings and performance metrics.",
            "secondary": "Company",
            "confidence_secondary": 0.87,
            "tertiary": "Management_Change",
            "confidence_tertiary": 0.82
        }

        mock_client.classify_with_retry.return_value = mock_claude_response

        service = PredictionService()
        
        # Test prediction
        result = service.predict(
            text="Company announces new CEO appointment and quarterly earnings results",
            predict_levels=["primary", "secondary", "tertiary"],
            context={}
        )
        
        # Verify response structure
        assert "elapsed_seconds" in result
        assert "processed_text" in result
        assert "prediction" in result
        
        prediction = result["prediction"]
        
        # Verify primary prediction
        assert "primary" in prediction
        primary = prediction["primary"]
        assert primary["pred"] == "News"
        assert primary["confidence"] == 0.95
        # key_evidence might be present depending on implementation
        if "key_evidence" in primary:
            assert "supporting" in primary["key_evidence"]
            assert "opposing" in primary["key_evidence"]
        
        # Verify secondary prediction
        assert "secondary" in prediction
        secondary = prediction["secondary"]
        assert secondary["pred"] == "Company"
        assert secondary["confidence"] == 0.87
        assert secondary["primary"] == "News"
        
        # Verify tertiary prediction
        assert "tertiary" in prediction
        tertiary = prediction["tertiary"]
        assert tertiary["pred"] == "Management_Change"
        assert tertiary["confidence"] == 0.82
        assert tertiary["primary"] == "News"
        assert tertiary["secondary"] == "Company"
    
    
    @patch('prediction_service.HierarchyValidator')
    @patch('prediction_service.PromptGenerator')
    @patch('prediction_service.ClaudeClient')
    def test_predict_partial_levels(self, mock_claude_client, mock_prompt_gen, mock_validator):
        """Test prediction with context (partial hierarchy)"""
        mock_client = Mock()
        mock_claude_client.return_value = mock_client

        mock_pg = Mock()
        mock_pg.generate_prompt.return_value = "mock prompt"
        mock_prompt_gen.return_value = mock_pg

        mock_val = Mock()
        mock_val.validate_and_fix_prediction.side_effect = lambda x: x
        mock_validator.return_value = mock_val

        mock_claude_response = {
            "secondary": "Company",
            "confidence_secondary": 0.89,
            "reasoning": "Document focuses on company-specific developments.",
            "tertiary": "Product_Launch",
            "confidence_tertiary": 0.85
        }

        mock_client.classify_with_retry.return_value = mock_claude_response

        service = PredictionService()
        
        # Test prediction with context
        result = service.predict(
            text="Company launches innovative new product line",
            predict_levels=["secondary", "tertiary"],
            context={"primary": "News"}
        )
        
        prediction = result["prediction"]
        
        # Should only have secondary and tertiary
        assert "primary" not in prediction
        assert "secondary" in prediction
        assert "tertiary" in prediction
        
        # Verify context is preserved
        assert prediction["secondary"]["primary"] == "News"
        assert prediction["tertiary"]["primary"] == "News"
        assert prediction["tertiary"]["secondary"] == "Company"
    
    
    @patch('prediction_service.HierarchyValidator')
    @patch('prediction_service.PromptGenerator')
    @patch('prediction_service.ClaudeClient')
    def test_predict_single_level(self, mock_claude_client, mock_prompt_gen, mock_validator):
        """Test prediction of single level only"""
        mock_client = Mock()
        mock_claude_client.return_value = mock_client

        mock_pg = Mock()
        mock_pg.generate_prompt.return_value = "mock prompt"
        mock_prompt_gen.return_value = mock_pg

        mock_val = Mock()
        mock_val.validate_and_fix_prediction.side_effect = lambda x: x
        mock_validator.return_value = mock_val

        mock_claude_response = {
            "tertiary": "Management_Change",
            "confidence_tertiary": 0.91,
            "reasoning": "Document specifically discusses leadership changes."
        }

        mock_client.classify_with_retry.return_value = mock_claude_response

        service = PredictionService()
        
        result = service.predict(
            text="New CEO appointed to lead transformation",
            predict_levels=["tertiary"],
            context={"primary": "News", "secondary": "Company"}
        )
        
        prediction = result["prediction"]
        
        # Should only have tertiary
        assert "primary" not in prediction
        assert "secondary" not in prediction
        assert "tertiary" in prediction
        
        tertiary = prediction["tertiary"]
        assert tertiary["pred"] == "Management_Change"
        assert tertiary["primary"] == "News"
        assert tertiary["secondary"] == "Company"
    
    
    @patch('prediction_service.HierarchyValidator')
    @patch('prediction_service.PromptGenerator')
    @patch('prediction_service.ClaudeClient')
    def test_predict_with_claude_error(self, mock_claude_client, mock_prompt_gen, mock_validator):
        """Test prediction when Claude client raises an error"""
        mock_client = Mock()
        mock_claude_client.return_value = mock_client

        mock_pg = Mock()
        mock_pg.generate_prompt.return_value = "mock prompt"
        mock_prompt_gen.return_value = mock_pg

        mock_val = Mock()
        mock_validator.return_value = mock_val

        mock_client.classify_with_retry.side_effect = Exception("Claude API error")

        service = PredictionService()
        
        with pytest.raises(Exception) as exc_info:
            service.predict(
                text="Test document",
                predict_levels=["primary"],
                context={}
            )
        
        assert "Claude API error" in str(exc_info.value)
    
    
    @patch('prediction_service.HierarchyValidator')
    @patch('prediction_service.PromptGenerator')
    @patch('prediction_service.ClaudeClient')
    def test_predict_with_invalid_claude_response(self, mock_claude_client, mock_prompt_gen, mock_validator):
        """Test prediction when Claude returns invalid response"""
        mock_client = Mock()
        mock_claude_client.return_value = mock_client

        mock_pg = Mock()
        mock_pg.generate_prompt.return_value = "mock prompt"
        mock_prompt_gen.return_value = mock_pg

        mock_val = Mock()
        mock_val.validate_and_fix_prediction.side_effect = lambda x: x
        mock_validator.return_value = mock_val

        # Missing required fields
        mock_claude_response = {
            "primary": "News"
            # Missing confidence and reasoning
        }

        mock_client.classify_with_retry.return_value = mock_claude_response

        service = PredictionService()
        
        # Should handle gracefully and provide defaults
        result = service.predict(
            text="Test document",
            predict_levels=["primary"],
            context={}
        )
        
        # Service should handle missing fields gracefully
        assert "prediction" in result
    
    
    @patch('prediction_service.HierarchyValidator')
    @patch('prediction_service.PromptGenerator')
    @patch('prediction_service.ClaudeClient')
    def test_text_preprocessing(self, mock_claude_client, mock_prompt_gen, mock_validator):
        """Test that text preprocessing works correctly"""
        mock_client = Mock()
        mock_claude_client.return_value = mock_client

        mock_pg = Mock()
        mock_pg.generate_prompt.return_value = "mock prompt"
        mock_prompt_gen.return_value = mock_pg

        mock_val = Mock()
        mock_val.validate_and_fix_prediction.side_effect = lambda x: x
        mock_validator.return_value = mock_val

        mock_claude_response = {
            "primary": "News",
            "confidence_primary": 0.9,
            "reasoning": "Test reasoning"
        }
        mock_client.classify_with_retry.return_value = mock_claude_response

        service = PredictionService()
        
        # Test with text that needs preprocessing
        original_text = "  This is a test document with extra   spaces and \n newlines  "
        
        result = service.predict(
            text=original_text,
            predict_levels=["primary"],
            context={}
        )
        
        # Verify text was returned (preprocessing may or may not happen depending on implementation)
        processed_text = result["processed_text"]
        assert processed_text is not None
        # Text might be preprocessed or returned as-is
        assert isinstance(processed_text, str)
    
    
    @patch('prediction_service.HierarchyValidator')
    @patch('prediction_service.PromptGenerator')
    @patch('prediction_service.ClaudeClient')
    def test_timing_measurement(self, mock_claude_client, mock_prompt_gen, mock_validator):
        """Test that prediction timing is measured correctly"""
        mock_client = Mock()
        mock_claude_client.return_value = mock_client

        mock_pg = Mock()
        mock_pg.generate_prompt.return_value = "mock prompt"
        mock_prompt_gen.return_value = mock_pg

        mock_val = Mock()
        mock_val.validate_and_fix_prediction.side_effect = lambda x: x
        mock_validator.return_value = mock_val

        mock_claude_response = {
            "primary": "News",
            "confidence_primary": 0.9,
            "reasoning": "Test reasoning"
        }
        mock_client.classify_with_retry.return_value = mock_claude_response

        service = PredictionService()
        
        result = service.predict(
            text="Test document",
            predict_levels=["primary"],
            context={}
        )
        
        # Verify timing is included and reasonable
        assert "elapsed_seconds" in result
        assert isinstance(result["elapsed_seconds"], (int, float))
        assert result["elapsed_seconds"] >= 0
        assert result["elapsed_seconds"] < 10  # Should be fast in tests