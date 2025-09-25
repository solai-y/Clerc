"""
Text Extraction Service Client for prediction service
"""
import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class TextExtractionClient:
    """Client for communicating with text extraction service"""
    
    def __init__(self, base_url: str = "http://text-extraction-service:5008"):
        self.base_url = base_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"Text extraction client initialized with base URL: {base_url}")
    
    async def extract_text_from_url(self, pdf_url: str) -> str:
        """
        Extract text from PDF at given URL using text extraction service
        
        Args:
            pdf_url: URL to PDF file (e.g., S3 URL)
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If text extraction fails
        """
        try:
            logger.info(f"Requesting text extraction from: {pdf_url}")
            
            # Call text extraction service
            response = await self.http_client.post(
                f"{self.base_url}/extract-text",
                json={"pdf_url": pdf_url}
            )
            response.raise_for_status()
            
            data = response.json()
            if not data.get("success"):
                raise Exception(data.get("error", "Text extraction failed"))
            
            extracted_text = data.get("text", "")
            character_count = data.get("character_count", len(extracted_text))
            
            logger.info(f"Successfully extracted {character_count} characters from PDF")
            return extracted_text
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} from text extraction service"
            try:
                error_detail = e.response.json().get("error", "Unknown error")
                error_msg += f": {error_detail}"
            except:
                pass
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except httpx.RequestError as e:
            error_msg = f"Network error connecting to text extraction service: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise Exception(f"Text extraction failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of text extraction service
        
        Returns:
            Health status information
        """
        try:
            response = await self.http_client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Text extraction service health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()