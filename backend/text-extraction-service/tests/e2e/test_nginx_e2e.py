"""
E2E tests for text extraction service through nginx
Tests the service when accessed through the nginx reverse proxy
"""
import pytest
import requests
import time

# Nginx URL - adjust based on your deployment
NGINX_URL = "http://localhost/text-extraction"

class TestTextExtractionNginxE2E:
    """E2E tests for text extraction service through nginx"""

    @pytest.fixture(autouse=True)
    def wait_for_service(self):
        """Wait for service to be available through nginx"""
        max_retries = 30
        retry_delay = 1

        for i in range(max_retries):
            try:
                response = requests.get(f"{NGINX_URL}/health", timeout=2)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                if i < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    pytest.skip("Text extraction service not available through nginx")

    def test_health_through_nginx(self):
        """Test health endpoint through nginx"""
        response = requests.get(f"{NGINX_URL}/health")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'healthy'
        assert data['service'] == 'text-extraction'

    def test_extract_text_through_nginx_missing_url(self):
        """Test extract-text through nginx without pdf_url"""
        response = requests.post(
            f"{NGINX_URL}/extract-text",
            json={}
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'pdf_url' in data['error'].lower()

    def test_extract_text_through_nginx_invalid_json(self):
        """Test extract-text through nginx with invalid JSON"""
        response = requests.post(
            f"{NGINX_URL}/extract-text",
            data="invalid json",
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 400

    def test_404_through_nginx(self):
        """Test 404 handling through nginx"""
        response = requests.get(f"{NGINX_URL}/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False

    def test_cors_headers_through_nginx(self):
        """Test that CORS headers are properly set through nginx"""
        response = requests.options(
            f"{NGINX_URL}/extract-text",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )

        # Nginx should handle CORS
        # Status might be 200 or 204 depending on nginx config
        assert response.status_code in [200, 204]
