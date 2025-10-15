"""
Client for communicating with AI service
"""
import asyncio
import httpx
import logging
import time
from typing import Dict, Any, List
from config import Config

logger = logging.getLogger(__name__)

class AIServiceClient:
    """Client for AI service communication"""
    
    def __init__(self):
        self.base_url = Config.AI_SERVICE_URL
        self.timeout = Config.AI_SERVICE_TIMEOUT
        logger.info(f"Initialized AI service client with URL: {self.base_url}")
    
    async def _ensure_service_ready(self) -> bool:
        """Ensure AI service is ready before making prediction requests"""
        max_checks = 5
        check_delay = 0.5
        
        for attempt in range(max_checks):
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"{self.base_url}/e2e")
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("model_status") == "ok" and not result.get("rebuilding", True):
                            logger.info(f"AI service ready after {attempt + 1} checks")
                            return True
                logger.warning(f"AI service not ready (attempt {attempt + 1}/{max_checks})")
                await asyncio.sleep(check_delay)
            except Exception as e:
                logger.warning(f"AI service readiness check failed (attempt {attempt + 1}/{max_checks}): {str(e)}")
                await asyncio.sleep(check_delay)
        
        logger.error("AI service failed readiness checks")
        return False

    async def predict(self, text: str, predict_levels: List[str]) -> Dict[str, Any]:
        """
        Call AI service prediction endpoint
        
        Args:
            text: Document text to classify
            predict_levels: Levels to predict (primary, secondary, tertiary)
            
        Returns:
            AI service response
            
        Raises:
            Exception: If AI service call fails
        """
        start_time = time.time()
        
        # Ensure AI service is ready before making requests
        if not await self._ensure_service_ready():
            raise Exception("AI service is not ready")
        
        try:
            # Retry logic for connection errors
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        logger.info(f"Calling AI service at {self.base_url}/predict (attempt {attempt + 1}/{max_retries})")
                        
                        response = await client.post(
                            f"{self.base_url}/predict",
                            json={"text": text, "predict_levels": predict_levels},
                            headers={"Content-Type": "application/json"}
                        )
                        
                        response.raise_for_status()
                        result = response.json()
                        
                        # If we get here, the request succeeded, break out of retry loop
                        break
                        
                except httpx.ConnectError as e:
                    duration = time.time() - start_time
                    logger.warning(f"AI service connection error on attempt {attempt + 1}/{max_retries} after {duration:.2f}s: {str(e)}")
                    
                    if attempt == max_retries - 1:  # Last attempt
                        logger.error(f"AI service connection failed after {max_retries} attempts")
                        raise Exception(f"AI service connection error: {str(e)}")
                    
                    # Wait before retry
                    await asyncio.sleep(retry_delay)
                    continue
                    
                except Exception as e:
                    duration = time.time() - start_time
                    logger.warning(f"AI service error on attempt {attempt + 1}/{max_retries} after {duration:.2f}s: {str(e)} (type: {type(e)})")
                    
                    # For non-connection errors, don't retry by default, but let specific errors retry
                    if "All connection attempts failed" in str(e) or "connection" in str(e).lower():
                        if attempt == max_retries - 1:  # Last attempt
                            logger.error(f"AI service connection failed after {max_retries} attempts")
                            raise Exception(f"AI service connection error: {str(e)}")
                        # Wait before retry
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        # For other errors, don't retry
                        raise e
            
            duration = time.time() - start_time
            logger.info(f"AI service call completed in {duration:.2f}s")
            
            # Transform result to expected format and add duration
            if "elapsed_seconds" in result:
                result["duration"] = result.pop("elapsed_seconds")
            else:
                result["duration"] = duration
            
            # Transform the prediction format to ensure arrays
            if "prediction" in result and isinstance(result["prediction"], dict):
                prediction = result["prediction"]
                # Ensure all levels are in array format for multi-label support
                transformed_prediction = {}
                for level in ["primary", "secondary", "tertiary"]:
                    level_data = prediction.get(level, [])

                    if isinstance(level_data, list):
                        # Already array format - keep it as arrays
                        # Just ensure key_evidence is properly formatted
                        formatted_predictions = []
                        for pred in level_data:
                            # Convert key_evidence to string if it's a dict
                            key_evidence = pred.get("key_evidence", "")
                            if isinstance(key_evidence, dict):
                                key_evidence = str(key_evidence)

                            formatted_predictions.append({
                                "label": pred.get("label", ""),
                                "confidence": pred.get("confidence", 0.0),
                                "key_evidence": key_evidence
                            })
                        transformed_prediction[level] = formatted_predictions
                    elif isinstance(level_data, dict):
                        # Single object format - convert to array with one element
                        reasoning = level_data.get("reasoning", "")
                        if isinstance(reasoning, dict):
                            reasoning = str(reasoning)

                        transformed_prediction[level] = [{
                            "label": level_data.get("pred", ""),
                            "confidence": level_data.get("confidence", 0.0),
                            "key_evidence": reasoning
                        }]
                    else:
                        # No prediction for this level
                        transformed_prediction[level] = []
                result["prediction"] = transformed_prediction
            
            return result
            
        except httpx.TimeoutException:
            duration = time.time() - start_time
            logger.error(f"AI service timeout after {duration:.2f}s")
            raise Exception(f"AI service timeout after {self.timeout}s")
        
        except httpx.HTTPStatusError as e:
            duration = time.time() - start_time
            logger.error(f"AI service HTTP error {e.response.status_code} after {duration:.2f}s")
            raise Exception(f"AI service error: {e.response.status_code} - {e.response.text}")
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"AI service error after {duration:.2f}s: {str(e)} (type: {type(e)})")
            raise Exception(f"AI service error: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check AI service health
        
        Returns:
            Health status of AI service
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/e2e")
                response.raise_for_status()
                return {
                    "status": "healthy",
                    "response": response.json()
                }
        except Exception as e:
            logger.error(f"AI service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }