"""
Bug Bounty Report Generator
Creates professional, platform-ready vulnerability reports
"""
import os
from datetime import datetime
from typing import Dict, List, Optional
from src.database.models import db, Vulnerability, ScanResult, Evidence

class BountyReportGenerator:
    """Generate bug bounty platform-ready reports"""
    
    def __init__(self, output_dir: str = "reports/bounty"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Platform-specific templates
        self.platforms = {
            'immunefi': self._generate_immunefi_report,
            'hackerone': self._generate_hackerone_report,
            'code4rena': self._generate_code4rena_report,
            'generic': self._generate_generic_report
        }
    
    def generate_report(
        self,
        vulnerability_id: int,
        platform: str = 'generic',
        include_remediation: bool = True
    ) -> str:
        """
        Generate bug bounty report for specified platform
        
        Args:
            vulnerability_id: Vulnerability ID from database
            platform: Target platform (immunefi, hackerone, code4rena, generic)
            include_remediation: Include fix recommendations
        
        Returns:
            Path to generated report file
        """
        session = db.get_session()
        
        try:
            # Load vulnerability data
            vuln = session.query(Vulnerability).filter_by(id=vulnerability_id).first()
            
            if not vuln:
                raise ValueError(f"Vulnerability {vulnerability_id} not found")
            
            # Load related scan data
            scan = session.query(ScanResult).filter_by(id=vuln.scan_id).first()
            
            # Load evidence
            evidence_files = session.query(Evidence).filter_by(
                vulnerability_id=vulnerability_id
            ).all()
            
            # Get report generator for platform
            generator = self.platforms.get(platform, self._generate_generic_report)
            
            # Generate report
            report_content = generator(vuln, scan, evidence_files, include_remediation)
            
            # Save report
            filename = f"{platform}_{vuln.vuln_type.replace(' ', '_')}_{vulnerability_id}.md"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"✅ Bounty report generated: {filename}")
            return filepath
            
        finally:
            session.close()
    
    def _generate_generic_report(
        self,
        vuln: Vulnerability,
        scan: ScanResult,
        evidence: List[Evidence],
        include_remediation: bool
    ) -> str:
        """Generate generic bug bounty report"""
        
        impact = vuln.extra_data.get('impact', {}) if vuln.extra_data else {}
        
        report = f"""# {vuln.severity} Severity: {vuln.vuln_type}

## Summary

**Vulnerability Type**: {vuln.vuln_type}  
**Severity**: {vuln.severity}  
**CVSS Score**: {vuln.cvss_score or 'N/A'}  
**Confidence**: {vuln.ml_confidence * 100:.1f}% (ML-verified)  
**Contract**: {scan.contract_name}  
**Chain**: {scan.chain.upper()}  

{vuln.description}

---

## Impact Analysis

"""
        
        if impact:
            report += f"""
### Financial Impact
- **Funds at Risk**: ${impact.get('financial_impact', {}).get('funds_at_risk_usd', 0):,.2f}
- **Attack Cost**: ${impact.get('attack_cost', {}).get('cost_usd', 0):.2f}
- **Potential Profit**: ${impact.get('financial_impact', {}).get('potential_profit_usd', 0):,.2f}
- **ROI**: {impact.get('financial_impact', {}).get('profit_ratio', 0):.0f}x

### Exploitability
- **Difficulty**: {impact.get('difficulty', 'Medium')}
- **Attack Vector**: {impact.get('exploitability', 'Network')}
- **User Interaction**: Not required
- **Privileges Required**: None

"""
        
        report += f"""
---

## Proof of Concept

### Verification Status
"""
        
        if vuln.poc_verified:
            verification = vuln.extra_data.get('verification', {}) if vuln.extra_data else {}
            report += f"""
✅ **POC Verified with Foundry**

- **Test Status**: PASSED
- **Gas Used**: {verification.get('gas_used', 0):,}
- **Tests Passed**: {verification.get('test_results', {}).get('passed', 0)}
- **Tests Failed**: {verification.get('test_results', {}).get('failed', 0)}

"""
        
        if vuln.poc_file_path:
            report += f"""
### POC File
See attached Foundry test: `{os.path.basename(vuln.poc_file_path)}`

The exploit can be reproduced by:
```bash
forge test --match-path {vuln.poc_file_path} -vvv
```

"""
        
        # Add evidence
        if evidence:
            report += """
---

## Visual Evidence

"""
            for ev in evidence:
                report += f"### {ev.evidence_type.replace('_', ' ').title()}\n"
                report += f"![{ev.description}]({ev.file_path})\n\n"
        
        # Add vulnerable code snippet
        report += f"""
---

## Vulnerable Code

**Location**: Line {vuln.line_number or 'N/A'}

```solidity
{scan.source_code[:1000]}
...
```

"""
        
        # Remediation
        if include_remediation:
            remediation = self._generate_remediation(vuln.vuln_type)
            report += f"""
---

## Recommended Fix

{remediation}

"""
        
        # Footer
        report += f"""
---

## Disclosure Timeline

- **Discovered**: {vuln.detected_at.strftime('%Y-%m-%d %H:%M UTC')}
- **Verified**: {vuln.verified_at.strftime('%Y-%m-%d %H:%M UTC') if vuln.verified_at else 'N/A'}
- **Reported**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

---

*Report generated by Web3 Hunter ML-Enhanced Scanner*  
*Vulnerability ID: {vuln.id} | Scan ID: {scan.id}*
"""
        
        return report
    
    def _generate_immunefi_report(self, vuln, scan, evidence, include_remediation) -> str:
        """Generate Immunefi-formatted report"""
        # Immunefi prefers structured format
        base_report = self._generate_generic_report(vuln, scan, evidence, include_remediation)
        
        immunefi_header = f"""# Immunefi Bug Report

**Program**: {scan.contract_name}
**Network**: {scan.chain}
**Severity Assessment**: {vuln.severity}

---

"""
        return immunefi_header + base_report
    
    def _generate_hackerone_report(self, vuln, scan, evidence, include_remediation) -> str:
        """Generate HackerOne-formatted report"""
        base_report = self._generate_generic_report(vuln, scan, evidence, include_remediation)
        
        h1_header = f"""# HackerOne Vulnerability Report

**Asset**: {scan.contract_name} ({scan.chain})
**Weakness**: {vuln.vuln_type}
**Severity**: {vuln.severity}
**Priority**: {'P1' if vuln.severity == 'Critical' else 'P2' if vuln.severity == 'High' else 'P3'}

---

"""
        return h1_header + base_report
    
    def _generate_code4rena_report(self, vuln, scan, evidence, include_remediation) -> str:
        """Generate Code4rena-formatted report"""
        # Code4rena uses issue format
        report = f"""## [{vuln.severity.upper()}] {vuln.vuln_type} in {scan.contract_name}

### Impact
{vuln.description}

CVSS Score: {vuln.cvss_score or 'N/A'}

### Proof of Concept

"""
        
        if vuln.poc_file_path:
            with open(vuln.poc_file_path, 'r', encoding='utf-8') as f:
                poc_code = f.read()
            report += f"```solidity\n{poc_code}\n```\n\n"
        
        if include_remediation:
            remediation = self._generate_remediation(vuln.vuln_type)
            report += f"### Recommended Mitigation Steps\n\n{remediation}\n"
        
        return report
    
    def _generate_remediation(self, vuln_type: str) -> str:
        """Generate fix recommendations for vulnerability type"""
        
        remediations = {
            'Reentrancy': """
**Reentrancy Fix:**

1. **Use Checks-Effects-Interactions Pattern:**
   ```solidity
   function withdraw() public {
       uint amt = balances[msg.sender];
       balances[msg.sender] = 0;  // Update state BEFORE external call
       (bool s,) = msg.sender.call{value: amt}("");
       require(s, "Transfer failed");
   }
   ```

2. **Add ReentrancyGuard:**
   ```solidity
   import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
   
   contract Vault is ReentrancyGuard {
       function withdraw() public nonReentrant {
           // Safe from reentrancy
       }
   }
   ```

3. **Use pull payment pattern** instead of push
""",
            'Access Control': """
**Access Control Fix:**

1. **Add proper access modifiers:**
   ```solidity
   address public owner;
   
   modifier onlyOwner() {
       require(msg.sender == owner, "Not authorized");
       _;
   }
   
   function privilegedFunction() public onlyOwner {
       // Only owner can call
   }
   ```

2. **Use OpenZeppelin's Ownable:**
   ```solidity
   import "@openzeppelin/contracts/access/Ownable.sol";
   
   contract MyContract is Ownable {
       function privilegedFunction() public onlyOwner {
           // Protected
       }
   }
   ```
""",
            'Integer Overflow/Underflow': """
**Integer Overflow Fix:**

1. **Use Solidity ^0.8.0** (built-in overflow checks)
   
2. **Or use SafeMath for older versions:**
   ```solidity
   using SafeMath for uint256;
   
   function add(uint a, uint b) public pure returns (uint) {
       return a.add(b);  // Safe addition
   }
   ```
""",
        }
        
        return remediations.get(vuln_type, f"Implement security best practices for {vuln_type}.")


if __name__ == "__main__":
    # Test report generator
    gen = BountyReportGenerator()
    
    print("\n📄 Bug Bounty Report Generator Test")
    print("=" * 70)
    
    # Check if we have any vulnerabilities to generate reports for
    session = db.get_session()
    vuln = session.query(Vulnerability).first()
    session.close()
    
    if vuln:
        print(f"\nGenerating reports for vulnerability #{vuln.id}...")
        
        for platform in ['generic', 'immunefi', 'hackerone', 'code4rena']:
            try:
                filepath = gen.generate_report(vuln.id, platform=platform)
                print(f"  ✅ {platform}: {filepath}")
            except Exception as e:
                print(f"  ❌ {platform}: {e}")
    else:
        print("\n⚠️  No vulnerabilities found in database")
        print("   Run a scan first to generate reports")
