"""
Main prediction service that orchestrates classification
"""
import time
import logging
from typing import Dict, List, Any
from claude_client import ClaudeClient
from prompt_generator import PromptGenerator
from hierarchy_validator import HierarchyValidator
from models import PredictionLevel, KeyEvidence

logger = logging.getLogger(__name__)

class PredictionService:
    """Main service for handling document classification predictions"""
    
    def __init__(self):
        self.claude_client = ClaudeClient()
        self.prompt_generator = PromptGenerator()
        self.validator = HierarchyValidator()
        logger.info("Prediction service initialized")
    
    def predict(self, text: str, predict_levels: List[str], context: Dict[str, str]) -> Dict[str, Any]:
        """
        Main prediction method
        
        Args:
            text: Preprocessed document content
            predict_levels: List of levels to predict (primary, secondary, tertiary)
            context: Already predicted levels for context
            
        Returns:
            Prediction response matching AI service format
        """
        start_time = time.time()
        
        try:
            # Generate appropriate prompt based on context
            prompt = self.prompt_generator.generate_prompt(text, predict_levels, context)
            
            # Log the prompt being sent to Claude (for debugging)
            logger.info("=== PROMPT SENT TO CLAUDE ===")
            logger.info(prompt)
            logger.info("=== END PROMPT ===")
            
            # Get classification from Claude with retries
            claude_result = self.claude_client.classify_with_retry(prompt)
            
            # Process and validate the result
            processed_result = self._process_claude_result(
                claude_result, predict_levels, context, text
            )
            
            elapsed_time = time.time() - start_time
            
            return {
                "elapsed_seconds": elapsed_time,
                "prediction": processed_result,
                "processed_text": text
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise
    
    def _process_claude_result(self, claude_result: Dict[str, Any], 
                              predict_levels: List[str], context: Dict[str, str],
                              text: str) -> Dict[str, Any]:
        """
        Process Claude's result and format it according to AI service format
        
        Args:
            claude_result: Raw result from Claude
            predict_levels: Levels that were requested
            context: Context provided in request
            text: Original document text
            
        Returns:
            Formatted prediction response
        """
        result = {}
        
        # Extract predictions from Claude result
        predictions = self._extract_predictions(claude_result, predict_levels, context)
        
        # Validate and fix predictions
        validated_predictions = self.validator.validate_and_fix_prediction(predictions)
        
        # Generate response for each level
        if "primary" in predict_levels and "primary" in validated_predictions:
            result["primary"] = self._create_prediction_level(
                validated_predictions["primary"],
                claude_result.get("confidence_primary", 0.85),
                text,
                level="primary",
                reasoning=claude_result.get("reasoning")
            )
        
        if "secondary" in predict_levels and "secondary" in validated_predictions:
            result["secondary"] = self._create_prediction_level(
                validated_predictions["secondary"],
                claude_result.get("confidence_secondary", 0.80),
                text,
                level="secondary",
                primary=validated_predictions.get("primary") or context.get("primary"),
                reasoning=claude_result.get("reasoning")
            )
        
        if "tertiary" in predict_levels and "tertiary" in validated_predictions:
            result["tertiary"] = self._create_prediction_level(
                validated_predictions["tertiary"],
                claude_result.get("confidence_tertiary", 0.75),
                text,
                level="tertiary",
                primary=validated_predictions.get("primary") or context.get("primary"),
                secondary=validated_predictions.get("secondary") or context.get("secondary"),
                reasoning=claude_result.get("reasoning")
            )
        
        return result
    
    def _extract_predictions(self, claude_result: Dict[str, Any], 
                            predict_levels: List[str], context: Dict[str, str]) -> Dict[str, str]:
        """Extract predictions from Claude result"""
        predictions = {}
        
        # Add context to predictions
        predictions.update(context)
        
        # Extract from Claude result
        if "primary" in predict_levels and "primary" in claude_result:
            predictions["primary"] = claude_result["primary"]
        
        if "secondary" in predict_levels and "secondary" in claude_result:
            predictions["secondary"] = claude_result["secondary"]
        
        if "tertiary" in predict_levels and "tertiary" in claude_result:
            predictions["tertiary"] = claude_result["tertiary"]
        
        return predictions
    
    def _create_prediction_level(self, prediction: str, confidence: float, text: str,
                               level: str, primary: str = None, secondary: str = None, 
                               reasoning: str = None) -> Dict[str, Any]:
        """
        Create a prediction level response in AI service format
        
        Args:
            prediction: The predicted tag
            confidence: Confidence score
            text: Original document text  
            level: Current level (primary, secondary, tertiary)
            primary: Primary context (for secondary/tertiary)
            secondary: Secondary context (for tertiary)
            reasoning: Claude's reasoning for the classification
            
        Returns:
            Formatted prediction level
        """
        result = {
            "pred": prediction,
            "confidence": confidence,
            "reasoning": reasoning or "No reasoning provided"
        }
        
        # Add context references
        if level in ["secondary", "tertiary"] and primary:
            result["primary"] = primary
        
        if level == "tertiary" and secondary:
            result["secondary"] = secondary
        
        return result