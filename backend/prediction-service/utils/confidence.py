"""
Confidence evaluation logic for hierarchical predictions
"""
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class ConfidenceEvaluator:
    """Evaluates confidence thresholds and determines LLM triggering"""
    
    @staticmethod
    def evaluate_thresholds(ai_predictions: Dict[str, Any], 
                          thresholds: Dict[str, float], 
                          predict_levels: List[str]) -> Tuple[bool, str, List[str]]:
        """
        Evaluate AI predictions against confidence thresholds
        
        Args:
            ai_predictions: AI service predictions
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
                
            # Get AI prediction for this level
            ai_pred = ai_predictions.get("prediction", {}).get(level, {})
            if not ai_pred:
                logger.warning(f"No AI prediction found for level: {level}")
                continue
                
            confidence = ai_pred.get("confidence", 0.0)
            threshold = thresholds.get(level, 0.8)
            
            logger.info(f"Level {level}: confidence={confidence:.3f}, threshold={threshold:.3f}")
            
            if confidence < threshold:
                # This level is below threshold
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
                         llm_levels: List[str]) -> Dict[str, str]:
        """
        Build context for LLM service call using AI predictions that are kept
        
        Args:
            ai_predictions: AI service predictions
            llm_levels: Levels that LLM will process
            
        Returns:
            Context dictionary for LLM service
        """
        context = {}
        hierarchy = ["primary", "secondary", "tertiary"]
        
        for level in hierarchy:
            if level not in llm_levels:  # Only include levels that LLM is NOT processing
                ai_pred = ai_predictions.get("prediction", {}).get(level, {})
                if ai_pred and ai_pred.get("pred"):
                    context[level] = ai_pred["pred"]
        
        logger.info(f"Built LLM context: {context}")
        return context