"""
Unit tests for GET /health endpoint
"""
import pytest


class TestHealth:
    """Tests for health check endpoint"""

    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert 'status' in data
        assert data['status'] == 'healthy'
        assert 'database' in data
        assert data['database'] == 'connected'
        assert 'timestamp' in data

    def test_health_check_response_format(self, client):
        """Test health check response format"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields
        assert isinstance(data, dict)
        assert isinstance(data['status'], str)
        assert isinstance(data['database'], str)
        assert isinstance(data['timestamp'], str)

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert 'service' in data
        assert data['service'] == 'Retraining Service'
        assert 'status' in data
        assert data['status'] == 'healthy'
        assert 'version' in data
        assert 'description' in data
