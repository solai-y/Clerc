"""
Unit tests for response aggregation logic
"""
import pytest
from services.aggregator import ResponseAggregator
from models import PredictionLevel

class TestResponseAggregator:
    """Test response aggregation logic"""
    
    def test_merge_service_timing(self):
        """Test merging service timing information"""
        ai_predictions = {"duration": 2.1}
        llm_predictions = {"duration": 5.8}
        
        total = ResponseAggregator.merge_service_timing(ai_predictions, llm_predictions)
        assert total == 7.9
        
        # Test with no LLM predictions
        total = ResponseAggregator.merge_service_timing(ai_predictions, None)
        assert total == 2.1
    
    def test_create_prediction_level_from_ai(self):
        """Test creating prediction level from AI response"""
        ai_predictions = {
            "prediction": {
                "primary": {
                    "pred": "News",
                    "confidence": 0.95,
                    "reasoning": "AI reasoning"
                }
            }
        }
        
        prediction_level = ResponseAggregator._create_prediction_level_from_ai(
            "primary", ai_predictions, None
        )
        
        assert prediction_level is not None
        assert prediction_level.pred == "News"
        assert prediction_level.confidence == 0.95
        assert prediction_level.source == "ai"
        assert prediction_level.ai_prediction == ai_predictions["prediction"]["primary"]
    
    def test_create_prediction_level_from_llm(self):
        """Test creating prediction level from LLM response"""
        llm_predictions = {
            "prediction": {
                "primary": {
                    "pred": "Company",
                    "confidence": 0.98,
                    "reasoning": "LLM reasoning"
                }
            }
        }
        ai_predictions = {
            "prediction": {
                "primary": {
                    "pred": "News",
                    "confidence": 0.85
                }
            }
        }
        
        prediction_level = ResponseAggregator._create_prediction_level_from_llm(
            "primary", llm_predictions, ai_predictions
        )
        
        assert prediction_level is not None
        assert prediction_level.pred == "Company"
        assert prediction_level.confidence == 0.98
        assert prediction_level.source == "llm"
        assert prediction_level.reasoning == "LLM reasoning"
        assert prediction_level.llm_prediction == llm_predictions["prediction"]["primary"]
        assert prediction_level.ai_prediction == ai_predictions["prediction"]["primary"]
    
    def test_aggregate_predictions_ai_only(self):
        """Test aggregating predictions when only AI is used"""
        ai_predictions = {
            "prediction": {
                "primary": {"pred": "News", "confidence": 0.95},
                "secondary": {"pred": "Company", "confidence": 0.90}
            }
        }
        
        result = ResponseAggregator.aggregate_predictions(
            ai_predictions, None, [], ["primary", "secondary"]
        )
        
        assert result.primary is not None
        assert result.primary.source == "ai"
        assert result.primary.pred == "News"
        
        assert result.secondary is not None
        assert result.secondary.source == "ai"
        assert result.secondary.pred == "Company"
    
    def test_aggregate_predictions_hybrid(self):
        """Test aggregating predictions with hybrid AI/LLM usage"""
        ai_predictions = {
            "prediction": {
                "primary": {"pred": "News", "confidence": 0.95},
                "secondary": {"pred": "Company", "confidence": 0.80},
                "tertiary": {"pred": "Announcement", "confidence": 0.75}
            }
        }
        
        llm_predictions = {
            "prediction": {
                "secondary": {"pred": "Technology", "confidence": 0.92},
                "tertiary": {"pred": "Product_Launch", "confidence": 0.88}
            }
        }
        
        # LLM was called for secondary + tertiary levels
        result = ResponseAggregator.aggregate_predictions(
            ai_predictions, llm_predictions, ["secondary", "tertiary"], 
            ["primary", "secondary", "tertiary"]
        )
        
        # Primary should use AI prediction
        assert result.primary is not None
        assert result.primary.source == "ai"
        assert result.primary.pred == "News"
        
        # Secondary should use LLM prediction
        assert result.secondary is not None
        assert result.secondary.source == "llm"
        assert result.secondary.pred == "Technology"
        
        # Tertiary should use LLM prediction
        assert result.tertiary is not None
        assert result.tertiary.source == "llm"
        assert result.tertiary.pred == "Product_Launch"