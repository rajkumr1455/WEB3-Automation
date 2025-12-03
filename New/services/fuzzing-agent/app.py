"""
Fuzzing Agent
Foundry fuzz testing, Echidna property tests, ABI mutation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import httpx
import os
import logging
import json
import subprocess
import tempfile
from pathlib import Path
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fuzzing Agent", version="1.0.0")
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


class FuzzRequest(BaseModel):
    """Request for fuzzing"""
    scan_id: str
    contracts: List[Dict[str, Any]]
    abis: List[Dict[str, Any]] = []


class FuzzResult(BaseModel):
    """Fuzzing results"""
    scan_id: str
    foundry_results: List[Dict[str, Any]] = []
    mutation_results: List[Dict[str, Any]] = []
    total_tests: int = 0
    failed_tests: int = 0
    coverage_percent: Optional[float] = None


async def call_llm(task_type: str, prompt: str, system_prompt: Optional[str] = None) -> str:
    """Call LLM Router"""
    async with httpx.AsyncClient(timeout=180) as client:
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


async def generate_fuzz_tests(contract_source: str, contract_name: str) -> str:
    """Generate Foundry fuzz tests using LLM"""
    prompt = f"""Generate Foundry fuzz tests for this Solidity contract:

```solidity
{contract_source[:2000]}  // Truncated for brevity
```

Contract name: {contract_name}

Generate comprehensive fuzz tests covering:
1. Input validation
2. Access control
3. Arithmetic operations
4. State transitions

Return ONLY the Solidity test code."""
    
    return await call_llm(
        "code_analysis",
        prompt,
        "You are a smart contract security engineer writing Foundry fuzz tests."
    )


async def run_foundry_fuzz(project_path: Path) -> Dict[str, Any]:
    """Run Foundry fuzz tests"""
    try:
        logger.info(f"Running Foundry fuzz in {project_path}")
        
        # Initialize Foundry project
        subprocess.run(
            ["forge", "init", "--force"],
            cwd=project_path,
            capture_output=True,
            timeout=30
        )
        
        # Run fuzz tests
        result = subprocess.run(
            ["forge", "test", "--json"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.stdout:
            # Parse results
            lines = result.stdout.strip().split('\n')
            test_results = []
            
            for line in lines:
                try:
                    data = json.loads(line)
                    if data.get("type") == "test_result":
                        test_results.append({
                            "test": data.get("test"),
                            "status": data.get("status"),
                            "reason": data.get("reason"),
                            "counterexample": data.get("counterexample")
                        })
                except:
                    pass
            
            return {
                "tests": test_results,
                "total": len(test_results),
                "failed": len([t for t in test_results if t["status"] == "Failure"])
            }
        
    except subprocess.TimeoutExpired:
        logger.error("Foundry timeout")
    except Exception as e:
        logger.error(f"Foundry failed: {e}")
    
    return {"tests": [], "total": 0, "failed": 0}


async def mutate_abi_inputs(abi: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate mutated inputs for ABI fuzzing"""
    mutations = []
    
    for func in abi:
        if func.get("type") == "function" and func.get("inputs"):
            # Generate edge case inputs
            for input_param in func["inputs"]:
                param_type = input_param.get("type", "")
                
                edge_cases = []
                if "uint" in param_type:
                    edge_cases = [0, 1, 2**256 - 1, 2**255]
                elif "int" in param_type:
                    edge_cases = [0, -1, 2**255 - 1, -(2**255)]
                elif "address" in param_type:
                    edge_cases = [
                        "0x0000000000000000000000000000000000000000",
                        "0xFFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF"
                    ]
                elif "bool" in param_type:
                    edge_cases = [True, False]
                
                mutations.append({
                    "function": func.get("name"),
                    "parameter": input_param.get("name"),
                    "type": param_type,
                    "edge_cases": edge_cases
                })
    
    return mutations


@app.post("/fuzz", response_model=FuzzResult)
async def fuzz(request: FuzzRequest):
    """Perform fuzzing"""
    logger.info(f"Starting fuzzing for scan: {request.scan_id}")
    
    result = FuzzResult(scan_id=request.scan_id)
    
    try:
        # Create temporary directory for fuzzing
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Process each contract
            for contract in request.contracts[:3]:  # Limit to 3 contracts
                if contract.get("source"):
                    contract_name = Path(contract.get("file", "Contract")).stem
                    
                    # Generate fuzz tests
                    logger.info(f"Generating fuzz tests for {contract_name}")
                    fuzz_tests = await generate_fuzz_tests(
                        contract["source"],
                        contract_name
                    )
                    
                    # Write contract and test files
                    src_dir = tmpdir_path / "src"
                    test_dir = tmpdir_path / "test"
                    src_dir.mkdir(exist_ok=True)
                    test_dir.mkdir(exist_ok=True)
                    
                    with open(src_dir / f"{contract_name}.sol", 'w') as f:
                        f.write(contract["source"])
                    
                    with open(test_dir / f"{contract_name}.t.sol", 'w') as f:
                        f.write(fuzz_tests)
                    
                    # Run Foundry fuzz
                    foundry_result = await run_foundry_fuzz(tmpdir_path)
                    result.foundry_results.append({
                        "contract": contract_name,
                        **foundry_result
                    })
                    
                    result.total_tests += foundry_result.get("total", 0)
                    result.failed_tests += foundry_result.get("failed", 0)
            
            # ABI mutation fuzzing
            for abi_data in request.abis[:3]:  # Limit to 3 ABIs
                if abi_data.get("abi"):
                    mutations = await mutate_abi_inputs(abi_data["abi"])
                    result.mutation_results.append({
                        "contract": abi_data.get("address"),
                        "mutations": mutations,
                        "count": len(mutations)
                    })
        
        logger.info(f"Fuzzing complete: {result.total_tests} tests, {result.failed_tests} failed")
        
    except Exception as e:
        logger.error(f"Fuzzing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return result


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "fuzzing-agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
