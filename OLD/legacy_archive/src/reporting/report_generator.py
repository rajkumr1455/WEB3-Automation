import logging
from typing import Dict, List, Any
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generates HTML audit reports from vulnerability findings.
    """
    
    def generate_html_report(self, 
                            contract_name: str,
                            source_code: str,
                            findings: List[Dict[str, Any]],
                            slither_results: List[Dict[str, Any]],
                            poc_code: str = "",
                            output_path: str = "data/reports") -> str:
        """
        Generates a comprehensive HTML audit report.
        """
        os.makedirs(output_path, exist_ok=True)
        
        # Parse findings if JSON string
        if isinstance(findings, str):
            try:
                findings = json.loads(findings)
                if isinstance(findings, dict) and "vulnerabilities" in findings:
                    findings = findings["vulnerabilities"]
            except:
                findings = []
        
        # Count by severity
        severity_counts = {"RED": 0, "YELLOW": 0, "BLUE": 0}
        for finding in findings:
            category = finding.get("category", "BLUE")
            severity_counts[category] = severity_counts.get(category, 0) + 1
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_filename = f"{contract_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_path = os.path.join(output_path, report_filename)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web3 Hunter Audit Report - {contract_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0e27; color: #e0e0e0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: #1a1f3a; border-radius: 12px; padding: 30px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }}
        h1 {{ color: #00d4ff; margin-bottom: 10px; font-size: 2.5em; }}
        .meta {{ color: #888; margin-bottom: 30px; font-size: 0.9em; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card.red {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .stat-card.yellow {{ background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333; }}
        .stat-card.blue {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .stat-number {{ font-size: 3em; font-weight: bold; }}
        .stat-label {{ font-size: 0.9em; opacity: 0.9; margin-top: 8px; }}
        .section {{ background: #252b4a; padding: 25px; border-radius: 8px; margin-bottom: 25px; }}
        .section h2 {{ color: #00d4ff; margin-bottom: 20px; font-size: 1.8em; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .finding {{ background: #1a1f3a; padding: 20px; border-left: 4px solid #667eea; margin-bottom: 15px; border-radius: 4px; }}
        .finding.RED {{ border-left-color: #f5576c; }}
        .finding.YELLOW {{ border-left-color: #fcb69f; }}
        .finding.BLUE {{ border-left-color: #00f2fe; }}
        .finding-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
        .finding-title {{ font-size: 1.3em; font-weight: 600; color: #fff; }}
        .badge {{ padding: 6px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 600; }}
        .badge.RED {{ background: #f5576c; color: white; }}
        .badge.YELLOW {{ background: #fcb69f; color: #333; }}
        .badge.BLUE {{ background: #00f2fe; color: #333; }}
        .finding-desc {{ line-height: 1.6; margin-bottom: 10px; color: #ccc; }}
        .finding-location {{ font-family: monospace; background: #0a0e27; padding: 8px; border-radius: 4px; font-size: 0.9em; color: #00d4ff; }}
        code {{ background: #0a0e27; padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; color: #00ff88; }}
        pre {{ background: #0a0e27; padding: 15px; border-radius: 4px; overflow-x: auto; font-size: 0.9em; line-height: 1.4; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Smart Contract Security Audit Report</h1>
        <div class="meta">
            <strong>Contract:</strong> {contract_name}<br>
            <strong>Generated:</strong> {timestamp}<br>
            <strong>Tool:</strong> Web3 Hunter v1.0
        </div>
        
        <div class="summary">
            <div class="stat-card red">
                <div class="stat-number">{severity_counts.get('RED', 0)}</div>
                <div class="stat-label">🔴 High Severity</div>
            </div>
            <div class="stat-card yellow">
                <div class="stat-number">{severity_counts.get('YELLOW', 0)}</div>
                <div class="stat-label">🟡 Config Issues</div>
            </div>
            <div class="stat-card blue">
                <div class="stat-number">{severity_counts.get('BLUE', 0)}</div>
                <div class="stat-label">🔵 Logical Risks</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(slither_results)}</div>
                <div class="stat-label">📊 Slither Detections</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Vulnerability Findings</h2>
"""
        
        if not findings:
            html_content += "<p>No vulnerabilities detected by LLM analysis.</p>"
        else:
            for finding in findings:
                category = finding.get("category", "BLUE")
                name = finding.get("name", "Unknown")
                desc = finding.get("description", "No description provided")
                location = finding.get("location", "Not specified")
                
                html_content += f"""
            <div class="finding {category}">
                <div class="finding-header">
                    <div class="finding-title">{name}</div>
                    <span class="badge {category}">{category}</span>
                </div>
                <div class="finding-desc">{desc}</div>
                <div class="finding-location">📍 Location: {location}</div>
            </div>
"""
        
        html_content += """
        </div>
"""
        
        if slither_results:
            html_content += """
        <div class="section">
            <h2>🔍 Static Analysis (Slither)</h2>
"""
            for result in slither_results[:10]:  # Limit to first 10
                check = result.get("check", "Unknown")
                impact = result.get("impact", "Unknown")
                desc = result.get("description", "No description")
                
                html_content += f"""
            <div class="finding">
                <div class="finding-header">
                    <div class="finding-title">{check}</div>
                    <span class="badge BLUE">{impact}</span>
                </div>
                <div class="finding-desc">{desc}</div>
            </div>
"""
            html_content += """
        </div>
"""
        
        if poc_code:
            html_content += f"""
        <div class="section">
            <h2>💣 Proof of Concept</h2>
            <pre><code>{poc_code}</code></pre>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {report_path}")
        return report_path
