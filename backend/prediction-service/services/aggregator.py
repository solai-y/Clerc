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
        Aggregate AI and LLM predictions into final response (multi-label support)

        Args:
            ai_predictions: AI service response with multi-label arrays
            llm_predictions: LLM service response (if called)
            llm_levels: Levels that were processed by LLM
            predict_levels: All requested prediction levels

        Returns:
            Aggregated prediction response with lists of predictions per level
        """
        result = PredictionResponse()

        for level in predict_levels:
            if level in llm_levels and llm_predictions:
                # Use LLM prediction for this level (returns list)
                prediction_levels = ResponseAggregator._create_prediction_level_from_llm(
                    level, llm_predictions, ai_predictions
                )
            else:
                # Use AI predictions for this level (returns list)
                prediction_levels = ResponseAggregator._create_prediction_level_from_ai(
                    level, ai_predictions, llm_predictions
                )

            # Set the prediction levels on the result (now lists)
            if level == "primary":
                result.primary = prediction_levels
            elif level == "secondary":
                result.secondary = prediction_levels
            elif level == "tertiary":
                result.tertiary = prediction_levels

        return result
    
    @staticmethod
    def _create_prediction_level_from_ai(level: str,
                                       ai_predictions: Dict[str, Any],
                                       llm_predictions: Optional[Dict[str, Any]]) -> Optional[List[PredictionLevel]]:
        """Create prediction levels using AI service response (multi-label support)"""
        ai_preds = ai_predictions.get("prediction", {}).get(level, [])
        if not isinstance(ai_preds, list):
            logger.warning(f"Expected list for level {level}, got {type(ai_preds)}")
            return None

        if not ai_preds:
            logger.warning(f"No AI predictions found for level: {level}")
            return None

        # Build context references from first prediction in parent levels
        context = {}
        if level in ["secondary", "tertiary"]:
            primary_preds = ai_predictions.get("prediction", {}).get("primary", [])
            if isinstance(primary_preds, list) and primary_preds:
                context["primary"] = primary_preds[0].get("label")

        if level == "tertiary":
            secondary_preds = ai_predictions.get("prediction", {}).get("secondary", [])
            if isinstance(secondary_preds, list) and secondary_preds:
                context["secondary"] = secondary_preds[0].get("label")

        # Get LLM prediction for this level if available (even if not used)
        llm_pred_for_level = None
        if llm_predictions:
            llm_pred_for_level = llm_predictions.get("prediction", {}).get(level)

        # Create PredictionLevel for each AI prediction
        prediction_levels = []
        for ai_pred in ai_preds:
            # Convert key_evidence to string if it's a dict
            key_evidence = ai_pred.get("key_evidence")
            if isinstance(key_evidence, dict):
                # Convert SHAP evidence dict to readable string
                key_evidence = str(key_evidence)

            prediction_levels.append(PredictionLevel(
                pred=ai_pred.get("label", ""),
                confidence=ai_pred.get("confidence", 0.0),
                reasoning=key_evidence,
                source="ai",
                primary=context.get("primary"),
                secondary=context.get("secondary"),
                ai_prediction=ai_pred,
                llm_prediction=llm_pred_for_level
            ))

        return prediction_levels
    
    @staticmethod
    def _create_prediction_level_from_llm(level: str,
                                        llm_predictions: Dict[str, Any],
                                        ai_predictions: Dict[str, Any]) -> Optional[List[PredictionLevel]]:
        """Create prediction level using LLM service response (returns as list for consistency)"""
        llm_pred = llm_predictions.get("prediction", {}).get(level, {})
        if not llm_pred:
            logger.warning(f"No LLM prediction found for level: {level}")
            return None

        # Get AI predictions for this level to preserve them
        ai_preds_for_level = ai_predictions.get("prediction", {}).get(level, [])

        # LLM returns single prediction, wrap it in a list for multi-label consistency
        return [PredictionLevel(
            pred=llm_pred.get("pred", ""),
            confidence=llm_pred.get("confidence", 0.0),
            reasoning=llm_pred.get("reasoning"),
            source="llm",
            primary=llm_pred.get("primary"),
            secondary=llm_pred.get("secondary"),
            ai_prediction=ai_preds_for_level,  # Include all AI predictions
            llm_prediction=llm_pred
        )]
    
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