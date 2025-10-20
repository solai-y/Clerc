"""
Client for communicating with LLM service
"""
import httpx
import logging
import time
from typing import Dict, Any, List
from config import Config

logger = logging.getLogger(__name__)

class LLMServiceClient:
    """Client for LLM service communication"""
    
    def __init__(self):
        self.base_url = Config.LLM_SERVICE_URL
        self.timeout = Config.LLM_SERVICE_TIMEOUT
        logger.info(f"Initialized LLM service client with URL: {self.base_url}")
    
    async def predict(self, text: str, predict_levels: List[str], context: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Call LLM service prediction endpoint
        
        Args:
            text: Document text to classify
            predict_levels: Levels to predict (primary, secondary, tertiary)
            context: Context with already predicted levels from AI service
            
        Returns:
            LLM service response
            
        Raises:
            Exception: If LLM service call fails
        """
        start_time = time.time()
        
        try:
            request_data = {
                "text": text,
                "predict": predict_levels,
                "context": context or {}
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Calling LLM service at {self.base_url}/predict for levels: {predict_levels}")
                logger.info(f"Context provided: {context}")
                
                response = await client.post(
                    f"{self.base_url}/predict",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                result = response.json()
                
                duration = time.time() - start_time
                logger.info(f"LLM service call completed in {duration:.2f}s")

                # Add duration to result
                if "elapsed_seconds" in result:
                    result["duration"] = result.pop("elapsed_seconds")
                else:
                    result["duration"] = duration

                # Keep prediction format as arrays for multi-tag support
                if "prediction" in result and isinstance(result["prediction"], dict):
                    prediction = result["prediction"]
                    transformed_prediction = {}

                    for level in ["primary", "secondary", "tertiary"]:
                        level_data = prediction.get(level, [])

                        if isinstance(level_data, list) and level_data:
                            # Keep all predictions as array (multi-tag support)
                            transformed_list = []
                            for pred in level_data:
                                # Ensure reasoning is a string
                                reasoning = pred.get("reasoning", "")
                                if isinstance(reasoning, dict):
                                    reasoning = str(reasoning)

                                transformed_list.append({
                                    "pred": pred.get("pred", ""),
                                    "confidence": pred.get("confidence", 0.0),
                                    "reasoning": reasoning,
                                    "primary": pred.get("primary"),
                                    "secondary": pred.get("secondary")
                                })

                            transformed_prediction[level] = transformed_list
                        elif isinstance(level_data, dict):
                            # Single object format - wrap in array for consistency
                            reasoning = level_data.get("reasoning", "")
                            if isinstance(reasoning, dict):
                                reasoning = str(reasoning)

                            transformed_prediction[level] = [{
                                "pred": level_data.get("pred", ""),
                                "confidence": level_data.get("confidence", 0.0),
                                "reasoning": reasoning,
                                "primary": level_data.get("primary"),
                                "secondary": level_data.get("secondary")
                            }]
                        else:
                            # No prediction for this level - empty array
                            transformed_prediction[level] = []

                    result["prediction"] = transformed_prediction

                return result
                
        except httpx.TimeoutException:
            duration = time.time() - start_time
            logger.error(f"LLM service timeout after {duration:.2f}s")
            raise Exception(f"LLM service timeout after {self.timeout}s")
        
        except httpx.HTTPStatusError as e:
            duration = time.time() - start_time
            logger.error(f"LLM service HTTP error {e.response.status_code} after {duration:.2f}s")
            error_text = ""
            try:
                error_text = e.response.text
            except:
                pass
            raise Exception(f"LLM service error: {e.response.status_code} - {error_text}")
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"LLM service error after {duration:.2f}s: {str(e)}")
            raise Exception(f"LLM service error: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check LLM service health
        
        Returns:
            Health status of LLM service
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return {
                    "status": "healthy",
                    "response": response.json()
                }
        except Exception as e:
            logger.error(f"LLM service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }