"""
Text Extraction Service - Microservice for extracting text from PDF documents
"""
import logging
import tempfile
import os
from typing import Optional, Dict, Any, Tuple

import fitz  # PyMuPDF
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OCR dependencies
try:
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image
    OCR_AVAILABLE = True
    logger.info("OCR dependencies loaded successfully")
except ImportError as e:
    OCR_AVAILABLE = False
    logger.warning(f"OCR dependencies not available: {e}. OCR fallback will be disabled.")

app = FastAPI()

# Pydantic models
class ExtractTextRequest(BaseModel):
    pdf_url: str

class TextExtractionService:
    """Service for extracting text from PDF documents"""

    def __init__(self):
        self.http_client = httpx.Client()
        logger.info("Text extraction service initialized")

    def extract_text_from_url(self, pdf_url: str) -> Tuple[str, Dict[str, Any]]:
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
            response = self.http_client.get(pdf_url, timeout=30.0)
            response.raise_for_status()
            pdf_bytes = response.content

            logger.info(f"Downloaded PDF ({len(pdf_bytes)} bytes), extracting text...")

            # Extract text from PDF bytes
            text, extraction_info = self._extract_text_from_bytes(pdf_bytes)

            logger.info(f"Extracted {len(text)} characters from PDF")
            return text, extraction_info

        except Exception as e:
            logger.error(f"Failed to extract text from PDF URL {pdf_url}: {str(e)}")
            raise Exception(f"PDF text extraction failed: {str(e)}")

    def _extract_text_from_bytes(self, pdf_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF bytes using PyMuPDF with OCR fallback

        Args:
            pdf_bytes: PDF file as bytes

        Returns:
            Extracted text content
        """
        temp_file_path = None
        try:
            # Create temporary file for PDF processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file.flush()
                temp_file_path = temp_file.name

                # Try PyMuPDF first (faster for text-based PDFs)
                try:
                    full_text = self._extract_with_pymupdf(temp_file_path)
                    if full_text.strip():
                        logger.info("Successfully extracted text using PyMuPDF")
                        return full_text.strip(), {"method": "pymupdf", "ocr_used": False}
                except Exception as e:
                    logger.warning(f"PyMuPDF extraction failed: {str(e)}")

                # Fallback to OCR if PyMuPDF fails or returns empty text
                if OCR_AVAILABLE:
                    logger.info("Attempting OCR fallback for text extraction")
                    try:
                        full_text = self._extract_with_ocr(pdf_bytes)
                        if full_text.strip():
                            logger.info("Successfully extracted text using OCR")
                            return full_text.strip(), {"method": "ocr", "ocr_used": True}
                    except Exception as e:
                        logger.error(f"OCR extraction failed: {str(e)}")

                # If both methods fail
                raise Exception("No text content found in PDF. Both PyMuPDF and OCR extraction failed.")

        except Exception as e:
            logger.error(f"Failed to extract text from PDF bytes: {str(e)}")
            raise Exception(f"PDF text extraction failed: {str(e)}")
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {temp_file_path}: {e}")

    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """
        Extract text using PyMuPDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content
        """
        doc = fitz.open(pdf_path)
        text_parts = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            if page_text.strip():  # Only add non-empty pages
                text_parts.append(f"[Page {page_num + 1}]\n{page_text.strip()}")

        doc.close()
        return "\n\n".join(text_parts)

    def _extract_with_ocr(self, pdf_bytes: bytes) -> str:
        """
        Extract text using OCR (pdf2image + tesseract)

        Args:
            pdf_bytes: PDF file as bytes

        Returns:
            Extracted text content
        """
        if not OCR_AVAILABLE:
            raise Exception("OCR dependencies not available")

        # Convert PDF to images
        try:
            images = convert_from_bytes(pdf_bytes)
        except Exception as e:
            raise Exception(f"Failed to convert PDF to images: {str(e)}")

        if not images:
            raise Exception("No images could be extracted from PDF")

        text_parts = []
        for page_num, image in enumerate(images, 1):
            try:
                # Use Tesseract to extract text from image
                page_text = pytesseract.image_to_string(image, lang='eng')
                if page_text.strip():
                    text_parts.append(f"[Page {page_num}]\n{page_text.strip()}")
                else:
                    logger.warning(f"No text found on page {page_num} using OCR")
            except Exception as e:
                logger.warning(f"OCR failed for page {page_num}: {str(e)}")
                continue

        if not text_parts:
            raise Exception("No text could be extracted using OCR")

        return "\n\n".join(text_parts)

# Initialize service
text_service = TextExtractionService()

@app.get('/health')
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "text-extraction",
        "ocr_available": OCR_AVAILABLE,
        "capabilities": {
            "pymupdf": True,
            "ocr_fallback": OCR_AVAILABLE
        }
    }

@app.post('/extract-text')
async def extract_text(request: ExtractTextRequest):
    """
    Extract text from PDF

    Request body:
    {
        "pdf_url": "https://example.com/document.pdf"
    }

    Response:
    {
        "success": true,
        "text": "Extracted text content...",
        "character_count": 1234
    }
    """
    try:
        # Extract text
        extracted_text, extraction_info = text_service.extract_text_from_url(request.pdf_url)

        return {
            "success": True,
            "text": extracted_text,
            "character_count": len(extracted_text),
            "extraction_method": extraction_info["method"],
            "ocr_used": extraction_info["ocr_used"]
        }

    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Text extraction failed: {str(e)}"
            }
        )

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = exc.errors()
    if errors:
        error = errors[0]
        field = error.get('loc', [''])[-1] if error.get('loc') else 'field'
        error_type = error.get('type', '')
        
        if error_type == 'missing':
            message = f"Missing required field: {field}"
        elif error_type == 'string_type':
            message = f"{field} must be a string"
        elif error_type == 'list_type':
            message = f"{field} must be an array"
        else:
            error_msg = error.get('msg', '').lower()
            if 'list' in error_msg or 'array' in error_msg:
                message = f"{field} must be an array"
            else:
                message = "Validation failed"
    else:
        message = "Validation failed"
    
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": message
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint not found"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error"
        }
    )

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 5008))
    host = os.environ.get('HOST', '0.0.0.0')

    logger.info(f"Starting Text Extraction Service on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
