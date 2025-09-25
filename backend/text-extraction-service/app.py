"""
Text Extraction Service - Microservice for extracting text from PDF documents
"""
import logging
import tempfile
import os
from typing import Optional, Dict, Any

import fitz  # PyMuPDF
import httpx
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest, InternalServerError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class TextExtractionService:
    """Service for extracting text from PDF documents"""
    
    def __init__(self):
        self.http_client = httpx.Client()
        logger.info("Text extraction service initialized")
    
    def extract_text_from_url(self, pdf_url: str) -> str:
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
        temp_file_path = None
        try:
            # Create temporary file for PDF processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file.flush()
                temp_file_path = temp_file.name
                
                # Open PDF with PyMuPDF
                doc = fitz.open(temp_file_path)
                
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
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {temp_file_path}: {e}")

# Initialize service
text_service = TextExtractionService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "text-extraction"}), 200

@app.route('/extract-text', methods=['POST'])
def extract_text():
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
        # Parse request
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        
        data = request.get_json()
        pdf_url = data.get('pdf_url')
        
        if not pdf_url:
            raise BadRequest("pdf_url is required")
        
        # Extract text
        extracted_text = text_service.extract_text_from_url(pdf_url)
        
        return jsonify({
            "success": True,
            "text": extracted_text,
            "character_count": len(extracted_text)
        }), 200
        
    except BadRequest as e:
        logger.warning(f"Bad request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Text extraction failed: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5008))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Text Extraction Service on {host}:{port}")
    app.run(host=host, port=port, debug=debug)