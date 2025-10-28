"""
Unit tests for text extraction service functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from app import TextExtractionService

class TestTextExtractionService:
    """Unit tests for TextExtractionService class"""

    @pytest.fixture
    def service(self):
        """Create a TextExtractionService instance"""
        return TextExtractionService()

    def test_service_initialization(self, service):
        """Test that service initializes correctly"""
        assert service is not None
        assert service.http_client is not None

    def test_extract_with_pymupdf_success(self, service):
        """Test successful text extraction with PyMuPDF"""
        # Create a simple PDF for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Create a minimal PDF using fitz
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 72), "Test content for unit testing")
            doc.save(temp_path)
            doc.close()

            # Extract text
            result = service._extract_with_pymupdf(temp_path)

            assert "Test content for unit testing" in result
            assert "[Page 1]" in result
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_extract_with_pymupdf_multiple_pages(self, service):
        """Test PyMuPDF extraction with multiple pages"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            import fitz
            doc = fitz.open()

            # Create multiple pages
            page1 = doc.new_page()
            page1.insert_text((72, 72), "Page 1 content")

            page2 = doc.new_page()
            page2.insert_text((72, 72), "Page 2 content")

            doc.save(temp_path)
            doc.close()

            result = service._extract_with_pymupdf(temp_path)

            assert "[Page 1]" in result
            assert "[Page 2]" in result
            assert "Page 1 content" in result
            assert "Page 2 content" in result
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('app.OCR_AVAILABLE', True)
    @patch('app.convert_from_bytes')
    @patch('app.pytesseract.image_to_string')
    def test_extract_with_ocr_success(self, mock_tesseract, mock_convert, service):
        """Test successful OCR extraction"""
        # Mock image conversion
        mock_image = Mock()
        mock_convert.return_value = [mock_image]

        # Mock OCR result
        mock_tesseract.return_value = "OCR extracted text"

        pdf_bytes = b"fake pdf content"
        result = service._extract_with_ocr(pdf_bytes)

        assert "OCR extracted text" in result
        assert "[Page 1]" in result
        mock_convert.assert_called_once_with(pdf_bytes)
        mock_tesseract.assert_called_once()

    @patch('app.OCR_AVAILABLE', False)
    def test_extract_with_ocr_not_available(self, service):
        """Test OCR extraction when OCR is not available"""
        pdf_bytes = b"fake pdf content"

        with pytest.raises(Exception, match="OCR dependencies not available"):
            service._extract_with_ocr(pdf_bytes)

    @patch('app.OCR_AVAILABLE', True)
    @patch('app.convert_from_bytes')
    def test_extract_with_ocr_no_images(self, mock_convert, service):
        """Test OCR extraction when no images can be extracted"""
        mock_convert.return_value = []

        pdf_bytes = b"fake pdf content"

        with pytest.raises(Exception, match="No images could be extracted from PDF"):
            service._extract_with_ocr(pdf_bytes)

    @patch('httpx.Client.get')
    def test_extract_text_from_url_success(self, mock_get, service):
        """Test successful text extraction from URL"""
        # Create a simple PDF
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "URL PDF content")
        pdf_bytes = doc.tobytes()
        doc.close()

        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = pdf_bytes
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://example.com/test.pdf"
        text, info = service.extract_text_from_url(url)

        assert "URL PDF content" in text
        assert info["method"] == "pymupdf"
        assert info["ocr_used"] is False
        mock_get.assert_called_once()

    @patch('httpx.Client.get')
    def test_extract_text_from_url_http_error(self, mock_get, service):
        """Test text extraction when HTTP request fails"""
        mock_get.side_effect = Exception("Network error")

        url = "https://example.com/test.pdf"

        with pytest.raises(Exception, match="PDF text extraction failed"):
            service.extract_text_from_url(url)

    def test_extract_from_bytes_cleanup_temp_file(self, service):
        """Test that temporary files are cleaned up after extraction"""
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Cleanup test")
        pdf_bytes = doc.tobytes()
        doc.close()

        # Get list of temp files before
        temp_dir = tempfile.gettempdir()
        temp_files_before = set(os.listdir(temp_dir))

        # Extract text
        text, info = service._extract_text_from_bytes(pdf_bytes)

        # Check temp files after
        temp_files_after = set(os.listdir(temp_dir))

        # Verify text was extracted
        assert "Cleanup test" in text

        # Verify no new temp files remain
        # Allow for a small window of temp files that might be created by system
        new_temp_files = temp_files_after - temp_files_before
        pdf_temp_files = [f for f in new_temp_files if f.endswith('.pdf')]
        assert len(pdf_temp_files) == 0
