"""
End-to-end tests for text extraction service
Tests the service running as a full application
"""
import pytest
import requests
import time

# Service URL - adjust based on your deployment
SERVICE_URL = "http://localhost:5008"

class TestTextExtractionE2E:
    """E2E tests for text extraction service"""

    @pytest.fixture(autouse=True)
    def wait_for_service(self):
        """Wait for service to be available before running tests"""
        max_retries = 30
        retry_delay = 1

        for i in range(max_retries):
            try:
                response = requests.get(f"{SERVICE_URL}/health", timeout=2)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                if i < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    pytest.skip("Text extraction service not available")

    def test_health_endpoint_e2e(self):
        """Test health endpoint in deployed service"""
        response = requests.get(f"{SERVICE_URL}/health")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'healthy'
        assert data['service'] == 'text-extraction'
        assert 'ocr_available' in data
        assert 'capabilities' in data

    def test_extract_text_endpoint_missing_json_e2e(self):
        """Test extract-text with non-JSON content"""
        response = requests.post(
            f"{SERVICE_URL}/extract-text",
            data="not json",
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False

    def test_extract_text_missing_pdf_url_e2e(self):
        """Test extract-text without pdf_url field"""
        response = requests.post(
            f"{SERVICE_URL}/extract-text",
            json={}
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'pdf_url' in data['error'].lower()

    def test_extract_text_invalid_url_e2e(self):
        """Test extract-text with invalid URL"""
        response = requests.post(
            f"{SERVICE_URL}/extract-text",
            json={"pdf_url": "https://invalid-domain-123456789.com/test.pdf"}
        )

        assert response.status_code == 500
        data = response.json()
        assert data['success'] is False
        assert 'error' in data

    def test_404_endpoint_e2e(self):
        """Test that non-existent endpoints return 404"""
        response = requests.get(f"{SERVICE_URL}/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert 'not found' in data['error'].lower()

    def test_service_accepts_json_content_type_e2e(self):
        """Test that service properly handles JSON content type"""
        response = requests.post(
            f"{SERVICE_URL}/extract-text",
            json={"pdf_url": "https://example.com/test.pdf"},
            headers={"Content-Type": "application/json"}
        )

        # Should process the request (may fail at URL fetch, but not at parsing)
        assert response.status_code in [200, 500]  # Either success or server error, not 400
        data = response.json()
        assert 'success' in data
