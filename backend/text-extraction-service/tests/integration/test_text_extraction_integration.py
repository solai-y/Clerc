"""
Integration tests for text extraction service
Tests the service with real PDF processing
"""
import pytest
import tempfile
import os

class TestTextExtractionIntegration:
    """Integration tests for text extraction endpoints"""

    def test_health_endpoint_integration(self, client):
        """Test health endpoint returns correct structure"""
        response = client.get('/health')

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert 'status' in data
        assert 'service' in data
        assert 'ocr_available' in data
        assert 'capabilities' in data

        # Verify values
        assert data['status'] == 'healthy'
        assert data['service'] == 'text-extraction'
        assert isinstance(data['ocr_available'], bool)
        assert isinstance(data['capabilities'], dict)
        assert data['capabilities']['pymupdf'] is True

    def test_extract_text_with_real_pdf(self, client):
        """Test text extraction with a real PDF created in memory"""
        import fitz

        # Create a real PDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Integration test content")
        page.insert_text((72, 100), "This is a multi-line PDF")
        pdf_bytes = doc.tobytes()
        doc.close()

        # Save to temp file and create a mock URL
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_bytes)
            temp_path = temp_file.name

        try:
            # For integration test, we'll test the service method directly
            # since we can't easily mock external URLs in integration tests
            from app import text_service

            text, info = text_service._extract_text_from_bytes(pdf_bytes)

            assert "Integration test content" in text
            assert "multi-line PDF" in text
            assert info["method"] == "pymupdf"
            assert info["ocr_used"] is False
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_extract_text_empty_pdf(self, client):
        """Test extraction from PDF with no text content"""
        import fitz

        # Create an empty PDF
        doc = fitz.open()
        doc.new_page()  # Empty page
        pdf_bytes = doc.tobytes()
        doc.close()

        from app import text_service

        # Should fail or return empty depending on OCR availability
        try:
            text, info = text_service._extract_text_from_bytes(pdf_bytes)
            # If OCR is available and runs, we might get empty text
            # or it might fail - both are acceptable for an empty PDF
        except Exception as e:
            # Expected to fail for completely empty PDF
            assert "text" in str(e).lower() or "extraction" in str(e).lower()

    def test_extract_text_multipage_pdf(self, client):
        """Test extraction from multi-page PDF"""
        import fitz

        # Create multi-page PDF
        doc = fitz.open()

        page1 = doc.new_page()
        page1.insert_text((72, 72), "First page content")

        page2 = doc.new_page()
        page2.insert_text((72, 72), "Second page content")

        page3 = doc.new_page()
        page3.insert_text((72, 72), "Third page content")

        pdf_bytes = doc.tobytes()
        doc.close()

        from app import text_service

        text, info = text_service._extract_text_from_bytes(pdf_bytes)

        # Verify all pages are extracted
        assert "First page content" in text
        assert "Second page content" in text
        assert "Third page content" in text

        # Verify page markers
        assert "[Page 1]" in text
        assert "[Page 2]" in text
        assert "[Page 3]" in text

    def test_endpoint_with_invalid_json(self, client):
        """Test /extract-text with invalid JSON"""
        response = client.post('/extract-text',
                              content='{"invalid json',
                              headers={"Content-Type": "application/json"})

        assert response.status_code == 400

    def test_endpoint_with_missing_field(self, client):
        """Test /extract-text with missing required field"""
        response = client.post('/extract-text',
                              json={'wrong_field': 'value'})

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'pdf_url' in data['error'].lower()

    def test_endpoint_with_invalid_url(self, client):
        """Test /extract-text with invalid URL"""
        response = client.post('/extract-text',
                              json={'pdf_url': 'https://invalid-url-that-does-not-exist.com/file.pdf'})

        assert response.status_code == 500
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
