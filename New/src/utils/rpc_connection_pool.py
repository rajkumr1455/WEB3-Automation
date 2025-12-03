"""
RPC Connection Pool with Failover & Health Checks
Addresses finding H3: Missing RPC provider rotation & health checks

Features:
- Multi-provider support (primary + backup RPC URLs)
- Automatic failover on connection errors
- Health check monitoring
- Circuit breaker pattern
- Exponential backoff retry logic
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import httpx
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

logger = logging.getLogger(__name__)


class ProviderStatus(str, Enum):
    """Status of an RPC provider"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class RPCProvider:
    """RPC provider configuration and state"""
    url: str
    priority: int = 0  # Lower = higher priority
    status: ProviderStatus = ProviderStatus.HEALTHY
    failure_count: int = 0
    last_check: Optional[datetime] = None
    circuit_open_until: Optional[datetime] = None
    
    def is_available(self) -> bool:
        """Check if provider is available for use"""
        if self.status == ProviderStatus.CIRCUIT_OPEN:
            if self.circuit_open_until and datetime.now() < self.circuit_open_until:
                return False
            # Circuit breaker timeout expired, try again
            self.status = ProviderStatus.DEGRADED
            return True
        return self.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]


class RPCConnectionPool:
    """
    Manages multiple RPC providers with automatic failover
    
    Usage:
        pool = RPCConnectionPool(
            providers=[
                "https://eth-mainnet.g.alchemy.com/v2/KEY1",
                "https://mainnet.infura.io/v3/KEY2"
            ]
        )
        
        block_number = await pool.get_block_number()
        web3 = pool.get_web3()
    """
    
    def __init__(
        self,
        providers: List[str],
        health_check_interval: int = 60,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 300  # 5 minutes
    ):
        """
        Initialize RPC connection pool
        
        Args:
            providers: List of RPC URLs in priority order
            health_check_interval: Seconds between health checks
            circuit_breaker_threshold: Failures before circuit opens
            circuit_breaker_timeout: Seconds to wait before retrying failed provider
        """
        self.providers = [
            RPCProvider(url=url, priority=i) 
            for i, url in enumerate(providers)
        ]
        self.health_check_interval = health_check_interval
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        
        self._current_provider: Optional[RPCProvider] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        logger.info(f"Initialized RPC pool with {len(providers)} providers")
    
    async def start(self):
        """Start health check background task"""
        if not self._health_check_task:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info("Started RPC health check task")
    
    async def stop(self):
        """Stop health check background task"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Stopped RPC health check task")
    
    async def _health_check_loop(self):
        """Background task to periodically check provider health"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._check_all_providers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _check_all_providers(self):
        """Check health of all providers"""
        for provider in self.providers:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        provider.url,
                        json={
                            "jsonrpc": "2.0",
                            "method": "eth_blockNumber",
                            "params": [],
                            "id": 1
                        }
                    )
                    
                    if response.status_code == 200:
                        provider.status = ProviderStatus.HEALTHY
                        provider.failure_count = 0
                        provider.last_check = datetime.now()
                        logger.debug(f"Provider {provider.url[:30]}... healthy")
                    else:
                        self._handle_provider_failure(provider)
                        
            except Exception as e:
                logger.warning(f"Provider {provider.url[:30]}... failed health check: {e}")
                self._handle_provider_failure(provider)
    
    def _handle_provider_failure(self, provider: RPCProvider):
        """Handle provider failure and circuit breaker logic"""
        provider.failure_count += 1
        provider.last_check = datetime.now()
        
        if provider.failure_count >= self.circuit_breaker_threshold:
            provider.status = ProviderStatus.CIRCUIT_OPEN
            provider.circuit_open_until = datetime.now() + timedelta(seconds=self.circuit_breaker_timeout)
            logger.error(
                f"Circuit breaker OPEN for {provider.url[:30]}... "
                f"(failures: {provider.failure_count})"
            )
        else:
            provider.status = ProviderStatus.DEGRADED
            logger.warning(
                f"Provider {provider.url[:30]}... degraded "
                f"(failures: {provider.failure_count}/{self.circuit_breaker_threshold})"
            )
    
    async def _get_available_provider(self) -> RPCProvider:
        """Get next available provider in priority order"""
        async with self._lock:
            # Try to use current provider if still available
            if self._current_provider and self._current_provider.is_available():
                return self._current_provider
            
            # Find best available provider
            available = [p for p in self.providers if p.is_available()]
            
            if not available:
                # All providers failed - try to reset circuit breakers
                logger.error("All RPC providers unavailable - attempting reset")
                for provider in self.providers:
                    if provider.status == ProviderStatus.CIRCUIT_OPEN:
                        provider.status = ProviderStatus.DEGRADED
                        provider.failure_count = self.circuit_breaker_threshold - 1
                
                available = [p for p in self.providers if p.is_available()]
                
                if not available:
                    raise Exception("All RPC providers failed - cannot continue")
            
            # Sort by priority (lower = better) and status
            available.sort(key=lambda p: (p.priority, p.failure_count))
            self._current_provider = available[0]
            
            logger.info(f"Selected RPC provider: {self._current_provider.url[:50]}...")
            return self._current_provider
    
    def get_web3(self) -> AsyncWeb3:
        """
        Get Web3 instance connected to best available provider
        
        Returns:
            AsyncWeb3 instance
        """
        if not self._current_provider:
            # Synchronously select first provider for initial connection
            self._current_provider = min(self.providers, key=lambda p: p.priority)
        
        provider = AsyncHTTPProvider(self._current_provider.url)
        return AsyncWeb3(provider)
    
    async def execute_with_failover(
        self,
        method: str,
        params: List[Any] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute JSON-RPC method with automatic failover
        
        Args:
            method: RPC method name (e.g., "eth_blockNumber")
            params: Method parameters
            max_retries: Maximum retry attempts across providers
            
        Returns:
            RPC response result
        """
        params = params or []
        last_error = None
        
        for attempt in range(max_retries):
            try:
                provider = await self._get_available_provider()
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        provider.url,
                        json={
                            "jsonrpc": "2.0",
                            "method": method,
                            "params": params,
                            "id": 1
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    if "error" in result:
                        raise Exception(f"RPC error: {result['error']}")
                    
                    # Success - reset failure count
                    provider.failure_count = 0
                    provider.status = ProviderStatus.HEALTHY
                    
                    return result.get("result")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"RPC call failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                if self._current_provider:
                    self._handle_provider_failure(self._current_provider)
                    self._current_provider = None  # Force provider selection on retry
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception(f"RPC call failed after {max_retries} attempts: {last_error}")
    
    async def get_block_number(self) -> int:
        """Get current block number with failover"""
        result = await self.execute_with_failover("eth_blockNumber")
        return int(result, 16)  # Convert hex to int
    
    async def get_balance(self, address: str) -> int:
        """Get account balance with failover"""
        result = await self.execute_with_failover("eth_getBalance", [address, "latest"])
        return int(result, 16)
    
    async def call(self, transaction: Dict[str, Any], block: str = "latest") -> str:
        """Execute eth_call with failover"""
        return await self.execute_with_failover("eth_call", [transaction, block])
    
    def get_status(self) -> Dict[str, Any]:
        """Get pool status and provider health"""
        return {
            "total_providers": len(self.providers),
            "healthy": sum(1 for p in self.providers if p.status == ProviderStatus.HEALTHY),
            "degraded": sum(1 for p in self.providers if p.status == ProviderStatus.DEGRADED),
            "failed": sum(1 for p in self.providers if p.status == ProviderStatus.FAILED),
            "circuit_open": sum(1 for p in self.providers if p.status == ProviderStatus.CIRCUIT_OPEN),
            "current_provider": self._current_provider.url[:50] if self._current_provider else None,
            "providers": [
                {
                    "url": p.url[:50] + "..." if len(p.url) > 50 else p.url,
                    "priority": p.priority,
                    "status": p.status,
                    "failures": p.failure_count,
                    "last_check": p.last_check.isoformat() if p.last_check else None
                }
                for p in self.providers
            ]
        }


# Example usage
if __name__ == "__main__":
    import os
    
    async def main():
        # Create pool with primary and backup providers
        pool = RPCConnectionPool(
            providers=[
                os.getenv("ETHEREUM_RPC_URL", "https://eth-mainnet.g.alchemy.com/v2/demo"),
                os.getenv("ETHEREUM_RPC_URL_BACKUP", "https://ethereum.publicnode.com")
            ]
        )
        
        await pool.start()
        
        try:
            # Get block number with automatic failover
            block = await pool.get_block_number()
            print(f"Current block: {block}")
            
            # Get pool status
            status = pool.get_status()
            print(f"Pool status: {status}")
            
        finally:
            await pool.stop()
    
    asyncio.run(main())
