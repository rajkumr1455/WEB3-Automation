"""
Orchestrator Service
Central pipeline controller that coordinates all agents sequentially
Enhanced with Priority 2/3/4 implementations
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import httpx
import os
import logging
import json
import uuid
from datetime import datetime
from enum import Enum
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response
import asyncio

# Configure logging FIRST (before any code that uses logger)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add path for RPC pool import
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    from src.utils.rpc_connection_pool import RPCConnectionPool
    RPC_POOL_AVAILABLE = True
except ImportError:
    logger.warning("RPC pool not available, will use single RPC endpoints")
    RPC_POOL_AVAILABLE = False

# Prometheus metrics
SCAN_COUNT = Counter('orchestrator_scans_total', 'Total scans', ['status'])
SCAN_DURATION = Histogram('orchestrator_scan_duration_seconds', 'Scan duration')
ACTIVE_SCANS = Gauge('orchestrator_active_scans', 'Currently active scans')
AGENT_ERRORS = Counter('orchestrator_agent_errors_total', 'Agent errors', ['agent'])

app = FastAPI(title="Web3 Bounty Orchestrator", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # Next.js UI
        "http://localhost:3000",  # Grafana
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent URLs from environment (PRIORITY 2: Added address-scanner)
AGENT_URLS = {
    "llm_router": os.getenv("LLM_ROUTER_URL", "http://llm-router:8000"),
    "recon": os.getenv("RECON_AGENT_URL", "http://recon-agent:8002"),
    "static": os.getenv("STATIC_AGENT_URL", "http://static-agent:8003"),
    "fuzzing": os.getenv("FUZZING_AGENT_URL", "http://fuzzing-agent:8004"),
    "monitoring": os.getenv("MONITORING_AGENT_URL", "http://monitoring-agent:8005"),
    "triage": os.getenv("TRIAGE_AGENT_URL", "http://triage-agent:8006"),
    "reporting": os.getenv("REPORTING_AGENT_URL", "http://reporting-agent:8007"),
    "address_scanner": os.getenv("ADDRESS_SCANNER_URL", "http://address-scanner:8008"),
}

# In-memory scan storage (use Redis/DB in production)
scans_db: Dict[str, Dict[str, Any]] = {}

# RPC Connection Pools (PRIORITY 2: Multi-provider failover)
RPC_POOLS = {}

def initialize_rpc_pools():
    """Initialize RPC pools for supported chains with failover"""
    if not RPC_POOL_AVAILABLE:
        logger.info("RPC pool not available, skipping initialization")
        return
    
    chains_config = {
        "ethereum": [
            os.getenv("ETHEREUM_RPC_URL", os.getenv("ETH_RPC_URL")),
            os.getenv("ETHEREUM_RPC_URL_BACKUP")
        ],
        "bsc": [
            os.getenv("BSC_RPC_URL"),
            os.getenv("BSC_RPC_URL_BACKUP")
        ],
        "polygon": [
            os.getenv("POLYGON_RPC_URL"),
            os.getenv("POLYGON_RPC_URL_BACKUP")
        ]
    }
    
    for chain, providers in chains_config.items():
        providers = [p for p in providers if p]
        if providers:
            try:
                RPC_POOLS[chain] = RPCConnectionPool(
                    providers=providers,
                    health_check_interval=60,
                    circuit_breaker_threshold=5
                )
                logger.info(f"RPC pool configured for {chain} with {len(providers)} providers")
            except Exception as e:
                logger.error(f"Failed to create RPC pool for {chain}: {e}")



class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanRequest(BaseModel):
    """Request to start a new security scan"""
    target_url: Optional[str] = Field(None, description="Target repository or contract URL")
    contract_address: Optional[str] = Field(None, description="Smart contract address (if applicable)")
    chain: Optional[str] = Field("ethereum", description="Blockchain network")
    scan_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom scan configuration")


class ScanResponse(BaseModel):
    """Response for scan request"""
    scan_id: str
    status: ScanStatus
    message: str


class ScanResult(BaseModel):
    """Complete scan result"""
    scan_id: str
    status: ScanStatus
    target_url: str
    contract_address: Optional[str]
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    results: Optional[Dict[str, Any]]
    error: Optional[str]


async def call_agent(agent_name: str, endpoint: str, data: Dict[str, Any], timeout: int = 300) -> Dict[str, Any]:
    """Call an agent service"""
    url = f"{AGENT_URLS[agent_name]}{endpoint}"
    
    try:
        logger.info(f"Calling {agent_name} agent at {url}")
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        AGENT_ERRORS.labels(agent=agent_name).inc()
        logger.error(f"{agent_name} agent failed: {e}")
        raise


async def run_scan_pipeline(scan_id: str, request: ScanRequest):
    """Execute the complete security scan pipeline"""
    start_time = datetime.now()
    
    try:
        from db_helpers import update_scan_status, save_stage_result, get_all_stage_results
        
        ACTIVE_SCANS.inc()
        update_scan_status(scan_id, "running", progress=0)
        
        # PRIORITY 2: Stage 0 - Address Scanner (if contract address provided without repo)
        source_code_dict = {}
        if request.contract_address and not request.target_url:
            logger.info(f"[{scan_id}] Stage 0: Address Scanning")
            update_scan_status(scan_id, "running", current_stage="address_scan", progress=5)
            
            try:
                address_result = await call_agent("address_scanner", "/scan-address", {
                    "address": request.contract_address,
                    "chain": request.chain
                })
                save_stage_result(scan_id, "address_scan", 0, address_result)
                logger.info(f"[{scan_id}] Address scan complete")
            except Exception as e:
                logger.error(f"[{scan_id}] Address scan failed: {e}")
                address_result = {"error": str(e)}
        
        # Stage 4: Dynamic Monitoring
        logger.info(f"[{scan_id}] Stage 4: Dynamic Monitoring")
        update_scan_status(scan_id, "running", current_stage="monitoring")
        
        if request.contract_address:
            monitoring_result = await call_agent("monitoring", "/monitor", {
                "scan_id": scan_id,
                "contract_address": request.contract_address,
                "chain": request.chain,
                "duration_minutes": request.scan_config.get("monitor_duration", 5)
            })
            save_stage_result(scan_id, "monitoring", 4, monitoring_result)
        else:
            logger.info(f"[{scan_id}] Stage 4: Monitoring skipped (no contract address)")
        # Then, enhance with LLM analysis
        try:
            logger.info(f"[{scan_id}] Enhancing triage with LLM")
            llm_triage = await call_agent("llm_router", "/route", {
                "task_type": "triage",
                "prompt": f"""Analyze these security findings and prioritize them:

Findings: {json.dumps(triage_result.get('findings', [])[:10], indent=2)}

Identify:
1. Critical vulnerabilities requiring immediate attention
2. False positives that can be filtered out
3. Exploit scenarios and attack vectors
4. Recommended fix priorities

Provide concise, actionable analysis.""",
                "max_tokens": 2000,
                "temperature": 0.1
            }, timeout=60)
            
            triage_result["llm_analysis"] = llm_triage.get("response", "")
            logger.info(f"[{scan_id}] LLM triage enhancement complete")
        except Exception as e:
            logger.warning(f"[{scan_id}] LLM triage enhancement failed: {e}")
            triage_result["llm_analysis"] = None
        
        save_stage_result(scan_id, "triage", 5, triage_result)
        update_scan_status(scan_id, "running", progress=90)
        
        # PRIORITY 3: Stage 6 - LLM-Enhanced Reporting
        logger.info(f"[{scan_id}] Stage 6: LLM-Enhanced Reporting")
        update_scan_status(scan_id, "running", current_stage="reporting", progress=95)
        
        # Get all stage results for reporting
        all_stage_results = get_all_stage_results(scan_id)
        
        reporting_result = await call_agent("reporting", "/generate", {
            "scan_id": scan_id,
            "target_url": request.target_url,
            "contract_address": request.contract_address,
            "findings": all_stage_results
        })
        
        # Enhance report with LLM-generated executive summary
        try:
            logger.info(f"[{scan_id}] Generating LLM executive summary")
            llm_summary = await call_agent("llm_router", "/route", {
                "task_type": "summarize",
                "prompt": f"""Generate an executive summary for this security scan:

Target: {request.target_url or request.contract_address}
Findings Count: {len(triage_result.get('findings', []))}
Critical: {len([f for f in triage_result.get('findings', []) if f.get('severity') == 'critical'])}

Key Issues: {json.dumps(triage_result.get('findings', [])[:5], indent=2)}

Create a concise executive summary suitable for stakeholders.""",
                "max_tokens": 1000,
                "temperature": 0.2
            }, timeout=60)
            
            reporting_result["executive_summary"] = llm_summary.get("response", "")
            logger.info(f"[{scan_id}] LLM-enhanced report complete")
        except Exception as e:
            logger.warning(f"[{scan_id}] LLM report enhancement failed: {e}")
            reporting_result["executive_summary"] = None
        
        save_stage_result(scan_id, "reporting", 6, reporting_result)
        
        # Mark as completed
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Mark as completed in database
        update_scan_status(
            scan_id, 
            "completed", 
            current_stage="completed",
            progress=100,
            completed_at=end_time,
            duration_seconds=duration
        )
        
        SCAN_COUNT.labels(status="completed").inc()
        SCAN_DURATION.observe(duration)
        
        logger.info(f"[{scan_id}] Scan completed in {duration:.2f}s")
        
    except Exception as e:
        logger.error(f"[{scan_id}] Scan failed: {e}")
        update_scan_status(
            scan_id,
            "failed",
            error=str(e),
            completed_at=datetime.now()
        )
        SCAN_COUNT.labels(status="failed").inc()
    
    finally:
        # Decrement active scans counter
        try:
            ACTIVE_SCANS.dec()
        except Exception:
            logger.debug("ACTIVE_SCANS.dec() failed during cleanup")


@app.post("/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest):
    """Start a new security scan (queued via RQ)"""
    from rq_worker import queue_scan_job
    from db_helpers import create_job_record, create_scan_in_db
    
    scan_id = str(uuid.uuid4())
    
    # Create scan in DATABASE first (required for foreign key)
    try:
        create_scan_in_db(
            scan_id=scan_id,
            target_url=request.target_url or "",
            contract_address=request.contract_address or "",
            chain=request.chain or "ethereum",
            scan_config=request.scan_config or {}
        )
    except Exception as e:
        logger.error(f"Failed to create scan in DB: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create scan: {str(e)}")
    
    # ALSO initialize in-memory (for backward compat)
    scans_db[scan_id] = {
        "scan_id": scan_id,
        "status": ScanStatus.PENDING,
        "target_url": request.target_url,
        "contract_address": request.contract_address,
        "chain": request.chain,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "current_stage": "pending",
        "progress": 0,
        "results": {},
        "error": None
    }
    
    # Queue to RQ
    try:
        job_id = queue_scan_job(scan_id, request.dict())
        create_job_record(job_id=job_id, scan_id=scan_id, job_type="scan_pipeline")
        logger.info(f"Queued scan {scan_id} to RQ (job: {job_id})")
        
        return ScanResponse(
            scan_id=scan_id,
            status=ScanStatus.PENDING,
            message=f"Scan queued successfully (job: {job_id[:8]}...)"
        )
    except Exception as e:
        logger.error(f"Failed to queue scan: {e}")
        scans_db[scan_id]["status"] = ScanStatus.FAILED
        scans_db[scan_id]["error"] = f"Failed to queue: {str(e)}"
        raise HTTPException(status_code=500, detail=f"Failed to queue scan: {str(e)}")


@app.get("/scan/{scan_id}", response_model=ScanResult)
async def get_scan(scan_id: str):
    """Get scan status and results"""
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan = scans_db[scan_id]
    
    return ScanResult(
        scan_id=scan["scan_id"],
        status=scan["status"],
        target_url=scan["target_url"],
        contract_address=scan.get("contract_address"),
        started_at=scan["started_at"],
        completed_at=scan.get("completed_at"),
        duration_seconds=scan.get("duration_seconds"),
        results=scan.get("results") if scan["status"] == ScanStatus.COMPLETED else None,
        error=scan.get("error")
    )

@app.get("/scans")
async def list_scans(limit: int = 50, status: Optional[ScanStatus] = None):
    """List recent scans"""
    scans = list(scans_db.values())
    
    if status:
        scans = [s for s in scans if s["status"] == status]
    
    # Sort by start time (most recent first)
    scans.sort(key=lambda x: x["started_at"], reverse=True)
    
    return {
        "total": len(scans),
        "scans": scans[:limit]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    # Check agent connectivity
    agent_health = {}
    
    async with httpx.AsyncClient(timeout=5) as client:
        for agent_name, url in AGENT_URLS.items():
            try:
                response = await client.get(f"{url}/health")
                agent_health[agent_name] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                agent_health[agent_name] = "unreachable"
    
    all_healthy = all(status == "healthy" for status in agent_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "agents": agent_health,
        "active_scans": len([s for s in scans_db.values() if s["status"] == ScanStatus.RUNNING])
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")


# ===== Address Scanner Proxy Endpoints =====
@app.get("/address-scanner/supported-chains")
async def proxy_supported_chains():
    """Proxy endpoint for address-scanner supported chains"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://address-scanner:8008/supported-chains",
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch supported chains: {e}")
        raise HTTPException(status_code=503, detail="Address scanner service unavailable")


@app.post("/address-scanner/scan-address")
async def proxy_scan_address(request: Dict[str, Any]):
    """Proxy endpoint for address-scanner scan requests"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://address-scanner:8008/scan-address",
                json=request,
                timeout=180.0  # 3 minutes for scan timeout
            )
            
            if response.status_code != 200:
                error_detail = response.json().get('detail', 'Scan failed')
                raise HTTPException(status_code=response.status_code, detail=error_detail)
            
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Address scan timed out")
    except httpx.ConnectError:
        logger.error("Cannot connect to address-scanner service")
        raise HTTPException(status_code=503, detail="Address scanner service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to scan address: {e}")
        raise HTTPException(status_code=500, detail=f"Address scan failed: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Initialize RPC pools on startup"""
    logger.info("Orchestrator starting up...")
    initialize_rpc_pools()
    
    # Start RPC pool health checks
    for chain, pool in RPC_POOLS.items():
        try:
            await pool.start()
            logger.info(f"RPC pool started for {chain}")
        except Exception as e:
            logger.error(f"Failed to start RPC pool for {chain}: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop RPC pools on shutdown"""
    logger.info("Orchestrator shutting down...")
    for chain, pool in RPC_POOLS.items():
        try:
            await pool.stop()
            logger.info(f"RPC pool stopped for {chain}")
        except Exception as e:
            logger.error(f"Error stopping RPC pool for {chain}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
