"""
Tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app

# Test client for FastAPI
client = TestClient(app)


class TestAPIEndpoints:
    """Test FastAPI endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_health_check_response_format(self):
        """Test health check response format"""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "ok"
        assert len(data) == 1  # Only status field
    
    def test_health_check_methods(self):
        """Test health check endpoint with different HTTP methods"""
        # GET should work
        response = client.get("/health")
        assert response.status_code == 200
        
        # POST should not work (if not implemented)
        response = client.post("/health")
        assert response.status_code in [405, 404]  # Method not allowed or not found
    
    def test_root_endpoint(self):
        """Test root endpoint if it exists"""
        response = client.get("/")
        # This might return 404 if no root endpoint is defined
        # or 200 if there's a root endpoint
        assert response.status_code in [200, 404]
    
    def test_nonexistent_endpoint(self):
        """Test that nonexistent endpoints return 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
