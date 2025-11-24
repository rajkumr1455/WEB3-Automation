import subprocess
import json
import sys
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class Finding:
    tool: str
    vuln_type: str
    file: str
    line: int
    severity: str
    details: str

class StaticAnalyzer:
    def run_slither(self, target: str) -> List[Finding]:
        findings = []
        try:
            # Run slither and capture JSON output
            # Note: Slither requires the target to be a directory or file.
            cmd = ["slither", target, "--json", "-"]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            # Slither writes JSON to stdout, logs to stderr
            output = result.stdout.strip()
            if not output:
                return []

            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                # Sometimes Slither mixes text with JSON if not configured perfectly
                if "{" in output:
                    start = output.find("{")
                    try:
                        data = json.loads(output[start:])
                    except:
                        return []
                else:
                    return []

            if "results" in data and "detectors" in data["results"]:
                for d in data["results"]["detectors"]:
                    vuln_type = d.get("check", "Unknown")
                    severity = d.get("impact", "Medium")
                    desc = d.get("description", "")
                    
                    file_path = "Unknown"
                    line = 0
                    
                    if d.get("elements"):
                        for elem in d["elements"]:
                            if "source_mapping" in elem:
                                file_path = elem["source_mapping"].get("filename_relative", file_path)
                                lines = elem["source_mapping"].get("lines", [])
                                if lines:
                                    line = lines[0]
                                break
                    
                    findings.append(Finding(
                        tool="slither",
                        vuln_type=vuln_type,
                        file=file_path,
                        line=line,
                        severity=severity,
                        details=desc
                    ))
        except FileNotFoundError:
            print("Slither executable not found.", file=sys.stderr)
        except Exception as e:
            print(f"Error running Slither: {e}", file=sys.stderr)
            
        return findings

    def run_aderyn(self, target: str) -> List[Finding]:
        findings = []
        try:
            # Aderyn writes to a file by default or stdout with --stdout?
            # We'll try to run it and expect report.json
            cmd = ["aderyn", target, "--output", "report.json"] 
            subprocess.run(cmd, capture_output=True, text=True)
            
            if os.path.exists("report.json"):
                with open("report.json", "r") as f:
                    data = json.load(f)
                    
                # Aderyn JSON structure keys
                severities = {
                    "critical_issues": "Critical",
                    "high_issues": "High",
                    "medium_issues": "Medium",
                    "low_issues": "Low"
                }
                
                for key, severity in severities.items():
                    if key in data and isinstance(data[key], list):
                        for issue in data[key]:
                            title = issue.get("title", "Unknown Issue")
                            desc = issue.get("description", "")
                            
                            instances = issue.get("instances", [])
                            if instances:
                                for inst in instances:
                                    file_path = inst.get("contract_path", "Unknown")
                                    line = inst.get("line_no", 0)
                                    
                                    findings.append(Finding(
                                        tool="aderyn",
                                        vuln_type=title,
                                        file=file_path,
                                        line=line,
                                        severity=severity,
                                        details=desc
                                    ))
                            else:
                                findings.append(Finding(
                                    tool="aderyn",
                                    vuln_type=title,
                                    file="Unknown",
                                    line=0,
                                    severity=severity,
                                    details=desc
                                ))
                
                # Cleanup
                # os.remove("report.json") 
        except FileNotFoundError:
            print("Aderyn executable not found.", file=sys.stderr)
        except Exception as e:
            print(f"Error running Aderyn: {e}", file=sys.stderr)
            
        return findings

    def scan(self, target: str) -> List[Dict]:
        all_findings = []
        # print(f"Scanning {target} with Slither...", file=sys.stderr)
        all_findings.extend(self.run_slither(target))
        # print(f"Scanning {target} with Aderyn...", file=sys.stderr)
        all_findings.extend(self.run_aderyn(target))
        return [asdict(f) for f in all_findings]

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    analyzer = StaticAnalyzer()
    results = analyzer.scan(target_dir)
    print(json.dumps(results, indent=2))
