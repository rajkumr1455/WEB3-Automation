import asyncio
import os
import logging
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import async_geth_poa_middleware
import httpx

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentCore")

# Configuration
RPC_URL = os.getenv("RPC_URL", "http://localhost:8545")

class AgentCore:
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        self.http_client = None
        self.w3 = None

    async def initialize(self):
        """
        Initialize the AsyncWeb3 provider with a persistent httpx client for connection pooling.
        """
        logger.info("Initializing Agent Core...")
        
        # Create a persistent AsyncClient
        self.http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            timeout=30.0
        )
        
        # Initialize AsyncWeb3 with AsyncHTTPProvider using the custom client logic?
        # Web3.py's AsyncHTTPProvider doesn't directly accept an httpx client instance in older versions,
        # but we can configure the request_kwargs or subclass it if needed.
        # However, for simple connection pooling, AsyncHTTPProvider usually manages its own session if not provided.
        # In web3.py v6+, it uses aiohttp by default. 
        # The prompt explicitly asked to "Replace all instances of requests.get with httpx.AsyncClient".
        # If we are using AsyncWeb3, it handles RPC calls. 
        # But if we have custom logic (like fetching source code from Etherscan), we should use self.http_client.
        
        # For the RPC provider itself:
        self.w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc_url))
        
        # Middleware for PoA chains (like BSC, Polygon, or local devnets)
        self.w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
        
        if await self.w3.is_connected():
            logger.info(f"Connected to RPC: {self.rpc_url}")
            chain_id = await self.w3.eth.chain_id
            logger.info(f"Chain ID: {chain_id}")
        else:
            logger.error("Failed to connect to RPC")
            raise ConnectionError("Could not connect to RPC")

    async def fetch_url(self, url: str, params: dict = None) -> dict:
        """
        Fetch data from a URL using the persistent httpx client.
        """
        if not self.http_client:
            raise RuntimeError("AgentCore not initialized")
            
        try:
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"An error occurred while requesting {e.request.url!r}.")
            return {}
        except httpx.HTTPStatusError as e:
            logger.error(f"Error response {e.response.status_code} while requesting {e.request.url!r}.")
            return {}

    async def run_loop(self):
        """
        Main event loop.
        """
        logger.info("Starting Event Loop...")
        try:
            while True:
                # Placeholder for block monitoring logic
                # In a real agent, we would listen for events here.
                # For now, we just sleep to simulate activity.
                block_number = await self.w3.eth.block_number
                logger.debug(f"Current Block: {block_number}")
                
                await asyncio.sleep(12) # Avg block time
        except asyncio.CancelledError:
            logger.info("Event loop cancelled")
        except Exception as e:
            logger.error(f"Error in event loop: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """
        Cleanup resources.
        """
        logger.info("Shutting down...")
        if self.http_client:
            await self.http_client.aclose()

if __name__ == "__main__":
    agent = AgentCore(RPC_URL)
    try:
        asyncio.run(agent.initialize())
        asyncio.run(agent.run_loop())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Fatal error: {e}")
