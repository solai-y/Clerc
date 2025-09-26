"""
PDF text extraction service for prediction service
"""
import logging
import tempfile
import fitz  # PyMuPDF
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

class TextExtractionService:
    """Service for extracting text from PDF documents"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient()
        logger.info("Text extraction service initialized")
    
    async def extract_text_from_url(self, pdf_url: str) -> str:
        """
        Extract text from PDF at given URL
        
        Args:
            pdf_url: URL to PDF file (e.g., S3 URL)
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If PDF processing fails
        """
        try:
            logger.info(f"Downloading PDF from URL: {pdf_url}")
            
            # Download PDF from URL
            response = await self.http_client.get(pdf_url)
            response.raise_for_status()
            pdf_bytes = response.content
            
            logger.info(f"Downloaded PDF ({len(pdf_bytes)} bytes), extracting text...")
            
            # Extract text using PyMuPDF
            text = self._extract_text_from_bytes(pdf_bytes)
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF URL {pdf_url}: {str(e)}")
            raise Exception(f"PDF text extraction failed: {str(e)}")
    
    def _extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF bytes using PyMuPDF
        
        Args:
            pdf_bytes: PDF file as bytes
            
        Returns:
            Extracted text content
        """
        try:
            # Create temporary file for PDF processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file.flush()
                
                # Open PDF with PyMuPDF
                doc = fitz.open(temp_file.name)
                
                # Extract text from all pages
                text_parts = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    if page_text.strip():  # Only add non-empty pages
                        text_parts.append(f"[Page {page_num + 1}]\n{page_text.strip()}")
                
                doc.close()
                
                # Combine all pages
                full_text = "\n\n".join(text_parts)
                
                if not full_text.strip():
                    raise Exception("No text content found in PDF (may be image-based or encrypted)")
                
                return full_text.strip()
                
        except Exception as e:
            logger.error(f"Failed to extract text from PDF bytes: {str(e)}")
            raise Exception(f"PDF text extraction failed: {str(e)}")
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()