"""
Monitoring Agent with RPC Connection Pool Integration
Updated to use RPC pool for automatic failover and health monitoring
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import httpx
import os
import logging
import asyncio
from web3 import Web3
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.utils.rpc_connection_pool import RPCConnectionPool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Monitoring Agent", version="2.0.0")
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# LLM Router URL
LLM_ROUTER_URL = os.getenv("LLM_ROUTER_URL", "http://llm-router:8000")

# RPC Connection Pools (with failover)
RPC_POOLS = {}

def initialize_rpc_pools():
    """Initialize RPC connection pools for all chains with failover"""
    chains_config = {
        "ethereum": [
            os.getenv("ETHEREUM_RPC_URL", os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com")),
            os.getenv("ETHEREUM_RPC_URL_BACKUP", "https://ethereum.publicnode.com")
        ],
        "bsc": [
            os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/"),
            os.getenv("BSC_RPC_URL_BACKUP", "https://rpc.ankr.com/bsc")
        ],
        "polygon": [
            os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com/"),
            os.getenv("POLYGON_RPC_URL_BACKUP", "https://polygon-mainnet.public.blastapi.io")
        ],
        "arbitrum": [
            os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
            os.getenv("ARBITRUM_RPC_URL_BACKUP", "https://rpc.ankr.com/arbitrum")
        ],
        "optimism": [
            os.getenv("OPTIMISM_RPC_URL", "https://mainnet.optimism.io"),
            os.getenv("OPTIMISM_RPC_URL_BACKUP", "https://rpc.ankr.com/optimism")
        ],
        "base": [
            os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
            os.getenv("BASE_RPC_URL_BACKUP", "https://base.publicnode.com")
        ]
    }
    
    for chain, providers in chains_config.items():
        # Filter out empty providers
        providers = [p for p in providers if p]
        if providers:
            RPC_POOLS[chain] = RPCConnectionPool(
                providers=providers,
                health_check_interval=60,
                circuit_breaker_threshold=5,
                circuit_breaker_timeout=300
            )
            logger.info(f"Initialized RPC pool for {chain} with {len(providers)} providers")


class MonitorRequest(BaseModel):
    """Request for dynamic monitoring"""
    scan_id: str
    contract_address: str
    chain: str = "ethereum"
    duration_minutes: int = 5


class MonitorResult(BaseModel):
    """Monitoring results"""
    scan_id: str
    contract_address: str
    mempool_anomalies: List[Dict[str, Any]] = []
    oracle_deviations: List[Dict[str, Any]] = []
    rpc_drift: List[Dict[str, Any]] = []
    suspicious_transactions: List[Dict[str, Any]] = []
    total_anomalies: int = 0
    rpc_pool_status: Optional[Dict[str, Any]] = None


async def monitor_mempool(pool: RPCConnectionPool, contract_address: str, duration_seconds: int) -> List[Dict[str, Any]]:
    """Monitor mempool for suspicious transactions"""
    anomalies = []
    
    try:
        logger.info(f"Monitoring mempool for {duration_seconds}s")
        
        # Get Web3 instance from pool
        w3 = pool.get_web3()
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < duration_seconds:
            try:
                # Get pending transactions (limited support on public RPCs)
                pending_block = w3.eth.get_block('pending', full_transactions=True)
                
                for tx in pending_block.transactions[:10]:  # Limit check
                    if tx.to and tx.to.lower() == contract_address.lower():
                        # Check for suspicious patterns
                        if tx.value > w3.to_wei(10, 'ether'):  # Large value transfer
                            anomalies.append({
                                "type": "large_value_transfer",
                                "tx_hash": tx.hash.hex(),
                                "value": str(tx.value),
                                "from": tx['from'],
                                "timestamp": datetime.now().isoformat()
                            })
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.debug(f"Mempool check iteration failed (will retry): {e}")
                await asyncio.sleep(5)
                continue
        
    except Exception as e:
        logger.error(f"Mempool monitoring failed: {e}")
    
    return anomalies


async def check_oracle_deviation(pool: RPCConnectionPool, contract_address: str) -> List[Dict[str, Any]]:
    """Check for oracle price deviations"""
    deviations = []
    
    try:
        logger.info("Checking oracle deviations")
        
        # Get current block number using pool (demonstrates failover)
        block_number = await pool.get_block_number()
        logger.info(f"Current block: {block_number}")
        
        # Placeholder for oracle deviation detection
        # Would need to identify oracle functions and compare prices
        
    except Exception as e:
        logger.error(f"Oracle check failed: {e}")
    
    return deviations


async def detect_rpc_drift(pool: RPCConnectionPool, chain: str) -> List[Dict[str, Any]]:
    """Detect RPC endpoint drift using connection pool status"""
    drift_issues = []
    
    try:
        logger.info(f"Checking RPC drift for {chain}")
        
        # Get pool status
        status = pool.get_status()
        
        # Check if any providers are circuit-open or failed
        if status['circuit_open'] > 0:
            drift_issues.append({
                "type": "circuit_breaker_triggered",
                "chain": chain,
                "providers_affected": status['circuit_open'],
                "details": "Some RPC providers have circuit breakers open"
            })
        
        if status['failed'] > 0:
            drift_issues.append({
                "type": "rpc_failures",
                "chain": chain,
                "providers_failed": status['failed'],
                "details": "Some RPC providers are unavailable"
            })
        
        # Check connectivity
        try:
            block = await pool.get_block_number()
            logger.info(f"RPC pool operational, current block: {block}")
        except Exception as e:
            drift_issues.append({
                "type": "connectivity_error",
                "chain": chain,
                "error": str(e)
            })
        
    except Exception as e:
        logger.error(f"RPC drift detection failed: {e}")
        drift_issues.append({
            "type": "drift_check_error",
            "chain": chain,
            "error": str(e)
        })
    
    return drift_issues


@app.on_event("startup")
async def startup_event():
    """Initialize RPC pools and start health checks"""
    logger.info("Initializing RPC connection pools...")
    initialize_rpc_pools()
    
    # Start health check tasks for all pools
    for chain, pool in RPC_POOLS.items():
        await pool.start()
        logger.info(f"Started health monitoring for {chain}")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop RPC pool health checks"""
    logger.info("Stopping RPC pool health checks...")
    for chain, pool in RPC_POOLS.items():
        await pool.stop()
        logger.info(f"Stopped monitoring for {chain}")


@app.post("/monitor", response_model=MonitorResult)
async def monitor(request: MonitorRequest):
    """Perform dynamic monitoring with RPC failover"""
    logger.info(f"Starting monitoring for scan: {request.scan_id}")
    
    result = MonitorResult(
        scan_id=request.scan_id,
        contract_address=request.contract_address
    )
    
    try:
        # Get RPC pool for chain
        pool = RPC_POOLS.get(request.chain)
        if not pool:
            raise HTTPException(status_code=400, detail=f"Unsupported chain: {request.chain}")
        
        # Check pool status
        pool_status = pool.get_status()
        result.rpc_pool_status = pool_status
        
        if pool_status['healthy'] == 0:
            raise HTTPException(
                status_code=503,
                detail=f"No healthy RPC providers available for {request.chain}"
            )
        
        # Convert duration to seconds
        duration_seconds = min(request.duration_minutes * 60, 300)  # Max 5 minutes
        
        # Run monitoring tasks
        logger.info(f"Monitoring for {duration_seconds}s using RPC pool with {pool_status['healthy']} healthy providers")
        
        # Mempool monitoring
        result.mempool_anomalies = await monitor_mempool(
            pool,
            request.contract_address,
            duration_seconds
        )
        
        # Oracle deviation check
        result.oracle_deviations = await check_oracle_deviation(
            pool,
            request.contract_address
        )
        
        # RPC drift detection
        result.rpc_drift = await detect_rpc_drift(pool, request.chain)
        
        # Calculate total anomalies
        result.total_anomalies = (
            len(result.mempool_anomalies) +
            len(result.oracle_deviations) +
            len(result.rpc_drift)
        )
        
        logger.info(
            f"Monitoring complete: {result.total_anomalies} anomalies detected "
            f"(RPC pool: {pool_status['healthy']}/{pool_status['total_providers']} healthy)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return result


@app.get("/rpc-status")
async def get_rpc_status():
    """Get status of all RPC connection pools"""
    status = {}
    for chain, pool in RPC_POOLS.items():
        status[chain] = pool.get_status()
    return status


@app.get("/health")
async def health():
    """Health check with RPC pool status"""
    rpc_health = {}
    for chain, pool in RPC_POOLS.items():
        pool_status = pool.get_status()
        rpc_health[chain] = {
            "healthy": pool_status['healthy'] > 0,
            "providers": f"{pool_status['healthy']}/{pool_status['total_providers']}"
        }
    
    all_healthy = all(status["healthy"] for status in rpc_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "monitoring-agent",
        "version": "2.0.0",
        "rpc_pools": rpc_health
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
