import asyncio
import os
from datetime import datetime
from typing import Dict, Any
from llm_service import LLMService
from poc_generator import PoCGenerator
from report_generator import ReportGenerator

class UnifiedScanner:
    """
    Complete contract security scanner integrating:
    - LLM Analysis with RAG
    - PoC Generation
    - Comprehensive Reporting
    """
    def __init__(self, chain: str = "eth"):
        self.chain = chain
        self.llm = LLMService(use_rag=True)
        self.poc_gen = PoCGenerator()
        self.report_gen = ReportGenerator()
        
    async def scan_contract(self, source_code: str, contract_name: str = "Contract") -> Dict[str, Any]:
        """
        Complete scan workflow
        """
        print(f"[*] Scanning {contract_name}...")
        
        # Step 1: LLM Analysis with RAG
        print("  [>] Running AI analysis...")
        analysis = await self.llm.analyze_code(source_code)
        
        if analysis.get('error'):
            return {"error": analysis['error']}
        
        vulnerabilities = analysis.get('vulnerabilities', [])
        print(f"  [>] Found {len(vulnerabilities)} vulnerabilities")
        
        # Step 2: Generate PoCs for High/Critical vulns
        pocs = []
        for vuln in vulnerabilities:
            if vuln['severity'] in ['High', 'Critical']:
                print(f"  [>] Generating PoC for {vuln['type']}...")
                poc = await self.poc_gen.generate(vuln, source_code, contract_name)
                if poc:
                    pocs.append(poc)
        
        # Step 3: Generate Report
        print("  [>] Generating report...")
        report = self.report_gen.create_report(
            contract_name=contract_name,
            chain=self.chain,
            source_code=source_code,
            vulnerabilities=vulnerabilities,
            pocs=pocs,
            summary=analysis.get('summary', '')
        )
        
        return {
            "contract_name": contract_name,
            "chain": self.chain,
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": vulnerabilities,
            "pocs": pocs,
            "report_path": report['markdown_path'],
            "summary": analysis.get('summary', '')
        }

if __name__ == "__main__":
    async def test():
        scanner = UnifiedScanner(chain="bss")
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
        result = await scanner.scan_contract(code, "VulnerableVault")
        print("\\n[+] Scan Complete!")
        print(f"Report: {result['report_path']}")
    
    asyncio.run(test())
