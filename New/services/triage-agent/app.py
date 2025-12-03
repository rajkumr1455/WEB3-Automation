"""
Triage Agent
Multi-tier vulnerability classification using Mistral -> DeepSeek-R1 -> Claude
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import httpx
import os
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Triage Agent", version="1.0.0")
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

# Severity mappings for bug bounty platforms
IMMUNEFI_SEVERITY = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "info": "Informational"
}

HACKENPROOF_SEVERITY = {
    "critical": "P1 - Critical",
    "high": "P2 - High",
    "medium": "P3 - Medium",
    "low": "P4 - Low",
    "info": "P5 - Informational"
}


class TriageRequest(BaseModel):
    """Request for vulnerability triage"""
    scan_id: str
    findings: Dict[str, Any]


class VulnerabilityReport(BaseModel):
    """Individual vulnerability report"""
    title: str
    severity: str
    confidence: str
    description: str
    impact: str
    recommendation: str
    reproduction_steps: Optional[List[str]] = None
    immunefi_severity: str
    hackenproof_severity: str
    cvss_score: Optional[float] = None


class TriageResult(BaseModel):
    """Triage results"""
    scan_id: str
    vulnerabilities: List[VulnerabilityReport] = []
    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    triage_summary: Optional[str] = None


async def call_llm(task_type: str, prompt: str, system_prompt: Optional[str] = None) -> str:
    """Call LLM Router"""
    async with httpx.AsyncClient(timeout=300) as client:
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


async def tier1_fast_triage(findings: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Tier 1: Fast triage using Mistral"""
    logger.info("Tier 1: Fast triage with Mistral")
    
    # Collect all findings
    all_findings = []
    
    for source, data in findings.items():
        if isinstance(data, dict):
            if source == "static":
                all_findings.extend(data.get("slither_findings", []))
                all_findings.extend(data.get("mythril_findings", []))
                all_findings.extend(data.get("semgrep_findings", []))
            elif source == "fuzzing":
                for result in data.get("foundry_results", []):
                    for test in result.get("tests", []):
                        if test.get("status") == "Failure":
                            all_findings.append({
                                "source": "fuzzing",
                                "test": test.get("test"),
                                "reason": test.get("reason")
                            })
            elif source == "monitoring":
                all_findings.extend(data.get("mempool_anomalies", []))
                all_findings.extend(data.get("oracle_deviations", []))
    
    # Quick classification
    triaged = []
    for finding in all_findings[:50]:  # Limit to top 50
        finding_text = json.dumps(finding, indent=2)
        
        prompt = f"""Quickly classify this security finding:

{finding_text}

Respond with ONLY a JSON object:
{{
  "is_vulnerability": true/false,
  "severity": "critical/high/medium/low/info",
  "confidence": "high/medium/low"
}}"""
        
        try:
            response = await call_llm(
                "fast_triage",
                prompt,
                "You are a security analyst doing quick triage."
            )
            
            # Parse JSON response
            classification = json.loads(response.strip())
            
            if classification.get("is_vulnerability"):
                triaged.append({
                    "finding": finding,
                    "tier1_classification": classification
                })
        except:
            # Skip if parsing fails
            continue
    
    logger.info(f"Tier 1 complete: {len(triaged)} potential vulnerabilities")
    return triaged


async def tier2_deep_reasoning(triaged_findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Tier 2: Deep reasoning using DeepSeek-R1"""
    logger.info("Tier 2: Deep reasoning with DeepSeek-R1")
    
    analyzed = []
    
    for item in triaged_findings[:20]:  # Limit to top 20
        finding = item["finding"]
        tier1 = item["tier1_classification"]
        
        # Skip low severity from tier 1
        if tier1.get("severity") in ["low", "info"]:
            continue
        
        finding_text = json.dumps(finding, indent=2)
        
        prompt = f"""Perform deep security analysis of this finding:

{finding_text}

Initial classification: {tier1.get('severity')} severity

Analyze:
1. Root cause
2. Exploitability
3. Real-world impact
4. Attack scenarios
5. Recommended fixes

Provide detailed technical analysis."""
        
        try:
            analysis = await call_llm(
                "smart_contract_analysis",
                prompt,
                "You are an expert smart contract security auditor performing deep analysis."
            )
            
            analyzed.append({
                "finding": finding,
                "tier1": tier1,
                "tier2_analysis": analysis
            })
        except Exception as e:
            logger.error(f"Tier 2 analysis failed: {e}")
            continue
    
    logger.info(f"Tier 2 complete: {len(analyzed)} analyzed")
    return analyzed


async def tier3_final_classification(analyzed_findings: List[Dict[str, Any]]) -> List[VulnerabilityReport]:
    """Tier 3: Final classification using Claude"""
    logger.info("Tier 3: Final classification with Claude")
    
    vulnerabilities = []
    
    for item in analyzed_findings[:10]:  # Limit to top 10
        finding = item["finding"]
        tier2_analysis = item["tier2_analysis"]
        
        prompt = f"""Create a professional vulnerability report for this finding:

FINDING:
{json.dumps(finding, indent=2)}

DEEP ANALYSIS:
{tier2_analysis}

Generate a structured vulnerability report with:
1. Title (concise, descriptive)
2. Severity (critical/high/medium/low)
3. Confidence (high/medium/low)
4. Description
5. Impact
6. Recommendation
7. Safe reproduction steps (no actual exploitation)
8. CVSS score estimate

Respond with ONLY a JSON object matching this structure:
{{
  "title": "...",
  "severity": "...",
  "confidence": "...",
  "description": "...",
  "impact": "...",
  "recommendation": "...",
  "reproduction_steps": ["step1", "step2"],
  "cvss_score": 7.5
}}"""
        
        try:
            response = await call_llm(
                "final_report",
                prompt,
                "You are a professional security researcher writing bug bounty reports."
            )
            
            # Parse JSON response
            report_data = json.loads(response.strip())
            
            severity = report_data.get("severity", "medium").lower()
            
            vulnerability = VulnerabilityReport(
                title=report_data.get("title", "Untitled Vulnerability"),
                severity=severity,
                confidence=report_data.get("confidence", "medium"),
                description=report_data.get("description", ""),
                impact=report_data.get("impact", ""),
                recommendation=report_data.get("recommendation", ""),
                reproduction_steps=report_data.get("reproduction_steps"),
                immunefi_severity=IMMUNEFI_SEVERITY.get(severity, "Low"),
                hackenproof_severity=HACKENPROOF_SEVERITY.get(severity, "P4 - Low"),
                cvss_score=report_data.get("cvss_score")
            )
            
            vulnerabilities.append(vulnerability)
            
        except Exception as e:
            logger.error(f"Tier 3 classification failed: {e}")
            continue
    
    logger.info(f"Tier 3 complete: {len(vulnerabilities)} final reports")
    return vulnerabilities


@app.post("/triage", response_model=TriageResult)
async def triage(request: TriageRequest):
    """Perform multi-tier triage"""
    logger.info(f"Starting triage for scan: {request.scan_id}")
    
    result = TriageResult(scan_id=request.scan_id)
    
    try:
        # Tier 1: Fast triage
        triaged = await tier1_fast_triage(request.findings)
        
        if not triaged:
            logger.info("No vulnerabilities found in tier 1")
            result.triage_summary = "No significant vulnerabilities detected."
            return result
        
        # Tier 2: Deep reasoning
        analyzed = await tier2_deep_reasoning(triaged)
        
        if not analyzed:
            logger.info("No vulnerabilities passed tier 2")
            result.triage_summary = "Initial findings were false positives."
            return result
        
        # Tier 3: Final classification
        result.vulnerabilities = await tier3_final_classification(analyzed)
        
        # Count by severity
        for vuln in result.vulnerabilities:
            if vuln.severity == "critical":
                result.critical_count += 1
            elif vuln.severity == "high":
                result.high_count += 1
            elif vuln.severity == "medium":
                result.medium_count += 1
            elif vuln.severity == "low":
                result.low_count += 1
        
        result.total_vulnerabilities = len(result.vulnerabilities)
        
        # Generate summary
        result.triage_summary = f"""Triage complete: {result.total_vulnerabilities} vulnerabilities confirmed.
- Critical: {result.critical_count}
- High: {result.high_count}
- Medium: {result.medium_count}
- Low: {result.low_count}"""
        
        logger.info(f"Triage complete: {result.total_vulnerabilities} vulnerabilities")
        
    except Exception as e:
        logger.error(f"Triage failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return result


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "triage-agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
