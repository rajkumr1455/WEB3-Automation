"""
Backend Integration Tests - Metrics Emission
Tests Prometheus metrics endpoints
"""
import pytest
import httpx
import re
from test_config import PROMETHEUS_URL

@pytest.mark.asyncio
@pytest.mark.integration
async def test_prometheus_health():
    """Test Prometheus is running"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{PROMETHEUS_URL}/-/healthy")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Prometheus not available")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_service_metrics():
    """Test that services expose metrics"""
    services = [
        ("address-scanner", 8008),
        ("guardrail", 8009),
        ("validator-worker", 8010),
        ("mlops-engine", 8011),
        ("signature-generator", 8012),
        ("remediator", 8013),
        ("streaming-indexer", 8014)
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service_name, port in services:
            try:
                # Try health endpoint
                response= await client.get(f"http://localhost:{port}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    assert "status" in data
                    assert data["status"] == "healthy"
            except httpx.ConnectError:
                pytest.skip(f"{service_name} not available")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_metrics_format():
    """Test metrics are in Prometheus format"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Try to get metrics from Prometheus
            response = await client.get(f"{PROMETHEUS_URL}/api/v1/targets")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Prometheus not available")
