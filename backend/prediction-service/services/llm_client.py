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

                # Transform the prediction format from arrays to single objects
                if "prediction" in result and isinstance(result["prediction"], dict):
                    prediction = result["prediction"]
                    transformed_prediction = {}

                    for level in ["primary", "secondary", "tertiary"]:
                        level_data = prediction.get(level, [])

                        if isinstance(level_data, list) and level_data:
                            # Take the first (highest confidence) prediction from array
                            best_pred = level_data[0]

                            # Ensure reasoning is a string
                            reasoning = best_pred.get("reasoning", "")
                            if isinstance(reasoning, dict):
                                reasoning = str(reasoning)

                            transformed_prediction[level] = {
                                "pred": best_pred.get("pred", ""),
                                "confidence": best_pred.get("confidence", 0.0),
                                "reasoning": reasoning,
                                "primary": best_pred.get("primary"),
                                "secondary": best_pred.get("secondary")
                            }
                        elif isinstance(level_data, dict):
                            # Already single object format
                            reasoning = level_data.get("reasoning", "")
                            if isinstance(reasoning, dict):
                                reasoning = str(reasoning)

                            transformed_prediction[level] = {
                                "pred": level_data.get("pred", ""),
                                "confidence": level_data.get("confidence", 0.0),
                                "reasoning": reasoning,
                                "primary": level_data.get("primary"),
                                "secondary": level_data.get("secondary")
                            }
                        else:
                            # No prediction for this level
                            transformed_prediction[level] = {
                                "pred": "",
                                "confidence": 0.0,
                                "reasoning": "",
                                "primary": None,
                                "secondary": None
                            }

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