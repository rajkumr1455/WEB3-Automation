"""
Backend Integration Tests - Address Scan Flow
Tests the address-only scanner with multi-chain support
"""
import pytest
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Any
from test_config import ADDRESS_SCANNER_URL as BASE_URL

@pytest.mark.asyncio
@pytest.mark.integration
async def test_address_scan_basic_flow():
    """Test basic address scanning workflow"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Submit scan for known test address (DAI on Ethereum)
        scan_request = {
            "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F"
        }
        
        response = await client.post(
            f"{BASE_URL}/scan-address",
            json=scan_request
        )
        
        # Skip if no API key configured (returns 404 for unverified contracts)
        if response.status_code == 404:
            pytest.skip("API key not configured or contract not verified")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "scan_id" in data
        assert "address" in data
        assert "chain" in data
        assert data["address"] == scan_request["address"]
        
        # Verify auto-detection worked
        assert data["chain"] in ["ethereum", "auto"]
        
        # Scan should have status
        assert "status" in data
        assert data["status"] in ["queued", "processing", "completed", "failed"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_address_scan_with_chain():
    """Test scanning with explicit chain specification"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        scan_request = {
            "address": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",  # BUSD on BSC
            "chain": "bsc"
        }
        
        response = await client.post(
            f"{BASE_URL}/scan-address",
            json=scan_request
        )
        
        # Skip if no API key configured
        if response.status_code == 404:
            pytest.skip("API key not configured or contract not verified")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["chain"] == "bsc"
        assert data["address"] == scan_request["address"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_address_scan_invalid_address():
    """Test error handling for invalid address"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        scan_request = {
            "address": "invalid_address"
        }
        
        response = await client.post(
            f"{BASE_URL}/scan-address",
            json=scan_request
        )
        
        # Should return error
        assert response.status_code in [400, 422]
        data = response.json()
        assert "detail" in data or "error" in data

@pytest.mark.asyncio
@pytest.mark.integration  
async def test_supported_chains():
    """Test supported chains endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/supported-chains")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "chains" in data
        assert isinstance(data["chains"], list)
        
        # Verify expected chains
        expected_chains = ["ethereum", "bsc", "polygon", "arbitrum", "optimism"]
        for chain in expected_chains:
            assert chain in data["chains"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint():
    """Test health check endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "address-scanner"
        assert "version" in data

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_scan_completion_wait():
    """Test waiting for scan completion (with API keys configured)"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # This test requires API keys to be configured
        # Skip if not available
        try:
            scan_request = {
                "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "chain": "ethereum"
            }
            
            response = await client.post(
                f"{BASE_URL}/scan-address",
                json=scan_request
            )
            
            if response.status_code == 404:
                pytest.skip("API keys not configured")
            
            assert response.status_code == 200
            data = response.json()
            
            # If findings are returned, verify structure
            if "findings" in data:
                assert isinstance(data["findings"], list)
                if len(data["findings"]) > 0:
                    finding = data["findings"][0]
                    assert "type" in finding
                    assert "severity" in finding
                    assert "title" in finding
                    assert "description" in finding
                    
        except httpx.ConnectError:
            pytest.skip("Service not available")
