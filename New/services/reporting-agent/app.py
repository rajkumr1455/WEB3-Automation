"""
Reporting Agent
Generate reports for Immunefi, HackenProof, GitHub, and notifications
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import httpx
import os
import logging
import json
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from github import Github
from slack_sdk.webhook import WebhookClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Reporting Agent", version="1.0.0")
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configuration
LLM_ROUTER_URL = os.getenv("LLM_ROUTER_URL", "http://llm-router:8000")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Initialize Jinja2
template_env = Environment(loader=FileSystemLoader("/app/templates"))


class ReportRequest(BaseModel):
    """Request for report generation"""
    scan_id: str
    target_url: str
    contract_address: Optional[str] = None
    findings: Dict[str, Any]


class ReportResult(BaseModel):
    """Report generation results"""
    scan_id: str
    immunefi_report_path: Optional[str] = None
    hackenproof_report_path: Optional[str] = None
    json_report_path: Optional[str] = None
    github_issue_url: Optional[str] = None
    slack_notified: bool = False


def generate_immunefi_report(scan_id: str, target_url: str, contract_address: Optional[str], 
                             vulnerabilities: List[Dict[str, Any]]) -> str:
    """Generate Immunefi-formatted report"""
    template = template_env.get_template("immunefi_template.md")
    
    report = template.render(
        scan_id=scan_id,
        target_url=target_url,
        contract_address=contract_address,
        vulnerabilities=vulnerabilities,
        timestamp=datetime.now().isoformat()
    )
    
    # Save report
    report_path = f"/app/reports/{scan_id}_immunefi.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    return report_path


def generate_hackenproof_report(scan_id: str, target_url: str, contract_address: Optional[str],
                                vulnerabilities: List[Dict[str, Any]]) -> str:
    """Generate HackenProof-formatted report"""
    template = template_env.get_template("hackenproof_template.md")
    
    report = template.render(
        scan_id=scan_id,
        target_url=target_url,
        contract_address=contract_address,
        vulnerabilities=vulnerabilities,
        timestamp=datetime.now().isoformat()
    )
    
    # Save report
    report_path = f"/app/reports/{scan_id}_hackenproof.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    return report_path


def generate_json_report(scan_id: str, target_url: str, contract_address: Optional[str],
                        findings: Dict[str, Any]) -> str:
    """Generate JSON report"""
    report = {
        "scan_id": scan_id,
        "target_url": target_url,
        "contract_address": contract_address,
        "timestamp": datetime.now().isoformat(),
        "findings": findings
    }
    
    # Save report
    report_path = f"/app/reports/{scan_id}_full.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report_path


async def create_github_issue(scan_id: str, target_url: str, vulnerabilities: List[Dict[str, Any]]) -> Optional[str]:
    """Create private GitHub issue"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        logger.warning("GitHub not configured")
        return None
    
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        # Create issue title
        critical_count = len([v for v in vulnerabilities if v.get("severity") == "critical"])
        high_count = len([v for v in vulnerabilities if v.get("severity") == "high"])
        
        title = f"[{scan_id}] Security Scan: {critical_count} Critical, {high_count} High"
        
        # Create issue body
        body = f"""# Security Scan Results

**Target:** {target_url}
**Scan ID:** {scan_id}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

Total vulnerabilities: {len(vulnerabilities)}
- Critical: {critical_count}
- High: {high_count}

## Vulnerabilities

"""
        
        for i, vuln in enumerate(vulnerabilities[:10], 1):  # Limit to top 10
            body += f"""
### {i}. {vuln.get('title', 'Untitled')}

**Severity:** {vuln.get('severity', 'unknown').upper()}
**Confidence:** {vuln.get('confidence', 'unknown')}

{vuln.get('description', 'No description')}

**Impact:** {vuln.get('impact', 'Unknown')}

**Recommendation:** {vuln.get('recommendation', 'None provided')}

---
"""
        
        # Create issue
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=["security", "automated-scan"]
        )
        
        logger.info(f"Created GitHub issue: {issue.html_url}")
        return issue.html_url
        
    except Exception as e:
        logger.error(f"Failed to create GitHub issue: {e}")
        return None


async def send_slack_notification(scan_id: str, target_url: str, vulnerabilities: List[Dict[str, Any]]) -> bool:
    """Send Slack notification"""
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack webhook not configured")
        return False
    
    try:
        webhook = WebhookClient(SLACK_WEBHOOK_URL)
        
        critical_count = len([v for v in vulnerabilities if v.get("severity") == "critical"])
        high_count = len([v for v in vulnerabilities if v.get("severity") == "high"])
        
        message = {
            "text": f"🔒 Security Scan Complete: {scan_id}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔒 Web3 Security Scan Complete"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Target:*\n{target_url}"},
                        {"type": "mrkdwn", "text": f"*Scan ID:*\n{scan_id}"},
                        {"type": "mrkdwn", "text": f"*Critical:*\n{critical_count}"},
                        {"type": "mrkdwn", "text": f"*High:*\n{high_count}"}
                    ]
                }
            ]
        }
        
        if critical_count > 0:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠️ *{critical_count} CRITICAL vulnerabilities detected!*"
                }
            })
        
        response = webhook.send(**message)
        
        logger.info(f"Slack notification sent: {response.status_code}")
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False


@app.post("/generate", response_model=ReportResult)
async def generate_report(request: ReportRequest):
    """Generate reports and notifications"""
    logger.info(f"Generating reports for scan: {request.scan_id}")
    
    result = ReportResult(scan_id=request.scan_id)
    
    try:
        # Extract vulnerabilities from triage results
        triage_data = request.findings.get("triage", {})
        vulnerabilities = triage_data.get("vulnerabilities", [])
        
        if not vulnerabilities:
            logger.info("No vulnerabilities to report")
            return result
        
        # Convert Pydantic models to dicts if needed
        if vulnerabilities and hasattr(vulnerabilities[0], 'dict'):
            vulnerabilities = [v.dict() for v in vulnerabilities]
        
        # Generate Immunefi report
        result.immunefi_report_path = generate_immunefi_report(
            request.scan_id,
            request.target_url,
            request.contract_address,
            vulnerabilities
        )
        
        # Generate HackenProof report
        result.hackenproof_report_path = generate_hackenproof_report(
            request.scan_id,
            request.target_url,
            request.contract_address,
            vulnerabilities
        )
        
        # Generate JSON report
        result.json_report_path = generate_json_report(
            request.scan_id,
            request.target_url,
            request.contract_address,
            request.findings
        )
        
        # Create GitHub issue
        result.github_issue_url = await create_github_issue(
            request.scan_id,
            request.target_url,
            vulnerabilities
        )
        
        # Send Slack notification
        result.slack_notified = await send_slack_notification(
            request.scan_id,
            request.target_url,
            vulnerabilities
        )
        
        logger.info(f"Reports generated successfully for {request.scan_id}")
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return result


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "reporting-agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
