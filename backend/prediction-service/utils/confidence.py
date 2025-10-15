"""
Confidence evaluation logic for hierarchical predictions
"""
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class ConfidenceEvaluator:
    """Evaluates confidence thresholds and determines LLM triggering"""

    @staticmethod
    def prune_low_confidence_tags(ai_predictions: Dict[str, Any],
                                   thresholds: Dict[str, float]) -> Dict[str, Any]:
        """
        Prune tags below confidence threshold from multi-label predictions

        Args:
            ai_predictions: AI service predictions with multi-label arrays
            thresholds: Confidence thresholds per level

        Returns:
            Pruned predictions with only tags above threshold
        """
        pruned_predictions = {"prediction": {}}

        for level in ["primary", "secondary", "tertiary"]:
            level_predictions = ai_predictions.get("prediction", {}).get(level, [])
            threshold = thresholds.get(level, 0.8)

            if isinstance(level_predictions, list):
                # Filter predictions that meet threshold
                pruned = [
                    pred for pred in level_predictions
                    if pred.get("confidence", 0.0) >= threshold
                ]
                pruned_predictions["prediction"][level] = pruned

                if pruned:
                    logger.info(f"Level {level}: kept {len(pruned)}/{len(level_predictions)} tags above threshold {threshold}")
                else:
                    logger.info(f"Level {level}: no tags above threshold {threshold}, removed all {len(level_predictions)} predictions")
            else:
                pruned_predictions["prediction"][level] = []

        # Copy over other fields
        for key in ai_predictions:
            if key != "prediction":
                pruned_predictions[key] = ai_predictions[key]

        return pruned_predictions

    @staticmethod
    def evaluate_thresholds(ai_predictions: Dict[str, Any],
                          thresholds: Dict[str, float],
                          predict_levels: List[str]) -> Tuple[bool, str, List[str]]:
        """
        Evaluate AI predictions against confidence thresholds for multi-label support

        For multi-label predictions:
        - If ALL tags in a level are below threshold (or level has no tags), trigger LLM
        - This means the level has no confident predictions

        Args:
            ai_predictions: AI service predictions with multi-label arrays
            thresholds: Confidence thresholds per level
            predict_levels: Requested prediction levels

        Returns:
            Tuple of (needs_llm, trigger_level, levels_below_threshold)
        """
        levels_below_threshold = []
        trigger_level = None

        # Check hierarchically: primary -> secondary -> tertiary
        hierarchy = ["primary", "secondary", "tertiary"]

        for level in hierarchy:
            if level not in predict_levels:
                continue

            # Get AI predictions for this level (now an array)
            ai_preds = ai_predictions.get("prediction", {}).get(level, [])
            if not isinstance(ai_preds, list):
                logger.warning(f"Expected list for level {level}, got {type(ai_preds)}")
                ai_preds = []

            threshold = thresholds.get(level, 0.8)

            # Check if ALL predictions are below threshold
            predictions_above_threshold = [
                pred for pred in ai_preds
                if pred.get("confidence", 0.0) >= threshold
            ]

            # Log all predictions
            for pred in ai_preds:
                conf = pred.get("confidence", 0.0)
                label = pred.get("label", "")
                logger.info(f"Level {level}, tag '{label}': confidence={conf:.3f}, threshold={threshold:.3f}")

            # If no predictions meet threshold, this level needs LLM
            if not predictions_above_threshold:
                logger.info(f"Level {level}: ALL {len(ai_preds)} tags below threshold {threshold}")
                levels_below_threshold.append(level)

                if trigger_level is None:
                    trigger_level = level

                # If this level is below threshold, all child levels must use LLM too
                # Add remaining levels in hierarchy
                remaining_levels = hierarchy[hierarchy.index(level)+1:]
                for child_level in remaining_levels:
                    if child_level in predict_levels and child_level not in levels_below_threshold:
                        levels_below_threshold.append(child_level)

                break  # Stop checking once we hit the first below-threshold level
            else:
                logger.info(f"Level {level}: {len(predictions_above_threshold)}/{len(ai_preds)} tags above threshold {threshold}")

        needs_llm = len(levels_below_threshold) > 0

        logger.info(f"Confidence evaluation: needs_llm={needs_llm}, trigger_level={trigger_level}, "
                   f"levels_below_threshold={levels_below_threshold}")

        return needs_llm, trigger_level, levels_below_threshold
    
    @staticmethod
    def determine_llm_levels(trigger_level: str, predict_levels: List[str]) -> List[str]:
        """
        Determine which levels LLM should process based on trigger level
        
        Args:
            trigger_level: The level that triggered LLM call
            predict_levels: All requested prediction levels
            
        Returns:
            List of levels that LLM should process
        """
        hierarchy = ["primary", "secondary", "tertiary"]
        
        if trigger_level not in hierarchy:
            return predict_levels
            
        # LLM processes trigger level and all children
        trigger_index = hierarchy.index(trigger_level)
        llm_levels = []
        
        for i in range(trigger_index, len(hierarchy)):
            level = hierarchy[i]
            if level in predict_levels:
                llm_levels.append(level)
        
        logger.info(f"LLM will process levels: {llm_levels} (triggered by {trigger_level})")
        
        return llm_levels
    
    @staticmethod
    def build_llm_context(ai_predictions: Dict[str, Any],
                         llm_levels: List[str]) -> Dict[str, Any]:
        """
        Build context for LLM service call using AI predictions that are kept

        Args:
            ai_predictions: AI service predictions with multi-label arrays
            llm_levels: Levels that LLM will process

        Returns:
            Context dictionary for LLM service with multi-label support
        """
        context = {}
        hierarchy = ["primary", "secondary", "tertiary"]

        for level in hierarchy:
            if level not in llm_levels:  # Only include levels that LLM is NOT processing
                ai_preds = ai_predictions.get("prediction", {}).get(level, [])
                if isinstance(ai_preds, list) and ai_preds:
                    # Pass all labels as a list for multi-label context
                    labels = [pred.get("label", "") for pred in ai_preds if pred.get("label")]
                    if labels:
                        # If single label, pass as string for compatibility
                        # If multiple labels, pass as list
                        context[level] = labels[0] if len(labels) == 1 else labels

        logger.info(f"Built LLM context: {context}")
        return context