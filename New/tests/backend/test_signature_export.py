"""
Backend Integration Tests - Signature Export
Tests signature generation and export in multiple formats
"""
import pytest
import httpx
from test_config import SIGNATURE_URL as BASE_URL

@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_signatures():
    """Test generating signatures from a finding"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        request = {
            "finding": {
                "id": "sig-test-001",
                "type": "reentrancy",
                "severity": "critical",
                "title": "Reentrancy in withdraw",
                "description": "Test reentrancy",
                "patterns": ["external_call", "state_change"],
                "bytecode_patterns": ["CALL", "SSTORE"]
            },
            "formats": ["yara", "sigma", "custom"]
        }
        
        response = await client.post(
            f"{BASE_URL}/generate",
            json=request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 3  # yara, sigma, custom
        
        # Verify each signature has required fields
        for sig in data:
            assert "signature_id" in sig
            assert "format" in sig
            assert "content" in sig
            assert sig["format"] in ["yara", "sigma", "custom"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_all_signatures():
    """Test retrieving all generated signatures"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/signatures")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "signatures" in data
        assert "total" in data
        assert "by_format" in data

@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_signatures():
    """Test exporting signatures in bulk"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Generate some signatures first
        await client.post(
            f"{BASE_URL}/generate",
            json={
                "finding": {
                    "id": "export-test",
                    "type": "access_control",
                    "severity": "high",
                    "title": "Test export",
                    "description": "Testing export functionality",
                    "patterns": ["missing_modifier"]
                }
            }
        )
        
        # Export
        response = await client.post(
            f"{BASE_URL}/export",
            params={"format": "yara"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "format" in data
        assert "count" in data
        assert "content" in data
        assert data["format"] == "yara"

@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint():
    """Test health check"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
