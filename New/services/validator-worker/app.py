from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import asyncio
import subprocess
import json
import os
import tempfile
import shutil
from datetime import datetime
from enum import Enum

app = FastAPI(
    title="Validator Worker",
    description="Reproduce and validate security findings in sandboxed environments",
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


# In-memory storage for validation jobs
validation_jobs: Dict[str, Dict] = {}
job_queue: asyncio.Queue = asyncio.Queue()

class FindingSeverity(str, Enum):
    """Severity levels for findings"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ValidationStatus(str, Enum):
    """Status of validation job"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class FindingType(str, Enum):
    """Types of security findings"""
    REENTRANCY = "reentrancy"
    INTEGER_OVERFLOW = "integer_overflow"
    ACCESS_CONTROL = "access_control"
    UNCHECKED_CALL = "unchecked_call"
    FLASH_LOAN = "flash_loan"
    PRICE_MANIPULATION = "price_manipulation"
    OTHER = "other"

class Finding(BaseModel):
    """Security finding to validate"""
    id: str = Field(..., description="Unique finding ID")
    type: FindingType
    severity: FindingSeverity
    title: str
    description: str
    contract_address: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    proof_of_concept: Optional[str] = Field(None, description="PoC code to reproduce")

class ValidationRequest(BaseModel):
    """Request to validate a finding"""
    finding: Finding
    chain: str = Field(default="ethereum", description="Blockchain network")
    timeout: int = Field(default=300, description="Timeout in seconds")
    sandbox_type: str = Field(default="foundry", description="Sandbox: foundry, hardhat, docker")

class ValidationResult(BaseModel):
    """Result of validation"""
    job_id: str
    finding_id: str
    status: ValidationStatus
    is_valid: Optional[bool] = None
    confidence: Optional[float] = Field(None, description="Confidence score 0.0-1.0")
    execution_trace: Optional[str] = None
    state_diff: Optional[Dict] = None
    gas_used: Optional[int] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

class SandboxManager:
    """
    Manages sandboxed execution environments for validation
    """
    
    @staticmethod
    async def create_foundry_sandbox(source_code: str, poc_code: str) -> str:
        """
        Create a Foundry test environment
        
        Args:
            source_code: Contract source code
            poc_code: Proof of concept test code
            
        Returns:
            Path to sandbox directory
        """
        # Create temporary directory
        sandbox_dir = tempfile.mkdtemp(prefix="validator_")
        
        try:
            # Initialize Foundry project
            await asyncio.create_subprocess_exec(
                "forge", "init", "--no-git", sandbox_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Write contract source
            contract_path = os.path.join(sandbox_dir, "src", "Target.sol")
            with open(contract_path, 'w') as f:
                f.write(source_code)
            
            # Write PoC test
            test_path = os.path.join(sandbox_dir, "test", "Exploit.t.sol")
            with open(test_path, 'w') as f:
                f.write(poc_code)
            
            return sandbox_dir
            
        except Exception as e:
            shutil.rmtree(sandbox_dir, ignore_errors=True)
            raise Exception(f"Failed to create sandbox: {e}")
    
    @staticmethod
    async def run_foundry_test(sandbox_dir: str, timeout: int = 300) -> Dict:
        """
        Run Foundry test and capture results
        
        Returns:
            Dict with execution results
        """
        try:
            # Run forge test with verbosity
            process = await asyncio.create_subprocess_exec(
                "forge", "test", "-vvv",
                cwd=sandbox_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "error": "Execution timeout",
                    "trace": None
                }
            
            output = stdout.decode() + stderr.decode()
            
            # Parse output for results
            is_exploit_successful = "test_exploit()" in output and "[PASS]" in output
            
            return {
                "success": is_exploit_successful,
                "output": output,
                "trace": output if is_exploit_successful else None,
                "exit_code": process.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "trace": None
            }
    
    @staticmethod
    def cleanup_sandbox(sandbox_dir: str):
        """Clean up sandbox directory"""
        try:
            shutil.rmtree(sandbox_dir, ignore_errors=True)
        except Exception as e:
            print(f"Cleanup error: {e}")

class FindingReproducer:
    """
    Reproduces security findings in controlled environments
    """
    
    @staticmethod
    async def reproduce_finding(
        finding: Finding,
        source_code: str,
        poc_code: str,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Attempt to reproduce a security finding
        
        Args:
            finding: Finding to reproduce
            source_code: Contract source code
            poc_code: Proof of concept code
            timeout: Execution timeout
            
        Returns:
            Reproduction results with trace and validation status
        """
        sandbox_dir = None
        
        try:
            # Create sandbox
            sandbox_dir = await SandboxManager.create_foundry_sandbox(
                source_code, poc_code
            )
            
            # Run test
            result = await SandboxManager.run_foundry_test(sandbox_dir, timeout)
            
            # Analyze results
            is_valid = result.get("success", False)
            confidence = 0.9 if is_valid else 0.1
            
            return {
                "is_valid": is_valid,
                "confidence": confidence,
                "execution_trace": result.get("trace"),
                "error_message": result.get("error"),
                "exit_code": result.get("exit_code", -1)
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "confidence": 0.0,
                "execution_trace": None,
                "error_message": str(e),
                "exit_code": -1
            }
        
        finally:
            if sandbox_dir:
                SandboxManager.cleanup_sandbox(sandbox_dir)
    
    @staticmethod
    def generate_default_poc(finding: Finding) -> str:
        """
        Generate default PoC based on finding type
        
        Returns:
            Solidity test code
        """
        poc_templates = {
            FindingType.REENTRANCY: '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/Target.sol";

contract ExploitTest is Test {
    Target target;
    
    function setUp() public {
        target = new Target();
    }
    
    function test_exploit() public {
        // Reentrancy attack
        // This is a template - customize based on actual vulnerability
        vm.deal(address(this), 10 ether);
        target.deposit{value: 1 ether}();
        target.withdraw(1 ether);
    }
    
    receive() external payable {
        if (address(target).balance >= 1 ether) {
            target.withdraw(1 ether);
        }
    }
}
''',
            FindingType.INTEGER_OVERFLOW: '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/Target.sol";

contract ExploitTest is Test {
    Target target;
    
    function setUp() public {
        target = new Target();
    }
    
    function test_exploit() public {
        // Test integer overflow
        uint256 largeValue = type(uint256).max;
        target.vulnerableFunction(largeValue);
    }
}
''',
            FindingType.ACCESS_CONTROL: '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/Target.sol";

contract ExploitTest is Test {
    Target target;
    address attacker = address(0x1337);
    
    function setUp() public {
        target = new Target();
    }
    
    function test_exploit() public {
        // Test unauthorized access
        vm.prank(attacker);
        target.privilegedFunction();
    }
}
'''
        }
        
        return poc_templates.get(
            finding.type,
            "// No template available - manual PoC required"
        )

async def validation_worker():
    """
    Background worker that processes validation queue
    """
    while True:
        try:
            # Get next job from queue
            job_id = await job_queue.get()
            
            if job_id not in validation_jobs:
                continue
            
            job = validation_jobs[job_id]
            job["status"] = ValidationStatus.RUNNING
            
            finding = job["finding"]
            
            # Get source code (would fetch from repository in production)
            source_code = "// Contract source code here"
            
            # Generate or use provided PoC
            poc_code = finding.proof_of_concept or \
                       FindingReproducer.generate_default_poc(finding)
            
            # Reproduce finding
            result = await FindingReproducer.reproduce_finding(
                finding,
                source_code,
                poc_code,
                timeout=job["timeout"]
            )
            
            # Update job
            job["status"] = ValidationStatus.COMPLETED
            job["is_valid"] = result["is_valid"]
            job["confidence"] = result["confidence"]
            job["execution_trace"] = result["execution_trace"]
            job["error_message"] = result["error_message"]
            job["completed_at"] = datetime.utcnow()
            
        except Exception as e:
            if job_id in validation_jobs:
                validation_jobs[job_id]["status"] = ValidationStatus.FAILED
                validation_jobs[job_id]["error_message"] = str(e)
                validation_jobs[job_id]["completed_at"] = datetime.utcnow()
        
        finally:
            job_queue.task_done()

@app.on_event("startup")
async def startup_event():
    """Start background validation worker"""
    asyncio.create_task(validation_worker())

@app.post("/validate", response_model=ValidationResult)
async def validate_finding(request: ValidationRequest, background_tasks: BackgroundTasks):
    """
    Queue a finding for validation
    
    This will:
    1. Create a sandboxed environment
    2. Attempt to reproduce the finding
    3. Capture execution trace and state diff
    4. Return validation result
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # Create job
    job = {
        "job_id": job_id,
        "finding": request.finding,
        "finding_id": request.finding.id,
        "status": ValidationStatus.QUEUED,
        "chain": request.chain,
        "timeout": request.timeout,
        "sandbox_type": request.sandbox_type,
        "is_valid": None,
        "confidence": None,
        "execution_trace": None,
        "state_diff": None,
        "error_message": None,
        "started_at": datetime.utcnow(),
        "completed_at": None
    }
    
    validation_jobs[job_id] = job
    
    # Add to queue
    await job_queue.put(job_id)
    
    return ValidationResult(**job)

@app.get("/validate/{job_id}", response_model=ValidationResult)
async def get_validation_status(job_id: str):
    """Get validation job status"""
    if job_id not in validation_jobs:
        raise HTTPException(404, "Job not found")
    
    return ValidationResult(**validation_jobs[job_id])

@app.get("/validations")
async def list_validations():
    """List all validation jobs"""
    return {
        "jobs": list(validation_jobs.values()),
        "total": len(validation_jobs),
        "queued": len([j for j in validation_jobs.values() if j["status"] == ValidationStatus.QUEUED]),
        "running": len([j for j in validation_jobs.values() if j["status"] == ValidationStatus.RUNNING]),
        "completed": len([j for j in validation_jobs.values() if j["status"] == ValidationStatus.COMPLETED])
    }

@app.post("/validate/{job_id}/mark")
async def mark_finding(job_id: str, is_valid: bool, confidence: Optional[float] = None):
    """
    Manually mark a finding as valid/invalid
    Used when automated validation is inconclusive
    """
    if job_id not in validation_jobs:
        raise HTTPException(404, "Job not found")
    
    job = validation_jobs[job_id]
    job["is_valid"] = is_valid
    job["confidence"] = confidence or (0.9 if is_valid else 0.1)
    job["status"] = ValidationStatus.COMPLETED
    job["completed_at"] = datetime.utcnow()
    
    return job

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "validator-worker",
        "version": "1.0.0",
        "queue_size": job_queue.qsize(),
        "total_jobs": len(validation_jobs)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
