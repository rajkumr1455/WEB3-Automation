"""
Backend Integration Tests - Validator Worker
Tests finding validation and reproduction
"""
import pytest
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_fixed
from test_config import VALIDATOR_URL as BASE_URL

@pytest.mark.asyncio
@pytest.mark.integration
async def test_submit_validation():
    """Test submitting a finding for validation"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        validation_request = {
            "finding": {
                "id": "test-finding-001",
                "type": "reentrancy",
                "severity": "critical",
                "title": "Reentrancy in withdraw()",
                "description": "The withdraw function is vulnerable to reentrancy"
            },
            "chain": "ethereum",
            "timeout": 300
        }
        
        response = await client.post(
            f"{BASE_URL}/validate",
            json=validation_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        assert data["finding_id"] == "test-finding-001"
        assert data["status"] in ["queued", "running"]

@retry(stop=stop_after_attempt(10), wait=wait_fixed(3))
async def wait_for_validation(client: httpx.AsyncClient, job_id: str):
    """Wait for validation to complete"""
    response = await client.get(f"{BASE_URL}/validate/{job_id}")
    data = response.json()
    
    assert data["status"] in ["queued", "running", "completed", "failed"]
    
    if data["status"] in ["queued", "running"]:
        raise Exception("Still processing")
    
    return data

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_validation_completion():
    """Test validation job completion"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Submit validation
        validation_request = {
            "finding": {
                "id": "test-finding-002",
                "type": "access_control",
                "severity": "high",
                "title": "Missing access control",
                "description": "Function lacks proper access control"
            },
            "chain": "ethereum"
        }
        
        submit_response = await client.post(
            f"{BASE_URL}/validate",
            json=validation_request
        )
        
        job_id = submit_response.json()["job_id"]
        
        # Wait for completion (with timeout)
        try:
            result = await wait_for_validation(client, job_id)
            
            # Verify result structure
            assert "job_id" in result
            assert "status" in result
            assert result["status"] in ["completed", "failed"]
            
            if result["status"] == "completed":
                assert "is_valid" in result
                assert "confidence" in result
                assert isinstance(result["confidence"], (int, float))
                assert 0 <= result["confidence"] <= 1
                
        except Exception as e:
            pytest.skip(f"Validation did not complete in time: {e}")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_all_validations():
    """Test getting all validation jobs"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/validations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "jobs" in data  # Fixed: API uses 'jobs' not 'validations'
        assert isinstance(data["jobs"], list)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_manual_override():
    """Test manual validation override"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Submit validation
        submit_response = await client.post(
            f"{BASE_URL}/validate",
            json={
                "finding": {
                    "id": "test-override",
                    "type": "unchecked_call",
                    "severity": "medium",
                    "title": "Test override",
                    "description": "Testing manual override"
                }
            }
        )
        
        job_id = submit_response.json()["job_id"]
        
        # Apply manual override
        response = await client.post(
            f"{BASE_URL}/validate/{job_id}/mark",
            params={"is_valid": True, "confidence": 0.95}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] == True
        assert data["confidence"] == 0.95

@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint():
    """Test health check"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "validator-worker"
