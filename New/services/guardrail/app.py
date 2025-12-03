from fastapi import FastAPI, HTTPException, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Set
import asyncio
from web3 import Web3
from datetime import datetime
import os
import json

app = FastAPI(
    title="Guardrail Auto-Pause System",
    description="Real-time transaction monitoring with automatic contract pausing",
    version="1.0.0"
)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory storage for active monitors
active_monitors: Dict[str, asyncio.Task] = {}
pause_requests: List[Dict] = []

class MonitorRequest(BaseModel):
    """Request to start monitoring a contract"""
    contract_address: str = Field(..., description="Contract address to monitor", min_length=42, max_length=42)
    chain: str = Field(default="ethereum", description="Blockchain network")
    rpc_url: Optional[str] = Field(None, description="Custom RPC endpoint")
    auto_pause: bool = Field(False, description="Automatically pause on exploit detection")
    alert_channels: List[str] = Field(default=["api"], description="Alert channels: api, slack, email")

class PauseRequest(BaseModel):
    """Request to pause a contract"""
    contract_address: str
    reason: str
    severity: str = Field(default="high", description="Severity: low, medium, high, critical")
    auto_approved: bool = Field(default=False)

class SimulationResult(BaseModel):
    """Result from transaction simulation"""
    tx_hash: str
    is_exploitive: bool
    risk_score: float  # 0.0 to 1.0
    patterns_detected: List[str]
    state_changes: Dict
    recommendation: str  # "allow", "block", "pause_contract"

class MempoolMonitor:
    """
    Monitors blockchain mempool for suspicious transactions
    """
    
    def __init__(self, contract_address: str, rpc_url: str):
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.monitored_txs: Set[str] = set()
        
    async def start_monitoring(self, callback):
        """
        Start monitoring pending transactions
        
        Note: This is a simplified implementation. In production, you would:
        - Use WebSocket connections for real-time updates
        - Subscribe to pending transaction events
        - Filter by contract address
        """
        while True:
            try:
                # Get pending transactions
                # Note: This requires a full node with txpool access
                # For production, use services like Blocknative or Alchemy
                
                # Simulated monitoring loop
                await asyncio.sleep(5)  # Check every 5 seconds
                
                # In production, you would:
                # 1. Connect to mempool via WebSocket
                # 2. Filter transactions targeting your contract
                # 3. Call simulation for each transaction
                # 4. Trigger alerts based on results
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def get_pending_transactions(self) -> List[Dict]:
        """
        Get pending transactions targeting the monitored contract
        
        Returns list of transaction objects
        """
        # This requires access to txpool
        # Most public RPC endpoints don't expose this
        # Use Blocknative, Alchemy, or your own node
        return []

class TransactionSimulator:
    """
    Simulates transactions on a forked network to detect exploits
    """
    
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        
    async def simulate_transaction(self, tx_data: Dict) -> SimulationResult:
        """
        Simulate a transaction and analyze for exploit patterns
        
        Args:
            tx_data: Transaction data including from, to, data, value
            
        Returns:
            SimulationResult with risk assessment
        """
        # In production, this would:
        # 1. Create a fork at current block
        # 2. Execute the transaction
        # 3. Analyze state changes
        # 4. Check for exploit patterns:
        #    - Reentrancy
        #    - Flash loan attacks  
        #    - Price manipulation
        #    - Unusual token transfers
        #    - Access control violations
        
        # Simulate patterns detection
        patterns_detected = self._detect_patterns(tx_data)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(patterns_detected)
        
        # Determine recommendation
        if risk_score >= 0.8:
            recommendation = "pause_contract"
        elif risk_score >= 0.5:
            recommendation = "block"
        else:
            recommendation = "allow"
        
        return SimulationResult(
            tx_hash=tx_data.get('hash', 'pending'),
            is_exploitive=risk_score >= 0.5,
            risk_score=risk_score,
            patterns_detected=patterns_detected,
            state_changes={},
            recommendation=recommendation
        )
    
    def _detect_patterns(self, tx_data: Dict) -> List[str]:
        """Detect exploit patterns in transaction"""
        patterns = []
        
        # Check for common exploit patterns
        # This is a placeholder - real implementation would use:
        # - Tenderly simulation API
        # - Hardhat forking
        # - Custom EVM execution
        
        if tx_data.get('value', 0) > 0:
            patterns.append("value_transfer")
        
        if len(tx_data.get('data', '')) > 1000:
            patterns.append("complex_call")
        
        return patterns
    
    def _calculate_risk_score(self, patterns: List[str]) -> float:
        """Calculate risk score from detected patterns"""
        # Simple scoring - in production, use ML model
        pattern_scores = {
            "reentrancy": 0.9,
            "flash_loan": 0.8,
            "price_manipulation": 0.85,
            "access_control_bypass": 0.95,
            "value_transfer": 0.3,
            "complex_call": 0.4
        }
        
        if not patterns:
            return 0.0
        
        max_score = max([pattern_scores.get(p, 0.5) for p in patterns])
        return max_score

class PauseManager:
    """
    Manages contract pause requests and execution
    """
    
    @staticmethod
    async def create_pause_request(request: PauseRequest) -> Dict:
        """
        Create a pause request
        
        In production, this would:
        - Generate a transaction to call pause() on the contract
        - Require multi-sig approval if not auto-approved
        - Execute via safe transaction service
        """
        pause_req = {
            "id": len(pause_requests) + 1,
            "contract_address": request.contract_address,
            "reason": request.reason,
            "severity": request.severity,
            "status": "auto_approved" if request.auto_approved else "pending_approval",
            "created_at": datetime.utcnow().isoformat(),
            "executed_at": None
        }
        
        pause_requests.append(pause_req)
        
        return pause_req
    
    @staticmethod
    async def execute_pause(pause_id: int) -> Dict:
        """
        Execute an approved pause request
        
        This would call the pause() function on the target contract
        """
        # Find the pause request
        for req in pause_requests:
            if req["id"] == pause_id:
                if req["status"] != "pending_approval":
                    raise HTTPException(400, "Request already processed")
                
                # In production, execute the pause transaction
                # via web3.py or ethers.js
                
                req["status"] = "executed"
                req["executed_at"] = datetime.utcnow().isoformat()
                
                return req
        
        raise HTTPException(404, "Pause request not found")

@app.post("/monitor/start")
async def start_monitoring(request: MonitorRequest, background_tasks: BackgroundTasks):
    """
    Start monitoring a contract for suspicious activity
    """
    address = request.contract_address.lower()
    
    if address in active_monitors:
        raise HTTPException(400, f"Already monitoring {address}")
    
    # Get RPC URL
    rpc_urls = {
        "ethereum": os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com"),
        "bsc": os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org"),
        "polygon": os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
    }
    rpc_url = request.rpc_url or rpc_urls.get(request.chain, rpc_urls["ethereum"])
    
    # Create monitor
    monitor = MempoolMonitor(request.contract_address, rpc_url)
    
    # Start monitoring in background
    async def monitor_loop():
        simulator = TransactionSimulator(rpc_url)
        
        async def process_tx(tx):
            # Simulate transaction
            result = await simulator.simulate_transaction(tx)
            
            if result.recommendation == "pause_contract" and request.auto_pause:
                # Auto-pause
                pause_req = PauseRequest(
                    contract_address=request.contract_address,
                    reason=f"Exploit detected: {', '.join(result.patterns_detected)}",
                    severity="critical",
                    auto_approved=True
                )
                await PauseManager.create_pause_request(pause_req)
        
        await monitor.start_monitoring(process_tx)
    
    # Start background task
    task = asyncio.create_task(monitor_loop())
    active_monitors[address] = task
    
    return {
        "status": "monitoring",
        "contract_address": request.contract_address,
        "chain": request.chain,
        "auto_pause": request.auto_pause,
        "message": "Monitoring started successfully"
    }

@app.post("/monitor/stop")
async def stop_monitoring(contract_address: str):
    """Stop monitoring a contract"""
    address = contract_address.lower()
    
    if address not in active_monitors:
        raise HTTPException(404, "Contract not being monitored")
    
    # Cancel monitoring task
    active_monitors[address].cancel()
    del active_monitors[address]
    
    return {
        "status": "stopped",
        "contract_address": contract_address,
        "message": "Monitoring stopped"
    }

@app.get("/monitor/status")
async def get_monitoring_status():
    """Get status of all active monitors"""
    return {
        "active_monitors": list(active_monitors.keys()),
        "total": len(active_monitors)
    }

@app.post("/pause/request")
async def request_pause(request: PauseRequest):
    """
    Create a request to pause a contract
    Manual approval required unless auto_approved=True
    """
    pause_req = await PauseManager.create_pause_request(request)
    return pause_req

@app.post("/pause/approve/{pause_id}")
async def approve_pause(pause_id: int):
    """Approve and execute a pause request"""
    result = await PauseManager.execute_pause(pause_id)
    return result

@app.get("/pause/requests")
async def get_pause_requests():
    """Get all pause requests"""
    return {
        "requests": pause_requests,
        "total": len(pause_requests)
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "guardrail",
        "version": "1.0.0",
        "active_monitors": len(active_monitors)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
