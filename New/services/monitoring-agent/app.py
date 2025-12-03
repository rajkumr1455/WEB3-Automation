"""
Dynamic Monitoring Agent
Mempool monitoring, oracle deviation, RPC drift detection
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Monitoring Agent", version="1.0.0")
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

# RPC endpoints
RPC_URLS = {
    "ethereum": os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com"),
    "bsc": os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/"),
    "polygon": os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com/"),
    "arbitrum": os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
}


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


async def monitor_mempool(w3: Web3, contract_address: str, duration_seconds: int) -> List[Dict[str, Any]]:
    """Monitor mempool for suspicious transactions"""
    anomalies = []
    
    try:
        logger.info(f"Monitoring mempool for {duration_seconds}s")
        
        # Subscribe to pending transactions (if supported)
        # Note: This is simplified - real implementation would use WebSocket
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
                logger.debug(f"Mempool check iteration failed: {e}")
                await asyncio.sleep(5)
                continue
        
    except Exception as e:
        logger.error(f"Mempool monitoring failed: {e}")
    
    return anomalies


async def check_oracle_deviation(w3: Web3, contract_address: str) -> List[Dict[str, Any]]:
    """Check for oracle price deviations"""
    deviations = []
    
    try:
        # This is a simplified check - real implementation would:
        # 1. Identify oracle contracts
        # 2. Compare prices across multiple sources
        # 3. Detect significant deviations
        
        logger.info("Checking oracle deviations")
        
        # Placeholder for oracle deviation detection
        # Would need to identify oracle functions and compare prices
        
    except Exception as e:
        logger.error(f"Oracle check failed: {e}")
    
    return deviations


async def detect_rpc_drift(chain: str) -> List[Dict[str, Any]]:
    """Detect RPC endpoint drift"""
    drift_issues = []
    
    try:
        logger.info(f"Checking RPC drift for {chain}")
        
        rpc_url = RPC_URLS.get(chain)
        if not rpc_url:
            return drift_issues
        
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Check basic connectivity and sync status
        if not w3.is_connected():
            drift_issues.append({
                "type": "rpc_disconnected",
                "chain": chain,
                "rpc": rpc_url
            })
        else:
            # Check block number consistency
            block_number = w3.eth.block_number
            
            # Compare with another RPC (if available)
            # This is simplified - real implementation would compare multiple RPCs
            
            logger.info(f"RPC at block {block_number}")
        
    except Exception as e:
        logger.error(f"RPC drift detection failed: {e}")
        drift_issues.append({
            "type": "rpc_error",
            "chain": chain,
            "error": str(e)
        })
    
    return drift_issues


@app.post("/monitor", response_model=MonitorResult)
async def monitor(request: MonitorRequest):
    """Perform dynamic monitoring"""
    logger.info(f"Starting monitoring for scan: {request.scan_id}")
    
    result = MonitorResult(
        scan_id=request.scan_id,
        contract_address=request.contract_address
    )
    
    try:
        # Initialize Web3
        rpc_url = RPC_URLS.get(request.chain)
        if not rpc_url:
            raise HTTPException(status_code=400, detail=f"Unsupported chain: {request.chain}")
        
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            raise HTTPException(status_code=503, detail=f"Cannot connect to {request.chain} RPC")
        
        # Convert duration to seconds
        duration_seconds = min(request.duration_minutes * 60, 300)  # Max 5 minutes
        
        # Run monitoring tasks
        logger.info(f"Monitoring for {duration_seconds}s")
        
        # Mempool monitoring
        result.mempool_anomalies = await monitor_mempool(
            w3,
            request.contract_address,
            duration_seconds
        )
        
        # Oracle deviation check
        result.oracle_deviations = await check_oracle_deviation(
            w3,
            request.contract_address
        )
        
        # RPC drift detection
        result.rpc_drift = await detect_rpc_drift(request.chain)
        
        # Calculate total anomalies
        result.total_anomalies = (
            len(result.mempool_anomalies) +
            len(result.oracle_deviations) +
            len(result.rpc_drift)
        )
        
        logger.info(f"Monitoring complete: {result.total_anomalies} anomalies detected")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return result


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "monitoring-agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
