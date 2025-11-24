import sys
import os
import json
from scanner_core import StaticAnalyzer
from ai_triage import analyze_finding
from verification_core import verify_finding

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    
    analyzer = StaticAnalyzer()
    findings = analyzer.scan(target)
    
    confirmed_findings = []
    
    print(f"Found {len(findings)} raw findings. Analyzing with AI...", file=sys.stderr)
    
    for finding in findings:
        file_path = finding['file']
        # Resolve file path relative to target or absolute
        if target == ".":
            full_path = file_path
        else:
            full_path = os.path.join(target, file_path)
        
        source_code = ""
        if os.path.exists(full_path) and os.path.isfile(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
            except Exception as e:
                print(f"Could not read {full_path}: {e}", file=sys.stderr)
        
        if source_code:
            # AI Triage
            result = analyze_finding(finding, source_code)
            
            if result.get('is_valid', True): 
                finding['ai_analysis'] = result
                
                # Dynamic Verification for High/Critical issues
                if finding['severity'] in ["High", "Critical"]:
                    print(f"Attempting dynamic verification for {finding['vuln_type']}...", file=sys.stderr)
                    ver_result = verify_finding(finding, source_code)
                    finding['verification'] = ver_result
                
                confirmed_findings.append(finding)
            else:
                print(f"False positive discarded: {finding['vuln_type']} in {finding['file']}", file=sys.stderr)
        else:
            finding['ai_analysis'] = {"reasoning": "Source code not found for analysis"}
            confirmed_findings.append(finding)
            
    # Generate Markdown
    print("# Audit Report")
    print(f"**Total Confirmed Findings:** {len(confirmed_findings)}\n")
    
    for f in confirmed_findings:
        severity_icon = "\U0001F534" if f['severity'] in ["High", "Critical"] else "\U0001F7E0"
        print(f"### {severity_icon} {f['vuln_type']} ({f['severity']})")
        print(f"- **File:** `{f['file']}` (Line {f['line']})")
        print(f"- **Tool:** {f['tool']}")
        print(f"- **Details:** {f['details']}")
        
        if 'ai_analysis' in f:
            confidence = f['ai_analysis'].get('confidence', 0)
            print(f"- **AI Confidence:** {confidence}")
            print(f"- **AI Reasoning:** {f['ai_analysis'].get('reasoning')}")
            
        if 'verification' in f:
            ver = f['verification']
            status_icon = "\u2705" if ver['verified'] else "\u274C"
            print(f"- **Dynamic Verification:** {status_icon}")
            if ver.get('test_file'):
                print(f"  - Test File: `{ver['test_file']}`")
        
        print("\n---")

if __name__ == "__main__":
    main()
