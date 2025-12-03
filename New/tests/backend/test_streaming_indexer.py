"""
Backend Integration Tests - Streaming Indexer
Tests real-time event indexing and WebSocket streaming
"""
import pytest
import httpx
from test_config import INDEXER_URL as BASE_URL

@pytest.mark.asyncio
@pytest.mark.integration
async def test_start_indexing():
    """Test starting contract indexing"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        request = {
            "contract_address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "chain": "ethereum",
            "backfill": False
        }
        
        response = await client.post(
            f"{BASE_URL}/index/start",
            json=request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["indexing_started", "already_indexing"]
        assert data["contract"] == request["contract_address"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_indexing_status():
    """Test getting indexing status"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/index/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "indexed_contracts" in data
        assert "total" in data
        assert "total_events" in data

@pytest.mark.asyncio
@pytest.mark.integration
async def test_query_events():
    """Test querying indexed events"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Start indexing first
        await client.post(
            f"{BASE_URL}/index/start",
            json={
                "contract_address": "0xtest123456789",
                "chain": "ethereum"
            }
        )
        
        # Query events
        response = await client.post(
            f"{BASE_URL}/query",
            json={
                "limit": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "events" in data
        assert "total" in data
        assert isinstance(data["events"], list)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_stats():
    """Test getting indexer statistics"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_events" in data
        assert "indexed_contracts" in data
        assert "active_websockets" in data

@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint():
    """Test health check"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
