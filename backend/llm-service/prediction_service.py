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
        Process Claude's result and format it according to AI service format (multi-label support)

        Args:
            claude_result: Raw result from Claude (now with arrays per level)
            predict_levels: Levels that were requested
            context: Context provided in request
            text: Original document text

        Returns:
            Formatted prediction response with arrays
        """
        result = {}

        # Extract predictions from Claude result (now expects arrays)
        predictions = self._extract_predictions(claude_result, predict_levels, context)

        # Process each level - return single best prediction per level (not arrays)
        # Only add levels that were actually requested and have valid predictions
        if "primary" in predict_levels and "primary" in predictions:
            primary_list = self._create_prediction_levels(
                predictions["primary"],
                level="primary",
                context=context
            )
            # Only add to result if we got a valid prediction
            if primary_list:
                result["primary"] = primary_list[0]

        if "secondary" in predict_levels and "secondary" in predictions:
            secondary_list = self._create_prediction_levels(
                predictions["secondary"],
                level="secondary",
                context={
                    **context,
                    "primary": result.get("primary", {}).get("pred") if result.get("primary") else context.get("primary")
                }
            )
            # Only add to result if we got a valid prediction
            if secondary_list:
                result["secondary"] = secondary_list[0]

        if "tertiary" in predict_levels and "tertiary" in predictions:
            tertiary_list = self._create_prediction_levels(
                predictions["tertiary"],
                level="tertiary",
                context={
                    **context,
                    "primary": result.get("primary", {}).get("pred") if result.get("primary") else context.get("primary"),
                    "secondary": result.get("secondary", {}).get("pred") if result.get("secondary") else context.get("secondary")
                }
            )
            # Only add to result if we got a valid prediction
            if tertiary_list:
                result["tertiary"] = tertiary_list[0]

        return result
    
    def _extract_predictions(self, claude_result: Dict[str, Any],
                            predict_levels: List[str], context: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract predictions from Claude result and convert to list of dicts format

        Claude can return two formats:
        1. Array format (new): {"primary": [{"tag": "News", "confidence": 0.9, "reasoning": "..."}]}
        2. Flat format (legacy): {"primary": "News", "confidence_primary": 0.9, "reasoning": "..."}

        We normalize both to the array format.
        """
        predictions = {}

        # Add context to predictions (keep as-is for string context)
        for key, value in context.items():
            if isinstance(value, str):
                predictions[key] = value

        # Extract from Claude result and convert to expected format
        for level in ["primary", "secondary", "tertiary"]:
            if level not in predict_levels or level not in claude_result:
                continue

            level_data = claude_result[level]

            # If already in array format, use as-is
            if isinstance(level_data, list):
                predictions[level] = level_data
            # If in flat format, convert to array
            elif isinstance(level_data, str):
                # Legacy flat format: {"primary": "News", "confidence_primary": 0.9}
                tag = level_data
                confidence = claude_result.get(f"confidence_{level}", 0.0)
                reasoning = claude_result.get("reasoning", "No reasoning provided")

                predictions[level] = [{
                    "tag": tag,
                    "confidence": confidence,
                    "reasoning": reasoning
                }]
            # If it's a dict, convert to array with single item
            elif isinstance(level_data, dict):
                predictions[level] = [level_data]

        return predictions
    
    def _create_prediction_levels(self, predictions: List[Dict[str, Any]],
                                 level: str, context: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Create prediction level responses in AI service format (multi-label support)

        Args:
            predictions: List of predictions from Claude (each with tag, confidence, reasoning)
            level: Current level (primary, secondary, tertiary)
            context: Context dictionary with primary/secondary values

        Returns:
            List of formatted prediction levels matching AI service format
        """
        if not predictions or not isinstance(predictions, list):
            logger.warning(f"No predictions or invalid format for level {level}")
            return []

        formatted_predictions = []

        for pred_data in predictions:
            # Extract fields from Claude's response
            tag = pred_data.get("tag", "")
            confidence = pred_data.get("confidence", 0.0)
            reasoning = pred_data.get("reasoning", "No reasoning provided")

            # Validate the tag exists in hierarchy
            if not self._validate_tag(tag, level, context):
                logger.warning(f"Invalid tag '{tag}' for level {level}, skipping")
                continue

            # Create formatted prediction
            result = {
                "pred": tag,
                "confidence": confidence,
                "reasoning": reasoning
            }

            # Add context references for secondary/tertiary
            if level in ["secondary", "tertiary"] and context.get("primary"):
                result["primary"] = context.get("primary")

            if level == "tertiary" and context.get("secondary"):
                result["secondary"] = context.get("secondary")

            formatted_predictions.append(result)

        return formatted_predictions

    def _validate_tag(self, tag: str, level: str, context: Dict[str, str]) -> bool:
        """
        Validate that a tag is valid for the given level and context

        Args:
            tag: The tag to validate
            level: The level (primary, secondary, tertiary)
            context: Context with primary/secondary values

        Returns:
            True if valid, False otherwise
        """
        if level == "primary":
            return self.validator.is_valid_primary(tag)
        elif level == "secondary":
            primary = context.get("primary")
            if not primary:
                return False
            return self.validator.is_valid_secondary(primary, tag)
        elif level == "tertiary":
            primary = context.get("primary")
            secondary = context.get("secondary")
            if not primary or not secondary:
                return False
            return self.validator.is_valid_tertiary(primary, secondary, tag)

        return False