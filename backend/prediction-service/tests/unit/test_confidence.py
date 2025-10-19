"""
Unit tests for confidence evaluation logic
"""
import pytest
from utils.confidence import ConfidenceEvaluator

class TestConfidenceEvaluator:
    """Test confidence evaluation logic"""
    
    def test_evaluate_thresholds_all_above(self):
        """Test when all confidence levels are above threshold (multi-label)"""
        ai_predictions = {
            "prediction": {
                "primary": [{"label": "News", "confidence": 0.95}],
                "secondary": [{"label": "Company", "confidence": 0.90}],
                "tertiary": [{"label": "Announcement", "confidence": 0.85}]
            }
        }
        thresholds = {"primary": 0.90, "secondary": 0.85, "tertiary": 0.80}
        predict_levels = ["primary", "secondary", "tertiary"]

        needs_llm, trigger_level, levels_below = ConfidenceEvaluator.evaluate_thresholds(
            ai_predictions, thresholds, predict_levels
        )

        assert needs_llm is False
        assert trigger_level is None
        assert levels_below == []
    
    def test_evaluate_thresholds_primary_below(self):
        """Test when ALL primary tags are below threshold (should trigger all levels)"""
        ai_predictions = {
            "prediction": {
                "primary": [{"label": "News", "confidence": 0.85}],
                "secondary": [{"label": "Company", "confidence": 0.90}],
                "tertiary": [{"label": "Announcement", "confidence": 0.85}]
            }
        }
        thresholds = {"primary": 0.90, "secondary": 0.85, "tertiary": 0.80}
        predict_levels = ["primary", "secondary", "tertiary"]

        needs_llm, trigger_level, levels_below = ConfidenceEvaluator.evaluate_thresholds(
            ai_predictions, thresholds, predict_levels
        )

        assert needs_llm is True
        assert trigger_level == "primary"
        assert levels_below == ["primary", "secondary", "tertiary"]
    
    def test_evaluate_thresholds_secondary_below(self):
        """Test when ALL secondary tags are below threshold (should trigger secondary + tertiary)"""
        ai_predictions = {
            "prediction": {
                "primary": [{"label": "News", "confidence": 0.95}],
                "secondary": [{"label": "Company", "confidence": 0.80}],
                "tertiary": [{"label": "Announcement", "confidence": 0.85}]
            }
        }
        thresholds = {"primary": 0.90, "secondary": 0.85, "tertiary": 0.80}
        predict_levels = ["primary", "secondary", "tertiary"]

        needs_llm, trigger_level, levels_below = ConfidenceEvaluator.evaluate_thresholds(
            ai_predictions, thresholds, predict_levels
        )

        assert needs_llm is True
        assert trigger_level == "secondary"
        assert levels_below == ["secondary", "tertiary"]

    def test_evaluate_thresholds_tertiary_only_below(self):
        """Test when ALL tertiary tags are below threshold"""
        ai_predictions = {
            "prediction": {
                "primary": [{"label": "News", "confidence": 0.95}],
                "secondary": [{"label": "Company", "confidence": 0.90}],
                "tertiary": [{"label": "Announcement", "confidence": 0.75}]
            }
        }
        thresholds = {"primary": 0.90, "secondary": 0.85, "tertiary": 0.80}
        predict_levels = ["primary", "secondary", "tertiary"]

        needs_llm, trigger_level, levels_below = ConfidenceEvaluator.evaluate_thresholds(
            ai_predictions, thresholds, predict_levels
        )

        assert needs_llm is True
        assert trigger_level == "tertiary"
        assert levels_below == ["tertiary"]

    def test_evaluate_thresholds_multi_label_mixed(self):
        """Test multi-label with some tags above and some below threshold"""
        ai_predictions = {
            "prediction": {
                "primary": [
                    {"label": "News", "confidence": 0.95},
                    {"label": "Disclosure", "confidence": 0.88}
                ],
                "secondary": [
                    {"label": "Company", "confidence": 0.82},
                    {"label": "Industry", "confidence": 0.79}
                ]
            }
        }
        thresholds = {"primary": 0.85, "secondary": 0.85}
        predict_levels = ["primary", "secondary"]

        # Should NOT trigger LLM because primary has tags above threshold
        needs_llm, trigger_level, levels_below = ConfidenceEvaluator.evaluate_thresholds(
            ai_predictions, thresholds, predict_levels
        )

        assert needs_llm is True  # All secondary tags below threshold
        assert trigger_level == "secondary"
        assert levels_below == ["secondary"]
    
    def test_determine_llm_levels(self):
        """Test LLM level determination based on trigger"""
        # Primary trigger should process all levels
        llm_levels = ConfidenceEvaluator.determine_llm_levels(
            "primary", ["primary", "secondary", "tertiary"]
        )
        assert llm_levels == ["primary", "secondary", "tertiary"]
        
        # Secondary trigger should process secondary + tertiary
        llm_levels = ConfidenceEvaluator.determine_llm_levels(
            "secondary", ["primary", "secondary", "tertiary"]
        )
        assert llm_levels == ["secondary", "tertiary"]
        
        # Tertiary trigger should process only tertiary
        llm_levels = ConfidenceEvaluator.determine_llm_levels(
            "tertiary", ["primary", "secondary", "tertiary"]
        )
        assert llm_levels == ["tertiary"]
    
    def test_build_llm_context(self):
        """Test building context for LLM service (multi-label support)"""
        ai_predictions = {
            "prediction": {
                "primary": [{"label": "News", "confidence": 0.95}],
                "secondary": [{"label": "Company", "confidence": 0.90}],
                "tertiary": [{"label": "Announcement", "confidence": 0.85}]
            }
        }

        # If LLM processes secondary + tertiary, context should include primary
        context = ConfidenceEvaluator.build_llm_context(
            ai_predictions, ["secondary", "tertiary"]
        )
        assert context == {"primary": "News"}

        # If LLM processes only tertiary, context should include primary + secondary
        context = ConfidenceEvaluator.build_llm_context(
            ai_predictions, ["tertiary"]
        )
        assert context == {"primary": "News", "secondary": "Company"}

        # If LLM processes all levels, context should be empty
        context = ConfidenceEvaluator.build_llm_context(
            ai_predictions, ["primary", "secondary", "tertiary"]
        )
        assert context == {}