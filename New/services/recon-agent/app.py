"""
Recon Agent
Repository mapping, DNS/ENS enumeration, RPC discovery, ABI extraction
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import httpx
import os
import logging
import json
from web3 import Web3
import dns.resolver
import re
from bs4 import BeautifulSoup
import git
from pathlib import Path
import asyncio
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('recon_requests_total', 'Total requests')
SCAN_DURATION = Histogram('recon_scan_duration_seconds', 'Scan duration')

# Get service URLs from environment
LLM_ROUTER_URL = os.getenv("LLM_ROUTER_URL", "http://llm-router:8000")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

app = FastAPI(title="Recon Agent", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Common block explorers
EXPLORERS = {
    "ethereum": "https://api.etherscan.io/api",
    "bsc": "https://api.bscscan.com/api",
    "polygon": "https://api.polygonscan.com/api",
    "arbitrum": "https://api.arbiscan.io/api",
    "optimism": "https://api-optimistic.etherscan.io/api",
    "base": "https://api.basescan.org/api",
}


class ReconRequest(BaseModel):
    """Request for reconnaissance"""
    target_url: Optional[str] = None
    contract_address: Optional[str] = None
    chain: str = "ethereum"


class ReconResult(BaseModel):
    """Reconnaissance results"""
    target_url: Optional[str] = None
    repository_info: Optional[Dict[str, Any]] = None
    contracts: List[Dict[str, Any]] = []
    abis: List[Dict[str, Any]] = []
    dns_records: List[Dict[str, str]] = []
    ens_records: List[Dict[str, str]] = []
    rpc_endpoints: List[str] = []
    frontend_info: Optional[Dict[str, Any]] = None
    backend_info: Optional[Dict[str, Any]] = None
    surface_map: Dict[str, Any] = {}


async def call_llm(task_type: str, prompt: str, system_prompt: Optional[str] = None) -> str:
    """Call LLM Router"""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{LLM_ROUTER_URL}/generate",
            json={
                "task_type": task_type,
                "prompt": prompt,
                "system_prompt": system_prompt
            }
        )
        response.raise_for_status()
        return response.json()["response"]


async def clone_repository(url: str) -> Optional[Path]:
    """Clone git repository"""
    try:
        # Extract repo name
        repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
        clone_path = Path(f"/app/data/repos/{repo_name}")
        
        if clone_path.exists():
            logger.info(f"Repository already cloned: {clone_path}")
            return clone_path
        
        logger.info(f"Cloning repository: {url}")
        git.Repo.clone_from(url, clone_path, depth=1)
        return clone_path
    except Exception as e:
        logger.error(f"Failed to clone repository: {e}")
        return None


async def analyze_repository_structure(repo_path: Path) -> Dict[str, Any]:
    """Analyze repository structure"""
    structure = {
        "has_contracts": False,
        "has_frontend": False,
        "has_backend": False,
        "contract_files": [],
        "frontend_files": [],
        "backend_files": [],
        "languages": set(),
        "frameworks": set()
    }
    
    # Scan for files
    for file_path in repo_path.rglob("*"):
        if file_path.is_file():
            suffix = file_path.suffix.lower()
            
            # Smart contracts
            if suffix in ['.sol', '.vy', '.rs']:
                structure["has_contracts"] = True
                structure["contract_files"].append(str(file_path.relative_to(repo_path)))
                if suffix == '.sol':
                    structure["languages"].add("Solidity")
                elif suffix == '.vy':
                    structure["languages"].add("Vyper")
                elif suffix == '.rs':
                    structure["languages"].add("Rust")
            
            # Frontend
            elif suffix in ['.jsx', '.tsx', '.vue']:
                structure["has_frontend"] = True
                structure["frontend_files"].append(str(file_path.relative_to(repo_path)))
                structure["languages"].add("JavaScript/TypeScript")
            
            # Backend
            elif suffix in ['.py', '.js', '.ts', '.go']:
                if 'server' in str(file_path).lower() or 'api' in str(file_path).lower():
                    structure["has_backend"] = True
                    structure["backend_files"].append(str(file_path.relative_to(repo_path)))
    
    # Detect frameworks
    if (repo_path / "package.json").exists():
        try:
            with open(repo_path / "package.json") as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "react" in deps:
                    structure["frameworks"].add("React")
                if "next" in deps:
                    structure["frameworks"].add("Next.js")
                if "vue" in deps:
                    structure["frameworks"].add("Vue.js")
        except:
            pass
    
    if (repo_path / "foundry.toml").exists():
        structure["frameworks"].add("Foundry")
    
    if (repo_path / "hardhat.config.js").exists() or (repo_path / "hardhat.config.ts").exists():
        structure["frameworks"].add("Hardhat")
    
    structure["languages"] = list(structure["languages"])
    structure["frameworks"] = list(structure["frameworks"])
    
    return structure


async def extract_contract_source(repo_path: Path, contract_files: List[str]) -> Dict[str, str]:
    """Extract source code from contract files"""
    sources = {}
    
    for file_path in contract_files[:10]:  # Limit to first 10 contracts
        try:
            full_path = repo_path / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                sources[file_path] = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
    
    return sources


async def fetch_contract_abi(address: str, chain: str) -> Optional[Dict[str, Any]]:
    """Fetch contract ABI from block explorer"""
    explorer_url = EXPLORERS.get(chain)
    if not explorer_url:
        logger.warning(f"No explorer configured for chain: {chain}")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                explorer_url,
                params={
                    "module": "contract",
                    "action": "getabi",
                    "address": address
                }
            )
            data = response.json()
            
            if data.get("status") == "1":
                return {
                    "address": address,
                    "abi": json.loads(data["result"]),
                    "verified": True
                }
    except Exception as e:
        logger.error(f"Failed to fetch ABI for {address}: {e}")
    
    return None


async def resolve_dns_records(domain: str) -> List[Dict[str, str]]:
    """Resolve DNS records"""
    records = []
    record_types = ['A', 'AAAA', 'CNAME', 'MX', 'TXT']
    
    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            for rdata in answers:
                records.append({
                    "type": record_type,
                    "value": str(rdata)
                })
        except:
            pass
    
    return records


async def discover_rpc_endpoints(repo_path: Path) -> List[str]:
    """Discover RPC endpoints from configuration files"""
    endpoints = set()
    
    # Common config files
    config_files = [
        "hardhat.config.js",
        "hardhat.config.ts",
        "foundry.toml",
        ".env",
        ".env.example",
        "truffle-config.js"
    ]
    
    rpc_pattern = re.compile(r'https?://[^\s\'"]+(?:infura|alchemy|quicknode|rpc)[^\s\'"]*')
    
    for config_file in config_files:
        file_path = repo_path / config_file
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    matches = rpc_pattern.findall(content)
                    endpoints.update(matches)
            except:
                pass
    
    return list(endpoints)


@app.post("/scan", response_model=ReconResult)
async def scan(request: ReconRequest):
    """Perform reconnaissance scan"""
    # Handle address-only scans
    if not request.target_url and request.contract_address:
        logger.info(f"Starting address-only recon for: {request.contract_address} on {request.chain}")
        result = ReconResult(target_url=f"contract://{request.contract_address}")
       
        try:
            # Fetch contract ABI
            abi_data = await fetch_contract_abi(request.contract_address, request.chain)
            if abi_data:
                result.abis.append(abi_data)
                # Create minimal contracts array for fuzzing compatibility
                result.contracts = [{
                    "address": request.contract_address,
                    "chain": request.chain,
                    "name": "Contract",
                    "abi": abi_data.get("abi", [])
                }]
            
            logger.info(f"Address-only recon completed: {len(result.contracts)} contracts")
        except Exception as e:
            logger.error(f"Address-only recon failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        
        return result
    
    # Original repository-based scan
    if not request.target_url:
        raise HTTPException(status_code=422, detail="Either target_url or contract_address must be provided")
    
    logger.info(f"Starting recon for: {request.target_url}")
    
    result = ReconResult(target_url=request.target_url)
    
    try:
        # Clone repository if it's a git URL
        if 'github.com' in request.target_url or 'gitlab.com' in request.target_url:
            repo_path = await clone_repository(request.target_url)
            
            if repo_path:
                # Analyze repository structure
                structure = await analyze_repository_structure(repo_path)
                result.repository_info = structure
                
                # Extract contract source code
                if structure["contract_files"]:
                    sources = await extract_contract_source(repo_path, structure["contract_files"])
                    result.contracts = [
                        {
                            "file": file_path,
                            "source": source,
                            "language": "Solidity" if file_path.endswith('.sol') else "Other"
                        }
                        for file_path, source in sources.items()
                    ]
                
                # Discover RPC endpoints
                result.rpc_endpoints = await discover_rpc_endpoints(repo_path)
                
                # Use LLM to analyze surface map
                if structure["has_contracts"]:
                    prompt = f"""Analyze this Web3 project structure and identify potential attack surfaces:
                    
Contracts: {len(structure['contract_files'])}
Frontend: {structure['has_frontend']}
Backend: {structure['has_backend']}
Languages: {structure['languages']}
Frameworks: {structure['frameworks']}

Provide a brief security-focused surface map highlighting key areas to investigate."""
                    
                    surface_analysis = await call_llm(
                        "code_analysis",
                        prompt,
                        "You are a Web3 security researcher analyzing project attack surfaces."
                    )
                    
                    result.surface_map = {
                        "analysis": surface_analysis,
                        "contract_count": len(structure["contract_files"]),
                        "has_frontend": structure["has_frontend"],
                        "has_backend": structure["has_backend"]
                    }
        
        # Fetch contract ABI if address provided
        if request.contract_address:
            abi_data = await fetch_contract_abi(request.contract_address, request.chain)
            if abi_data:
                result.abis.append(abi_data)
        
        # DNS reconnaissance (extract domain from URL)
        if request.target_url:
            domain_match = re.search(r'https?://([^/]+)', request.target_url)
            if domain_match:
                domain = domain_match.group(1)
                result.dns_records = await resolve_dns_records(domain)
        
        logger.info(f"Recon completed: {len(result.contracts)} contracts, {len(result.abis)} ABIs")
        
    except Exception as e:
        logger.error(f"Recon failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return result


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "recon-agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
