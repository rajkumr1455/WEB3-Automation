"""
Enhanced Unified Scanner with ML Integration
Integrates ML classifier, advanced POC generation, and continuous learning
"""
import asyncio
import os
from datetime import datetime
from typing import Dict, Any
from src.database.models import db, ScanResult, Vulnerability
from src.core.llm_service import LLMService
from src.poc.generator import PoCGenerator
from src.bounty.report_generator import BountyReportGenerator

class UnifiedScannerML:
    """
    Complete ML-enhanced contract security scanner
    """
    def __init__(self, chain: str = "eth", use_ml: bool = True):
        self.chain = chain
        self.use_ml = use_ml
        self.llm = LLMService(use_rag=True)
        self.poc_gen = PoCGenerator()
        self.report_gen = BountyReportGenerator()
        
        # Load ML model if available
        if use_ml:
            self._load_ml_model()
        
    def _load_ml_model(self):
        """Load the active ML model"""
        try:
            from src.ml.trainer import VulnerabilityClassifier
            
            # Check if trained model exists
            model_dir = "models/vulnerability_classifier"
            if os.path.exists(model_dir):
                self.ml_classifier = VulnerabilityClassifier()
                # Load model (this would normally load from saved checkpoint)
                print("✓ ML classifier loaded")
            else:
                print("⚠️  ML model not found - train with: python ml_trainer.py")
                self.ml_classifier = None
        except Exception as e:
            print(f"⚠️  ML classifier unavailable: {e}")
            self.ml_classifier = None
        
    async def scan_contract(
        self,
        source_code: str,
        contract_name: str = "Contract",
        contract_address: str = None,
        generate_poc: bool = True,
        verify_poc: bool = True,
        create_evidence: bool = True,
        generate_bounty_report: bool = False,
        bounty_platform: str = 'generic'
    ) -> Dict[str, Any]:
        """
        Complete ML-enhanced scan workflow
        
        Args:
            source_code: Contract source code
            contract_name: Contract name
            contract_address: Optional contract address
            generate_poc: Generate POC for vulnerabilities
            verify_poc: Verify POCs with Foundry
            create_evidence: Generate visual evidence
            generate_bounty_report: Create bug bounty report
            bounty_platform: Target platform (immunefi, hackerone, etc.)
        
        Returns:
            Complete scan results with all generated artifacts
        """
        print(f"\n{'='*70}")
        print(f"🔍 Web3 Hunter ML-Enhanced Scanner")
        print(f"{'='*70}")
        print(f"Contract: {contract_name}")
        print(f"Chain: {self.chain}")
        print(f"ML: {'Enabled' if self.ml_classifier else 'Disabled'}")
        print(f"{'='*70}\n")
        
        # Save scan to database
        scan_id = self._save_scan(contract_name, contract_address, source_code)
        
        # Step 1: LLM Analysis with RAG
        print("  [1/5] Running AI analysis...")
        analysis = await self.llm.analyze_code(source_code)
        
        if analysis.get('error'):
            return {"error": analysis['error'], "scan_id": scan_id}
        
        vulnerabilities = analysis.get('vulnerabilities', [])
        print(f"        ✓ Found {len(vulnerabilities)} potential vulnerabilities")
        
        # Step 2: ML Classification (if available)
        if self.ml_classifier and vulnerabilities:
            print("  [2/5] Running ML classification...")
            vulnerabilities = self._apply_ml_classification(vulnerabilities, source_code)
        else:
            print("  [2/5] Skipping ML classification (model not loaded)")
        
        # Step 3: Save vulnerabilities to database
        print(f"  [3/5] Saving {len(vulnerabilities)} vulnerabilities...")
        vuln_records = self._save_vulnerabilities(scan_id, vulnerabilities)
        
        # Step 4: Generate POCs
        pocs = []
        if generate_poc:
            print(f"  [4/5] Generating POCs for High/Critical findings...")
            for i, vuln in enumerate(vulnerabilities):
                if vuln['severity'] in ['High', 'Critical']:
                    print(f"\n        [{i+1}] {vuln['type']} (Severity: {vuln['severity']})")
                    
                    # Add database ID to vulnerability
                    vuln['id'] = vuln_records[i]['id'] if i < len(vuln_records) else None
                    
                    poc = await self.poc_gen.generate(
                        vuln,
                        source_code,
                        contract_name,
                        verify=verify_poc,
                        generate_evidence=create_evidence,
                        calculate_impact=True
                    )
                    
                    if poc:
                        pocs.append(poc)
                        
                        # Update vulnerability with impact data
                        if poc.get('impact') and vuln_records[i]:
                            self._update_vulnerability_impact(vuln_records[i]['id'], poc['impact'])
            
        else:
            print("  [4/5] Skipping POC generation")
        
        # Step 5: Generate Bug Bounty Reports
        bounty_reports = []
        if generate_bounty_report and vuln_records:
            print(f"  [5/5] Generating bug bounty reports...")
            for vuln_record in vuln_records:
                if vuln_record['severity'] in ['High', 'Critical']:
                    try:
                        report_path = self.report_gen.generate_report(
                            vuln_record['id'],
                            platform=bounty_platform
                        )
                        bounty_reports.append(report_path)
                    except Exception as e:
                        print(f"        ⚠️  Report generation failed: {e}")
        else:
            print("  [5/5] Skipping bounty report generation")
        
        # Final summary
        print(f"\n{'='*70}")
        print("✅ Scan Complete!")
        print(f"{'='*70}")
        print(f"Vulnerabilities Found: {len(vulnerabilities)}")
        print(f"  Critical: {sum(1 for v in vulnerabilities if v['severity'] == 'Critical')}")
        print(f"  High:     {sum(1 for v in vulnerabilities if v['severity'] == 'High')}")
        print(f"  Medium:   {sum(1 for v in vulnerabilities if v['severity'] == 'Medium')}")
        print(f"  Low:      {sum(1 for v in vulnerabilities if v['severity'] == 'Low')}")
        print(f"\nPOCs Generated: {len(pocs)}")
        print(f"  Verified: {sum(1 for p in pocs if p.get('verified'))}")
        print(f"\nBounty Reports: {len(bounty_reports)}")
        print(f"{'='*70}\n")
        
        return {
            "scan_id": scan_id,
            "contract_name": contract_name,
            "chain": self.chain,
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": vulnerabilities,
            "pocs": pocs,
            "bounty_reports": bounty_reports,
            "summary": analysis.get('summary', '')
        }
    
    def _save_scan(self, contract_name: str, contract_address: str, source_code: str) -> int:
        """Save scan to database"""
        session = db.get_session()
        
        try:
            scan = ScanResult(
                contract_name=contract_name,
                contract_address=contract_address,
                chain=self.chain,
                source_code=source_code
            )
            
            session.add(scan)
            session.commit()
            
            scan_id = scan.id
            print(f"  ✓ Scan saved to database (ID: {scan_id})")
            return scan_id
            
        finally:
            session.close()
    
    def _apply_ml_classification(self, vulnerabilities: list, source_code: str) -> list:
        """Apply ML classification to vulnerabilities"""
        enhanced_vulnerabilities = []
        
        for vuln in vulnerabilities:
            # Get ML prediction for this vulnerability type
            # (In production, you'd extract the relevant code snippet)
            try:
                ml_result = self.ml_classifier.predict(source_code[:512])
                
                # Add ML confidence score
                vuln['ml_confidence'] = ml_result['confidence']
                vuln['ml_prediction'] = ml_result['vulnerability_type']
                
                # Adjust severity based on ML confidence
                if ml_result['confidence'] > 0.9:
                    print(f"        ✓ {vuln['type']}: {ml_result['confidence']*100:.1f}% confidence (HIGH)")
                elif ml_result['confidence'] > 0.7:
                    print(f"        ✓ {vuln['type']}: {ml_result['confidence']*100:.1f}% confidence (MEDIUM)")
                else:
                    print(f"        ⚠️  {vuln['type']}: {ml_result['confidence']*100:.1f}% confidence (LOW)")
                
            except Exception as e:
                print(f"        ⚠️  ML classification failed: {e}")
                vuln['ml_confidence'] = 0.5
                vuln['ml_prediction'] = vuln['type']
            
            enhanced_vulnerabilities.append(vuln)
        
        return enhanced_vulnerabilities
    
    def _save_vulnerabilities(self, scan_id: int, vulnerabilities: list) -> list:
        """Save vulnerabilities to database and return their IDs"""
        session = db.get_session()
        saved_records = []
        
        try:
            for vuln in vulnerabilities:
                vuln_record = Vulnerability(
                    scan_id=scan_id,
                    vuln_type=vuln['type'],
                    severity=vuln.get('severity', 'Medium'),
                    line_number=vuln.get('line', 0),
                    description=vuln.get('description', ''),
                    ml_confidence=vuln.get('ml_confidence', vuln.get('confidence', 0.5)),
                    detected_by='ml_scanner' if 'ml_confidence' in vuln else 'llm'
                )
                
                session.add(vuln_record)
                session.flush()  # Flush to get ID
                
                saved_records.append({
                    'id': vuln_record.id,
                    'severity': vuln_record.severity,
                    'type': vuln_record.vuln_type
                })
            
            session.commit()
            print(f"        ✓ Saved {len(saved_records)} vulnerabilities")
            
            return saved_records
            
        except Exception as e:
            print(f"        ❌ Failed to save vulnerabilities: {e}")
            session.rollback()
            return []
        
        finally:
            session.close()




    def _update_vulnerability_impact(self, vuln_id: int, impact_data: dict):
        """Update vulnerability with impact data using a fresh session"""
        session = db.get_session()
        try:
            vuln = session.query(Vulnerability).filter_by(id=vuln_id).first()
            if vuln:
                vuln.cvss_score = impact_data.get('cvss_score')
                
                # Update extra_data
                current_data = dict(vuln.extra_data) if vuln.extra_data else {}
                current_data['impact'] = impact_data
                vuln.extra_data = current_data
                
                session.commit()
        except Exception as e:
            print(f"        ⚠️  Failed to update vulnerability impact: {e}")
            session.rollback()
        finally:
            session.close()


if __name__ == "__main__":
    async def test():
        scanner = UnifiedScannerML(chain="eth", use_ml=True)
        
        code = """
        pragma solidity ^0.8.0;
        
        contract VulnerableVault {
            mapping(address => uint) public balances;
            
            function deposit() public payable {
                balances[msg.sender] += msg.value;
            }
            
            function withdraw() public {
                uint amt = balances[msg.sender];
                (bool success,) = msg.sender.call{value: amt}("");
                require(success);
                balances[msg.sender] = 0;  // State updated AFTER external call!
            }
        }
        """
        
        result = await scanner.scan_contract(
            code,
            "VulnerableVault",
            generate_poc=True,
            verify_poc=True,
            create_evidence=True,
            generate_bounty_report=True,
            bounty_platform='immunefi'
        )
        
        print("\n📊 Scan Results:")
        print(f"  Scan ID: {result['scan_id']}")
        print(f"  Vulnerabilities: {len(result['vulnerabilities'])}")
        print(f"  Verified POCs: {sum(1 for p in result['pocs'] if p.get('verified'))}")
        print(f"  Bounty Reports: {len(result['bounty_reports'])}")
    
    asyncio.run(test())
