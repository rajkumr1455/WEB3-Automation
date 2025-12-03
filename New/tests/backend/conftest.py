"""
Pytest fixtures and configuration for backend tests
"""
import pytest
import httpx
import asyncio
from typing import AsyncGenerator

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide HTTP client for tests"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

@pytest.fixture
def sample_finding():
    """Provide sample finding for tests"""
    return {
        "id": "test-finding-sample",
        "type": "reentrancy",
        "severity": "critical",
        "title": "Sample reentrancy vulnerability",
        "description": "Test reentrancy for validation",
        "file_path": "contracts/Vulnerable.sol",
        "line_number": 42,
        "vulnerable_code": "function withdraw() public { ... }"
    }

@pytest.fixture
def sample_contract_address():
    """Provide sample contract address"""
    return "0x6B175474E89094C44Da98b954EedeAC495271d0F"  # DAI contract

@pytest.fixture
def test_repo_url():
    """Provide test repository URL"""
    return "https://github.com/test/sample-repo"

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Add cleanup logic here if needed
    await asyncio.sleep(0.1)  # Small delay to allow async cleanup
