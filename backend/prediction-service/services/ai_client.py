"""
Client for communicating with AI service
"""
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
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Calling AI service at {self.base_url}/predict")
                
                response = await client.post(
                    f"{self.base_url}/predict",
                    json={"text": text, "predict_levels": predict_levels},
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                result = response.json()
                
                duration = time.time() - start_time
                logger.info(f"AI service call completed in {duration:.2f}s")
                
                # Add duration to result
                result["duration"] = duration
                
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
            logger.error(f"AI service error after {duration:.2f}s: {str(e)}")
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