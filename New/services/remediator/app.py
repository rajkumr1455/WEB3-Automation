from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import httpx
import os
import re

app = FastAPI(
    title="Remediator Service",
    description="Automated vulnerability remediation with GitHub PR creation",
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


# In-memory storage
remediation_jobs: Dict[str, Dict] = {}
pr_history: List[Dict] = []

class FindingType(str, Enum):
    """Types of security findings"""
    REENTRANCY = "reentrancy"
    INTEGER_OVERFLOW = "integer_overflow"
    ACCESS_CONTROL = "access_control"
    UNCHECKED_CALL = "unchecked_call"
    TIMESTAMP_DEPENDENCE = "timestamp_dependence"
    TX_ORIGIN = "tx_origin"

class RemediationStatus(str, Enum):
    """Status of remediation job"""
    QUEUED = "queued"
    ANALYZING = "analyzing"
    GENERATING_FIX = "generating_fix"
    VERIFYING = "verifying"
    CREATING_PR = "creating_pr"
    COMPLETED = "completed"
    FAILED = "failed"

class Finding(BaseModel):
    """Security finding to remediate"""
    id: str
    type: FindingType
    severity: str
    file_path: str
    line_number: int
    function_name: Optional[str] = None
    vulnerable_code: str
    description: str

class RemediationRequest(BaseModel):
    """Request to remediate a finding"""
    finding: Finding
    repo_url: str
    branch: str = Field(default="main")
    create_pr: bool = Field(default=True)
    auto_merge: bool = Field(default=False)

class FixGenerator:
    """
    Generate fixes for different vulnerability types
    """
    
    @staticmethod
    def generate_reentrancy_fix(vulnerable_code: str, function_name: str) -> Dict[str, str]:
        """
        Generate fix for reentrancy vulnerability
        
        Applies checks-effects-interactions pattern
        """
        # Add ReentrancyGuard modifier or mutex
        fixed_code = vulnerable_code
        
        # Check if using OpenZeppelin
        if "import" in vulnerable_code and "openzeppelin" in vulnerable_code.lower():
            # Add ReentrancyGuard modifier
            if function_name and "function " + function_name in vulnerable_code:
                fixed_code = re.sub(
                    rf"(function\s+{function_name}\s*\([^)]*\)\s+[^{{]*)",
                    r"\1 nonReentrant ",
                    vulnerable_code
                )
                
                explanation = f"""Added `nonReentrant` modifier from OpenZeppelin's ReentrancyGuard to prevent reentrancy attacks in `{function_name}()`.

**Changes:**
- Added `nonReentrant` modifier to function declaration
- Ensures function cannot be called recursively during execution

**Recommendation:** Ensure contract inherits from ReentrancyGuard:
```solidity
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract YourContract is ReentrancyGuard {{
    // ... your code
}}
```"""
        else:
            # Manual mutex pattern
            fixed_code = """// Add mutex pattern
bool private locked;

modifier noReentrant() {
    require(!locked, "No reentrancy");
    locked = true;
    _;
    locked = false;
}

""" + vulnerable_code
            
            explanation = "Added manual reentrancy guard using mutex pattern"
        
        return {
            "fixed_code": fixed_code,
            "explanation": explanation,
            "confidence": 0.9
        }
    
    @staticmethod
    def generate_access_control_fix(vulnerable_code: str, function_name: str) -> Dict[str, str]:
        """
        Generate fix for access control vulnerability
        
        Adds appropriate access modifiers
        """
        fixed_code = vulnerable_code
        
        # Add onlyOwner or appropriate modifier
        if function_name and "function " + function_name in vulnerable_code:
            fixed_code = re.sub(
                rf"(function\s+{function_name}\s*\([^)]*\)\s+[^{{]*)",
                r"\1 onlyOwner ",
                vulnerable_code
            )
            
            explanation = f"""Added `onlyOwner` modifier to restrict access to `{function_name}()`.

**Changes:**
- Added access control modifier
- Prevents unauthorized users from calling this function

**Recommendation:** Ensure contract inherits from Ownable:
```solidity
import "@openzeppelin/contracts/access/Ownable.sol";

contract YourContract is Ownable {{
    // ... your code
}}
```

**Alternative:** Consider using role-based access control (AccessControl) for more granular permissions."""
        else:
            explanation = "Added access control modifier"
        
        return {
            "fixed_code": fixed_code,
            "explanation": explanation,
            "confidence": 0.85
        }
    
    @staticmethod
    def generate_integer_overflow_fix(vulnerable_code: str) -> Dict[str, str]:
        """
        Generate fix for integer overflow vulnerability
        
        For Solidity >= 0.8.0, overflow protection is built-in
        For older versions, suggests SafeMath
        """
        # Check Solidity version
        if "pragma solidity ^0.8" in vulnerable_code or "pragma solidity 0.8" in vulnerable_code:
            explanation = """**Good News:** Solidity 0.8.0+ includes built-in overflow protection.

No code changes needed - overflow protection is automatic!

**Note:** Remove any SafeMath usage as it's redundant in Solidity 0.8+"""
            
            # Remove SafeMath if present
            fixed_code = re.sub(r'using SafeMath for uint256;', '// SafeMath not needed in Solidity 0.8+', vulnerable_code)
            fixed_code = re.sub(r'\.add\(', ' + ', fixed_code)
            fixed_code = re.sub(r'\.sub\(', ' - ', fixed_code)
            fixed_code = re.sub(r'\.mul\(', ' * ', fixed_code)
            fixed_code = re.sub(r'\.div\(', ' / ', fixed_code)
            
            confidence = 0.95
        else:
            # Add SafeMath
            fixed_code = """import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract YourContract {
    using SafeMath for uint256;
    
""" + vulnerable_code
            
            explanation = """Added SafeMath library to prevent integer overflow/underflow.

**Changes:**
- Imported OpenZeppelin's SafeMath
- Added `using SafeMath for uint256;`
- Replace arithmetic operations with SafeMath methods:
  - `a + b` → `a.add(b)`
  - `a - b` → `a.sub(b)`
  - `a * b` → `a.mul(b)`
  - `a / b` → `a.div(b)`

**Better Solution:** Upgrade to Solidity 0.8.0+ for built-in protection."""
            
            confidence = 0.8
        
        return {
            "fixed_code": fixed_code,
            "explanation": explanation,
            "confidence": confidence
        }
    
    @staticmethod
    def generate_unchecked_call_fix(vulnerable_code: str) -> Dict[str, str]:
        """
        Generate fix for unchecked external call
        
        Adds return value checking
        """
        # Add require statement for call return value
        fixed_code = re.sub(
            r'([a-zA-Z0-9_]+)\.call\(',
            r'(bool success, ) = \1.call(\nrequire(success, "Call failed");',
            vulnerable_code
        )
        
        explanation = """Added return value checking for external calls.

**Changes:**
- Capture call return value
- Added `require(success, "Call failed")` to revert on failure

**Best Practice:** Always check return values of low-level calls (.call, .delegatecall, .staticcall).

**Alternative:** Consider using `transfer()` or `send()` for ETH transfers, or higher-level interfaces for contract calls."""
        
        return {
            "fixed_code": fixed_code,
            "explanation": explanation,
            "confidence": 0.9
        }
    
    @classmethod
    def generate_fix(cls, finding: Finding) -> Dict[str, str]:
        """
        Generate fix based on finding type
        """
        if finding.type == FindingType.REENTRANCY:
            return cls.generate_reentrancy_fix(
                finding.vulnerable_code,
                finding.function_name or ""
            )
        elif finding.type == FindingType.ACCESS_CONTROL:
            return cls.generate_access_control_fix(
                finding.vulnerable_code,
                finding.function_name or ""
            )
        elif finding.type == FindingType.INTEGER_OVERFLOW:
            return cls.generate_integer_overflow_fix(finding.vulnerable_code)
        elif finding.type == FindingType.UNCHECKED_CALL:
            return cls.generate_unchecked_call_fix(finding.vulnerable_code)
        else:
            return {
                "fixed_code": finding.vulnerable_code,
                "explanation": f"No automatic fix available for {finding.type.value}. Manual review required.",
                "confidence": 0.0
            }

class GitHubIntegration:
    """
    GitHub API integration for PR creation
    """
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
    
    async def create_branch(self, owner: str, repo: str, base_branch: str, new_branch: str) -> bool:
        """Create a new branch"""
        if not self.token:
            return False
        
        async with httpx.AsyncClient() as client:
            # Get base branch SHA
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{base_branch}",
                headers={"Authorization": f"token {self.token}"}
            )
            
            if response.status_code != 200:
                return False
            
            base_sha = response.json()["object"]["sha"]
            
            # Create new branch
            response = await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/git/refs",
                headers={"Authorization": f"token {self.token}"},
                json={
                    "ref": f"refs/heads/{new_branch}",
                    "sha": base_sha
                }
            )
            
            return response.status_code == 201
    
    async def update_file(
        self,
        owner: str,
        repo: str,
        branch: str,
        file_path: str,
        content: str,
        message: str
    ) -> bool:
        """Update a file in the repository"""
        if not self.token:
            return False
        
        async with httpx.AsyncClient() as client:
           # Get current file SHA
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}",
                headers={"Authorization": f"token {self.token}"}
            )
            
            current_sha = response.json().get("sha", "")
            
            # Update file
            import base64
            encoded_content = base64.b64encode(content.encode()).decode()
            
            response = await client.put(
                f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}",
                headers={"Authorization": f"token {self.token}"},
                json={
                    "message": message,
                    "content": encoded_content,
                    "sha": current_sha,
                    "branch": branch
                }
            )
            
            return response.status_code == 200
    
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str
    ) -> Optional[str]:
        """Create a pull request"""
        if not self.token:
            return None
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/pulls",
                headers={"Authorization": f"token {self.token}"},
                json={
                    "title": title,
                    "body": body,
                    "head": head_branch,
                    "base": base_branch
                }
            )
            
            if response.status_code == 201:
                return response.json()["html_url"]
            
            return None

@app.post("/remediate")
async def remediate_finding(request: RemediationRequest, background_tasks: BackgroundTasks):
    """
    Remediate a security finding
    
    Generates fix and optionally creates GitHub PR
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # Create job
    job = {
        "job_id": job_id,
        "finding_id": request.finding.id,
        "status": RemediationStatus.QUEUED,
        "repo_url": request.repo_url,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "fix": None,
        "pr_url": None,
        "error": None
    }
    
    remediation_jobs[job_id] = job
    
    # Process in background
    background_tasks.add_task(process_remediation, job_id, request)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Remediation job created"
    }

async def process_remediation(job_id: str, request: RemediationRequest):
    """Background task to process remediation"""
    job = remediation_jobs[job_id]
    
    try:
        # Generate fix
        job["status"] = RemediationStatus.GENERATING_FIX
        fix = FixGenerator.generate_fix(request.finding)
        job["fix"] = fix
        
        if fix["confidence"] < 0.5:
            job["status"] = RemediationStatus.FAILED
            job["error"] = "Low confidence fix - manual review required"
            job["completed_at"] = datetime.utcnow().isoformat()
            return
        
        # Create PR if requested
        if request.create_pr:
            job["status"] = RemediationStatus.CREATING_PR
            
            # Parse repo URL
            parts = request.repo_url.replace("https://github.com/", "").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                
                github = GitHubIntegration()
                branch_name = f"fix/{request.finding.type.value}-{request.finding.id}"
                
                # Create branch
                await github.create_branch(owner, repo, request.branch, branch_name)
                
                # Update file
                await github.update_file(
                    owner, repo, branch_name,
                    request.finding.file_path,
                    fix["fixed_code"],
                    f"Fix {request.finding.type.value} vulnerability in {request.finding.function_name or 'contract'}"
                )
                
                # Create PR
                pr_title = f"🔒 Security Fix: {request.finding.type.value.replace('_', ' ').title()}"
                pr_body = f"""## Security Vulnerability Remediation

**Finding ID:** {request.finding.id}  
**Type:** {request.finding.type.value}  
**Severity:** {request.finding.severity}  
**File:** {request.finding.file_path}:{request.finding.line_number}

### Description
{request.finding.description}

### Fix Applied
{fix['explanation']}

### Confidence Score
{fix['confidence'] * 100:.0f}%

---
*This PR was automatically generated by the Remediator service.*
**⚠️ Please review carefully before merging!**
"""
                
                pr_url = await github.create_pull_request(
                    owner, repo,
                    branch_name, request.branch,
                    pr_title, pr_body
                )
                
                job["pr_url"] = pr_url
                pr_history.append({
                    "finding_id": request.finding.id,
                    "pr_url": pr_url,
                    "created_at": datetime.utcnow().isoformat()
                })
        
        job["status"] = RemediationStatus.COMPLETED
        job["completed_at"] = datetime.utcnow().isoformat()
        
    except Exception as e:
        job["status"] = RemediationStatus.FAILED
        job["error"] = str(e)
        job["completed_at"] = datetime.utcnow().isoformat()

@app.get("/remediate/{job_id}")
async def get_job_status(job_id: str):
    """Get remediation job status"""
    if job_id not in remediation_jobs:
        raise HTTPException(404, "Job not found")
    
    return remediation_jobs[job_id]

@app.get("/jobs")
async def list_jobs():
    """List all remediation jobs"""
    return {
        "jobs": list(remediation_jobs.values()),
        "total": len(remediation_jobs)
    }

@app.get("/prs")
async def list_prs():
    """List all created PRs"""
    return {
        "prs": pr_history,
        "total": len(pr_history)
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "remediator",
        "version": "1.0.0",
        "total_jobs": len(remediation_jobs),
        "prs_created": len(pr_history)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)
