"""
Backend Integration Tests - Remediator PR Generation
Tests automated fix generation and GitHub PR creation
"""
import pytest
import httpx
from test_config import REMEDIATOR_URL as BASE_URL

@pytest.mark.asyncio
@pytest.mark.integration
async def test_remediate_finding():
    """Test remediating a security finding"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        remediation_request = {
            "finding": {
                "id": "rem-test-001",
                "type": "reentrancy",
                "severity": "critical",
                "file_path": "contracts/Vault.sol",
                "line_number": 42,
                "function_name": "withdraw",
                "vulnerable_code": "function withdraw() public { ... }",
                "description": "Reentrancy vulnerability in withdraw"
            },
            "repo_url": "https://github.com/test/sample-repo",
            "branch": "main",
            "create_pr": False  # Don't actually create PR in tests
        }
        
        response = await client.post(
            f"{BASE_URL}/remediate",
            json=remediation_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        assert data["status"] == "queued"

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_remediation_job():
    """Test retrieving remediation job status"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create job
        create_response = await client.post(
            f"{BASE_URL}/remediate",
            json={
                "finding": {
                    "id": "rem-status-test",
                    "type": "access_control",
                    "severity": "high",
                    "file_path": "contracts/Manager.sol",
                    "line_number": 10,
                    "vulnerable_code": "function dangerous() public { ... }",
                    "description": "Missing access control"
                },
                "repo_url": "https://github.com/test/repo",
                "create_pr": False
            }
        )
        
        job_id = create_response.json()["job_id"]
        
        # Get job status
        status_response = await client.get(f"{BASE_URL}/remediate/{job_id}")
        
        assert status_response.status_code == 200
        data = status_response.json()
        
        assert data["job_id"] == job_id
        assert "status" in data

@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_jobs():
    """Test listing all remediation jobs"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/jobs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "jobs" in data
        assert "total" in data
        assert isinstance(data["jobs"], list)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_pr_list():
    """Test listing created PRs"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/prs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "prs" in data
        assert "total" in data

@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint():
    """Test health check"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "remediator"
