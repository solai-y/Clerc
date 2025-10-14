"""
Unit tests for text extraction service API endpoints
"""
import pytest
from unittest.mock import patch, Mock

class TestHealthEndpoint:
    """Tests for /health endpoint"""

    def test_health_check_success(self, client):
        """Test health check returns 200"""
        response = client.get('/health')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'text-extraction'
        assert 'ocr_available' in data
        assert 'capabilities' in data
        assert 'pymupdf' in data['capabilities']
        assert 'ocr_fallback' in data['capabilities']


class TestExtractTextEndpoint:
    """Tests for /extract-text endpoint"""

    def test_extract_text_missing_json(self, client):
        """Test extract-text with non-JSON request"""
        response = client.post('/extract-text', data='not json')

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'error' in data

    def test_extract_text_missing_pdf_url(self, client):
        """Test extract-text without pdf_url parameter"""
        response = client.post('/extract-text', json={})

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'pdf_url' in data['error'].lower()

    @patch('app.text_service.extract_text_from_url')
    def test_extract_text_success(self, mock_extract, client):
        """Test successful text extraction"""
        mock_extract.return_value = (
            "Extracted text content",
            {"method": "pymupdf", "ocr_used": False}
        )

        response = client.post('/extract-text',
                              json={'pdf_url': 'https://example.com/test.pdf'})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['text'] == "Extracted text content"
        assert data['character_count'] == len("Extracted text content")
        assert data['extraction_method'] == "pymupdf"
        assert data['ocr_used'] is False

    @patch('app.text_service.extract_text_from_url')
    def test_extract_text_service_error(self, mock_extract, client):
        """Test extract-text when service raises exception"""
        mock_extract.side_effect = Exception("PDF processing failed")

        response = client.post('/extract-text',
                              json={'pdf_url': 'https://example.com/test.pdf'})

        assert response.status_code == 500
        data = response.json()
        assert data['success'] is False
        assert 'Text extraction failed' in data['error']

    @patch('app.text_service.extract_text_from_url')
    def test_extract_text_with_ocr(self, mock_extract, client):
        """Test text extraction that uses OCR"""
        mock_extract.return_value = (
            "OCR extracted text",
            {"method": "ocr", "ocr_used": True}
        )

        response = client.post('/extract-text',
                              json={'pdf_url': 'https://example.com/test.pdf'})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['text'] == "OCR extracted text"
        assert data['extraction_method'] == "ocr"
        assert data['ocr_used'] is True


class TestErrorHandlers:
    """Tests for error handlers"""

    def test_404_handler(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent-endpoint')

        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert 'not found' in data['error'].lower()
