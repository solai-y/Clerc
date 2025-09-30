"""
Response aggregation logic for combining AI and LLM predictions
"""
import logging
from typing import Dict, Any, List, Optional
from models import PredictionLevel, PredictionResponse

logger = logging.getLogger(__name__)

class ResponseAggregator:
    """Aggregates responses from AI and LLM services"""
    
    @staticmethod
    def aggregate_predictions(ai_predictions: Dict[str, Any],
                            llm_predictions: Optional[Dict[str, Any]],
                            llm_levels: List[str],
                            predict_levels: List[str]) -> PredictionResponse:
        """
        Aggregate AI and LLM predictions into final response
        
        Args:
            ai_predictions: AI service response
            llm_predictions: LLM service response (if called)
            llm_levels: Levels that were processed by LLM
            predict_levels: All requested prediction levels
            
        Returns:
            Aggregated prediction response
        """
        result = PredictionResponse()
        
        for level in predict_levels:
            if level in llm_levels and llm_predictions:
                # Use LLM prediction for this level
                prediction_level = ResponseAggregator._create_prediction_level_from_llm(
                    level, llm_predictions, ai_predictions
                )
            else:
                # Use AI prediction for this level
                prediction_level = ResponseAggregator._create_prediction_level_from_ai(
                    level, ai_predictions, llm_predictions
                )
            
            # Set the prediction level on the result
            if level == "primary":
                result.primary = prediction_level
            elif level == "secondary":
                result.secondary = prediction_level
            elif level == "tertiary":
                result.tertiary = prediction_level
        
        return result
    
    @staticmethod
    def _create_prediction_level_from_ai(level: str, 
                                       ai_predictions: Dict[str, Any],
                                       llm_predictions: Optional[Dict[str, Any]]) -> Optional[PredictionLevel]:
        """Create prediction level using AI service response"""
        ai_pred = ai_predictions.get("prediction", {}).get(level, {})
        if not ai_pred:
            logger.warning(f"No AI prediction found for level: {level}")
            return None
        
        # Build context references
        context = {}
        if level in ["secondary", "tertiary"]:
            primary_pred = ai_predictions.get("prediction", {}).get("primary", {})
            if primary_pred:
                context["primary"] = primary_pred.get("pred")
        
        if level == "tertiary":
            secondary_pred = ai_predictions.get("prediction", {}).get("secondary", {})
            if secondary_pred:
                context["secondary"] = secondary_pred.get("pred")
        
        # Get LLM prediction for this level if available (even if not used)
        llm_pred_for_level = None
        if llm_predictions:
            llm_pred_for_level = llm_predictions.get("prediction", {}).get(level)

        return PredictionLevel(
            pred=ai_pred.get("pred", ""),
            confidence=ai_pred.get("confidence", 0.0),
            reasoning=ai_pred.get("reasoning"),
            source="ai",
            primary=context.get("primary"),
            secondary=context.get("secondary"),
            ai_prediction=ai_pred,
            llm_prediction=llm_pred_for_level
        )
    
    @staticmethod
    def _create_prediction_level_from_llm(level: str,
                                        llm_predictions: Dict[str, Any],
                                        ai_predictions: Dict[str, Any]) -> Optional[PredictionLevel]:
        """Create prediction level using LLM service response"""
        llm_pred = llm_predictions.get("prediction", {}).get(level, {})
        if not llm_pred:
            logger.warning(f"No LLM prediction found for level: {level}")
            return None
        
        # Get AI prediction for this level to preserve it
        ai_pred_for_level = ai_predictions.get("prediction", {}).get(level, {})

        return PredictionLevel(
            pred=llm_pred.get("pred", ""),
            confidence=llm_pred.get("confidence", 0.0),
            reasoning=llm_pred.get("reasoning"),
            source="llm",
            primary=llm_pred.get("primary"),
            secondary=llm_pred.get("secondary"),
            ai_prediction=ai_pred_for_level,
            llm_prediction=llm_pred
        )
    
    @staticmethod
    def merge_service_timing(ai_predictions: Dict[str, Any],
                           llm_predictions: Optional[Dict[str, Any]]) -> float:
        """
        Calculate total elapsed time from both services
        
        Args:
            ai_predictions: AI service response with duration
            llm_predictions: LLM service response with duration (if called)
            
        Returns:
            Total elapsed seconds
        """
        ai_duration = ai_predictions.get("duration", 0.0)
        llm_duration = llm_predictions.get("duration", 0.0) if llm_predictions else 0.0
        
        # Services are called sequentially, so add the durations
        total_duration = ai_duration + llm_duration
        
        logger.info(f"Total elapsed time: AI={ai_duration:.2f}s + LLM={llm_duration:.2f}s = {total_duration:.2f}s")
        
        return total_duration