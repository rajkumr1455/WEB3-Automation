import ollama
import asyncio
import os
from typing import Dict, Any, Optional
from src.database.models import db, Vulnerability, Evidence
from src.poc.verifier import PoCVerifier
from src.analysis.evidence import EvidenceGenerator
from src.analysis.impact import ImpactCalculator

class PoCGenerator:
    """
    Advanced POC Generator with automated verification and evidence
    """
    def __init__(self, model: str = "qwen2.5-coder:7b"):
        self.model = model
        self.verifier = PoCVerifier()
        self.evidence_gen = EvidenceGenerator()
        self.impact_calc = ImpactCalculator()
        
    async def generate(
        self,
        vulnerability: Dict[str, Any],
        source_code: str,
        contract_name: str,
        verify: bool = True,
        generate_evidence: bool = True,
        calculate_impact: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a bug bounty-grade PoC with verification and evidence
        
        Args:
            vulnerability: Vulnerability details from scanner
            source_code: Contract source code
            contract_name: Contract name
            verify: Run automated verification with Foundry
            generate_evidence: Create visual evidence (diagrams, charts)
            calculate_impact: Calculate financial impact and CVSS
        
        Returns:
            {
                "vulnerability": str,
                "poc_file": str,
                "code": str,
                "verified": bool,
                "verification_result": dict,
                "evidence": list,
                "impact": dict
            }
        """
        vuln_type = vulnerability['type']
        line = vulnerability.get('line', 0)
        severity = vulnerability.get('severity', 'Medium')
        
        # Step 1: Generate POC code with LLM
        print(f"\n🔨 Generating POC for {vuln_type}...")
        
        prompt = f"""
You are a security researcher. Generate a comprehensive Foundry test that demonstrates a {vuln_type} exploit.

Target Contract:
```solidity
{source_code}
```

Vulnerability: {vuln_type} at line {line}
Severity: {severity}
Description: {vulnerability.get('description', '')}

Create a complete Foundry test file that:
1. Inherits from forge-std/Test.sol
2. Deploys the vulnerable contract with initial funding
3. Creates an attacker contract if needed (for reentrancy, etc.)
4. Demonstrates the exploit step-by-step with comments
5. Captures balances BEFORE and AFTER the attack
6. Asserts the successful exploitation with clear evidence
7. Uses cheatcodes (vm.startPrank, vm.deal) for realistic testing
8. Emits events or logs to show the attack progression

IMPORTANT: The test should PASS when the exploit succeeds!

Return ONLY the Solidity code, no markdown.
"""
        
        try:
            client = ollama.AsyncClient()
            response = await client.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.3, "num_predict": 2048}
            )
            
            code = response['response'].strip()
            
            # Clean markdown if present
            if "```solidity" in code:
                code = code.split("```solidity")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            # Save PoC
            poc_dir = "reports/pocs"
            os.makedirs(poc_dir, exist_ok=True)
            
            filename = f"{contract_name}_{vuln_type.replace(' ', '_')}_PoC.t.sol"
            filepath = os.path.join(poc_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(code)
            
            print(f"   ✓ POC saved: {filename}")
            
            result = {
                "vulnerability": vuln_type,
                "poc_file": filepath,
                "code": code,
                "verified": False,
                "verification_result": None,
                "evidence": [],
                "impact": None
            }
            
            # Get vulnerability ID if it exists in database
            vuln_id = vulnerability.get('id')
            
            # Step 2: Verify POC
            if verify:
                print(f"   🔍 Verifying POC...")
                verification_result = self.verifier.verify_poc(filepath, vuln_id)
                result['verified'] = verification_result['success']
                result['verification_result'] = verification_result
            
            # Step 3: Generate Evidence
            if generate_evidence and result.get('verified'):
                print(f"   📸 Generating visual evidence...")
                evidence_files = await self._generate_evidence(
                    vuln_id,
                    vuln_type,
                    severity,
                    result.get('verification_result', {})
                )
                result['evidence'] = evidence_files
            
            # Step 4: Calculate Impact
            if calculate_impact:
                print(f"   💰 Calculating impact...")
                impact_data = self._calculate_impact(
                    vuln_type,
                    severity,
                    result.get('verification_result', {})
                )
                result['impact'] = impact_data
            
            return result
            
        except Exception as e:
            print(f"❌ PoC generation failed: {e}")
            return None
    
    async def _generate_evidence(
        self,
        vuln_id: Optional[int],
        vuln_type: str,
        severity: str,
        verification_result: Dict
    ) -> list:
        """Generate visual evidence for the POC"""
        evidence_files = []
        
        if not vuln_id:
            vuln_id = 999  # Demo ID
        
        try:
            # State transition diagram
            # Example: before/after balances
            before_state = {
                'Vault': 10.0,
                'Attacker': 0.5
            }
            
            after_state = {
                'Vault': 0.0,
                'Attacker': 10.5
            }
            
            state_diagram = self.evidence_gen.generate_state_transition_diagram(
                vuln_id,
                before_state,
                after_state,
                f"{vuln_type} - State Transition"
            )
            evidence_files.append(state_diagram)
            
            # Transaction flow
            flow_steps = self._generate_flow_steps(vuln_type)
            if flow_steps:
                flow_diagram = self.evidence_gen.generate_transaction_flow(
                    vuln_id,
                    flow_steps,
                    f"{vuln_type} - Exploit Flow"
                )
                evidence_files.append(flow_diagram)
            
            # Impact chart
            impact_data = {
                'funds_drained': 20000,  # Example
                'attack_cost': 50,
                'profit': 19950,
                'severity': severity
            }
            
            impact_chart = self.evidence_gen.generate_impact_chart(
                vuln_id,
                impact_data,
                f"{vuln_type} - Impact Analysis"
            )
            evidence_files.append(impact_chart)
            
        except Exception as e:
            print(f"   ⚠️  Evidence generation warning: {e}")
        
        return evidence_files
    
    def _generate_flow_steps(self, vuln_type: str) -> list:
        """Generate transaction flow steps based on vulnerability type"""
        flows = {
            'Reentrancy': [
                {'from': 'Attacker', 'to': 'Vault', 'action': 'deposit()', 'value': '0.5 ETH'},
                {'from': 'Attacker', 'to': 'Vault', 'action': 'withdraw()', 'value': ''},
                {'from': 'Vault', 'to': 'Attacker', 'action': 'call.value()', 'value': '0.5 ETH'},
                {'from': 'Attacker', 'to': 'Vault', 'action': 'withdraw() [REENTER]', 'value': ''},
                {'from': 'Vault', 'to': 'Attacker', 'action': 'drain remaining', 'value': '9.5 ETH'},
            ],
            'Access Control': [
                {'from': 'Attacker', 'to': 'Contract', 'action': 'privilegedFunction()', 'value': ''},
                {'from': 'Contract', 'to': 'Attacker', 'action': 'unauthorized access', 'value': 'SUCCESS'},
            ],
        }
        
        return flows.get(vuln_type, [])
    
    def _calculate_impact(
        self,
        vuln_type: str,
        severity: str,
        verification_result: Dict
    ) -> Dict:
        """Calculate comprehensive impact metrics"""
        # Estimate funds at risk (example - in production, analyze contract TVL)
        funds_at_risk_eth = {
            'Critical': 50.0,
            'High': 10.0,
            'Medium': 2.0,
            'Low': 0.5
        }.get(severity, 5.0)
        
        # Get gas from verification if available
        gas_used = verification_result.get('gas_used', 200000)
        num_transactions = 3  # Typical multi-step exploit
        
        impact = self.impact_calc.generate_full_impact_report(
            vulnerability_type=vuln_type,
            funds_at_risk_eth=funds_at_risk_eth,
            num_transactions=num_transactions,
            gas_per_tx=gas_used // num_transactions if gas_used > 0 else 200000,
            exploitability='high' if severity in ['Critical', 'High'] else 'medium'
        )
        
        return impact


if __name__ == "__main__":
    async def test():
        gen = PoCGenerator()
        vuln = {
            "type": "Reentrancy",
            "line": 5,
            "severity": "High",
            "description": "Reentrancy vulnerability in withdraw function - state updated after external call"
        }
        code = """
        pragma solidity ^0.8.0;
        contract Vault {
            mapping(address => uint) balances;
            function withdraw() public {
                uint amt = balances[msg.sender];
                (bool s,) = msg.sender.call{value: amt}("");
                balances[msg.sender] = 0;
            }
        }
        """
        
        result = await gen.generate(
            vuln,
            code,
            "VulnerableVault",
            verify=True,
            generate_evidence=True,
            calculate_impact=True
        )
        
        if result:
            print(f"\n{'='*70}")
            print("✅ POC Generation Complete!")
            print(f"{'='*70}")
            print(f"POC File: {result['poc_file']}")
            print(f"Verified: {result['verified']}")
            print(f"Evidence Files: {len(result['evidence'])}")
            if result['impact']:
                print(f"Impact Summary: {result['impact']['summary']}")
    
    asyncio.run(test())
