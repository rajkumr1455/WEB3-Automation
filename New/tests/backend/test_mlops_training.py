"""
Backend Integration Tests - ML-Ops Engine
Tests continuous learning and rule generation
"""
import pytest
import httpx
from test_config import MLOPS_URL as BASE_URL

@pytest.mark.asyncio
@pytest.mark.integration
async def test_ingest_finding():
    """Test ingesting a validated finding"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        finding = {
            "finding_id": "ml-test-001",
            "type": "reentrancy",
            "severity": "critical",
            "is_valid": True,
            "confidence": 0.9,
            "source_code": "function withdraw() { ... }",
            "patterns": ["external_call", "state_change_after"]
        }
        
        response = await client.post(
            f"{BASE_URL}/ingest",
            json=finding
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ingested"
        assert "patterns_extracted" in data

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_metrics():
    """Test retrieving ML-Ops metrics"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_findings" in data
        assert "validated_findings" in data
        assert "accuracy" in data
        assert isinstance(data["accuracy"], (int, float))

@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_rules():
    """Test generating detection rules"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First ingest some findings
        for i in range(3):
            await client.post(
                f"{BASE_URL}/ingest",
                json={
                    "finding_id": f"rule-test-{i}",
                    "type": "access_control",
                    "severity": "high",
                    "is_valid": True,
                    "confidence": 0.85,
                    "patterns": ["missing_modifier", "public_function"]
                }
            )
        
        # Generate rules
        response = await client.post(
            f"{BASE_URL}/generate-rules",
            json={
                "min_confidence": 0.7,
                "min_samples": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "count" in data
        assert "rules" in data
        assert isinstance(data["rules"], list)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint():
    """Test health check"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
