"""
Static Analysis Agent
Slither, Mythril, Semgrep integration with AI-assisted analysis
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import httpx
import os
import logging
import subprocess
import json
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
ANALYSIS_COUNT = Counter('static_analysis_total', 'Total analyses')
FINDING_COUNT = Counter('static_findings_total', 'Total findings', ['severity'])

LLM_ROUTER_URL = os.getenv("LLM_ROUTER_URL", "http://llm-router:8000")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

app = FastAPI(title="Static Analysis Agent", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    """Request for static analysis"""
    scan_id: str
    contracts: List[Dict[str, Any]]
    source_code: Optional[Dict[str, str]] = None


class AnalysisResult(BaseModel):
    """Static analysis results"""
    scan_id: str
    slither_findings: List[Dict[str, Any]] = []
    mythril_findings: List[Dict[str, Any]] = []
    semgrep_findings: List[Dict[str, Any]] = []
    ai_summary: Optional[str] = None
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0


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


async def run_slither(contract_path: Path) -> List[Dict[str, Any]]:
    """Run Slither static analyzer"""
    try:
        logger.info(f"Running Slither on {contract_path}")
        
        result = subprocess.run(
            ["slither", str(contract_path), "--json", "-"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.stdout:
            data = json.loads(result.stdout)
            findings = []
            
            for detector in data.get("results", {}).get("detectors", []):
                findings.append({
                    "tool": "slither",
                    "check": detector.get("check"),
                    "impact": detector.get("impact"),
                    "confidence": detector.get("confidence"),
                    "description": detector.get("description"),
                    "elements": detector.get("elements", [])
                })
            
            return findings
        
    except subprocess.TimeoutExpired:
        logger.error("Slither timeout")
    except Exception as e:
        logger.error(f"Slither failed: {e}")
    
    return []


async def run_mythril(contract_path: Path) -> List[Dict[str, Any]]:
    """Run Mythril symbolic analyzer"""
    try:
        logger.info(f"Running Mythril on {contract_path}")
        
        result = subprocess.run(
            ["myth", "analyze", str(contract_path), "--output", "json", "--execution-timeout", "60"],
            capture_output=True,
            text=True,
            timeout=90
        )
        
        if result.stdout:
            data = json.loads(result.stdout)
            findings = []
            
            for issue in data.get("issues", []):
                findings.append({
                    "tool": "mythril",
                    "title": issue.get("title"),
                    "severity": issue.get("severity"),
                    "description": issue.get("description"),
                    "swc_id": issue.get("swc-id"),
                    "contract": issue.get("contract"),
                    "function": issue.get("function")
                })
            
            return findings
        
    except subprocess.TimeoutExpired:
        logger.error("Mythril timeout")
    except Exception as e:
        logger.error(f"Mythril failed: {e}")
    
    return []


async def run_semgrep(contract_path: Path, rules_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Run Semgrep with custom rules"""
    try:
        logger.info(f"Running Semgrep on {contract_path}")
        
        cmd = ["semgrep", "--json", "--config", "auto"]
        
        if rules_path and rules_path.exists():
            cmd = ["semgrep", "--json", "--config", str(rules_path)]
        
        cmd.append(str(contract_path))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.stdout:
            data = json.loads(result.stdout)
            findings = []
            
            for finding in data.get("results", []):
                findings.append({
                    "tool": "semgrep",
                    "check_id": finding.get("check_id"),
                    "severity": finding.get("extra", {}).get("severity", "INFO"),
                    "message": finding.get("extra", {}).get("message"),
                    "path": finding.get("path"),
                    "line": finding.get("start", {}).get("line"),
                    "code": finding.get("extra", {}).get("lines")
                })
            
            return findings
        
    except subprocess.TimeoutExpired:
        logger.error("Semgrep timeout")
    except Exception as e:
        logger.error(f"Semgrep failed: {e}")
    
    return []


async def generate_ai_summary(all_findings: List[Dict[str, Any]]) -> str:
    """Generate AI summary of findings"""
    if not all_findings:
        return "No security issues detected."
    
    # Prepare findings summary
    findings_text = "\n".join([
        f"- [{f.get('tool', 'unknown').upper()}] {f.get('impact', f.get('severity', 'UNKNOWN'))}: {f.get('description', f.get('message', 'No description'))}"
        for f in all_findings[:20]  # Limit to top 20
    ])
    
    prompt = f"""Analyze these static analysis findings and provide a concise security summary:

{findings_text}

Provide:
1. Most critical vulnerabilities (top 3)
2. Overall risk assessment
3. Recommended immediate actions

Keep it concise and actionable."""
    
    return await call_llm(
        "code_analysis",
        prompt,
        "You are a smart contract security auditor analyzing static analysis results."
    )


def categorize_findings(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    """Categorize findings by severity"""
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    for finding in findings:
        severity = finding.get("impact", finding.get("severity", "")).lower()
        
        if severity in ["critical", "high"]:
            counts["critical" if severity == "critical" else "high"] += 1
        elif severity in ["medium", "moderate"]:
            counts["medium"] += 1
        elif severity in ["low", "informational", "info"]:
            counts["low"] += 1
    
    return counts


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(request: AnalysisRequest):
    """Perform static analysis"""
    logger.info(f"Starting static analysis for scan: {request.scan_id}")
    
    result = AnalysisResult(scan_id=request.scan_id)
    all_findings = []
    
    try:
        # Create temporary directory for analysis
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Write contract source files
            for contract in request.contracts:
                if contract.get("source"):
                    file_name = contract.get("file", "contract.sol")
                    contract_path = tmpdir_path / Path(file_name).name
                    
                    with open(contract_path, 'w') as f:
                        f.write(contract["source"])
                    
                    # Run analyzers
                    logger.info(f"Analyzing {file_name}")
                    
                    # Slither
                    slither_findings = await run_slither(contract_path)
                    result.slither_findings.extend(slither_findings)
                    all_findings.extend(slither_findings)
                    
                    # Mythril (skip for very large contracts)
                    if len(contract["source"]) < 10000:
                        mythril_findings = await run_mythril(contract_path)
                        result.mythril_findings.extend(mythril_findings)
                        all_findings.extend(mythril_findings)
                    
                    # Semgrep
                    semgrep_findings = await run_semgrep(contract_path)
                    result.semgrep_findings.extend(semgrep_findings)
                    all_findings.extend(semgrep_findings)
        
        # Generate AI summary
        if all_findings:
            result.ai_summary = await generate_ai_summary(all_findings)
        
        # Categorize findings
        counts = categorize_findings(all_findings)
        result.total_issues = len(all_findings)
        result.critical_count = counts["critical"]
        result.high_count = counts["high"]
        result.medium_count = counts["medium"]
        result.low_count = counts["low"]
        
        logger.info(f"Analysis complete: {result.total_issues} issues found")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return result


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "static-agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
