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
        """Test creating prediction levels from AI response (multi-label)"""
        ai_predictions = {
            "prediction": {
                "primary": [
                    {
                        "label": "News",
                        "confidence": 0.95,
                        "key_evidence": "AI reasoning"
                    }
                ]
            }
        }

        prediction_levels = ResponseAggregator._create_prediction_level_from_ai(
            "primary", ai_predictions, None
        )

        assert prediction_levels is not None
        assert len(prediction_levels) == 1
        assert prediction_levels[0].pred == "News"
        assert prediction_levels[0].confidence == 0.95
        assert prediction_levels[0].source == "ai"
        assert prediction_levels[0].ai_prediction == ai_predictions["prediction"]["primary"][0]
    
    def test_create_prediction_level_from_llm(self):
        """Test creating prediction level from LLM response (returns as list)"""
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
                "primary": [
                    {
                        "label": "News",
                        "confidence": 0.85
                    }
                ]
            }
        }

        prediction_levels = ResponseAggregator._create_prediction_level_from_llm(
            "primary", llm_predictions, ai_predictions
        )

        assert prediction_levels is not None
        assert len(prediction_levels) == 1
        assert prediction_levels[0].pred == "Company"
        assert prediction_levels[0].confidence == 0.98
        assert prediction_levels[0].source == "llm"
        assert prediction_levels[0].reasoning == "LLM reasoning"
        assert prediction_levels[0].llm_prediction == llm_predictions["prediction"]["primary"]
        assert prediction_levels[0].ai_prediction == ai_predictions["prediction"]["primary"]
    
    def test_aggregate_predictions_ai_only(self):
        """Test aggregating predictions when only AI is used (multi-label)"""
        ai_predictions = {
            "prediction": {
                "primary": [{"label": "News", "confidence": 0.95, "key_evidence": "AI reasoning"}],
                "secondary": [{"label": "Company", "confidence": 0.90, "key_evidence": "AI reasoning 2"}]
            }
        }

        result = ResponseAggregator.aggregate_predictions(
            ai_predictions, None, [], ["primary", "secondary"]
        )

        assert result.primary is not None
        assert len(result.primary) == 1
        assert result.primary[0].source == "ai"
        assert result.primary[0].pred == "News"

        assert result.secondary is not None
        assert len(result.secondary) == 1
        assert result.secondary[0].source == "ai"
        assert result.secondary[0].pred == "Company"

    def test_aggregate_predictions_hybrid(self):
        """Test aggregating predictions with hybrid AI/LLM usage (multi-label)"""
        ai_predictions = {
            "prediction": {
                "primary": [{"label": "News", "confidence": 0.95, "key_evidence": "AI reasoning"}],
                "secondary": [{"label": "Company", "confidence": 0.80, "key_evidence": "AI reasoning 2"}],
                "tertiary": [{"label": "Announcement", "confidence": 0.75, "key_evidence": "AI reasoning 3"}]
            }
        }

        llm_predictions = {
            "prediction": {
                "secondary": {"pred": "Technology", "confidence": 0.92, "reasoning": "LLM reasoning"},
                "tertiary": {"pred": "Product_Launch", "confidence": 0.88, "reasoning": "LLM reasoning 2"}
            }
        }

        # LLM was called for secondary + tertiary levels
        result = ResponseAggregator.aggregate_predictions(
            ai_predictions, llm_predictions, ["secondary", "tertiary"],
            ["primary", "secondary", "tertiary"]
        )

        # Primary should use AI prediction
        assert result.primary is not None
        assert len(result.primary) == 1
        assert result.primary[0].source == "ai"
        assert result.primary[0].pred == "News"

        # Secondary should use LLM prediction
        assert result.secondary is not None
        assert len(result.secondary) == 1
        assert result.secondary[0].source == "llm"
        assert result.secondary[0].pred == "Technology"

        # Tertiary should use LLM prediction
        assert result.tertiary is not None
        assert len(result.tertiary) == 1
        assert result.tertiary[0].source == "llm"
        assert result.tertiary[0].pred == "Product_Launch"