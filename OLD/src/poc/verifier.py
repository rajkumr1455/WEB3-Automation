"""
POC Verification System
Automatically runs generated POCs with Foundry and captures results
"""
import os
import subprocess
import json
import re
from typing import Dict, Optional
from datetime import datetime
from src.database.models import db, Vulnerability, Evidence

class PoCVerifier:
    """
    Verifies POC exploits using Foundry
    """
    
    def __init__(self, foundry_path: str = "foundry"):
        self.foundry_path = foundry_path
        self.foundry_dir = os.path.join(foundry_path, "test")
        os.makedirs(self.foundry_dir, exist_ok=True)
    
    def setup_foundry_project(self):
        """Initialize Foundry project if not exists"""
        if not os.path.exists(os.path.join(self.foundry_path, "foundry.toml")):
            print("🔧 Initializing Foundry project...")
            subprocess.run(
                ["forge", "init", "--force", self.foundry_path],
                capture_output=True,
                text=True
            )
    
    def verify_poc(self, poc_file_path: str, vulnerability_id: int = None) -> Dict:
        """
        Run POC test with Foundry and capture results
        
        Returns:
            {
                'success': bool,
                'gas_used': int,
                'output': str,
                'error': str,
                'test_results': dict
            }
        """
        print(f"\n🧪 Verifying POC: {os.path.basename(poc_file_path)}")
        
        # Copy POC to Foundry test directory
        poc_filename = os.path.basename(poc_file_path)
        foundry_test_path = os.path.join(self.foundry_dir, poc_filename)
        
        try:
            with open(poc_file_path, 'r') as src:
                poc_code = src.read()
            
            with open(foundry_test_path, 'w') as dst:
                dst.write(poc_code)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to copy POC file: {e}",
                'output': '',
                'gas_used': 0,
                'test_results': {}
            }
        
        # Run forge test
        cmd = [
            "forge", "test",
            "--match-path", foundry_test_path,
            "-vvv",  # Very verbose output
            "--gas-report"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.foundry_path,
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace'
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            # Parse test results
            test_results = self._parse_forge_output(output)
            
            # Extract gas usage
            
            if success:
                print(f"   ✅ POC VERIFIED! Gas used: {gas_used:,}")
            else:
                print(f"   ❌ POC FAILED")
            
            return verification_result
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test timeout (>60s)',
                'output': '',
                'gas_used': 0,
                'test_results': {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'gas_used': 0,
                'test_results': {}
            }
    
    def _parse_forge_output(self, output: str) -> Dict:
        """Parse Forge output to extract test results"""
        results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'test_names': []
        }
        
        # Look for test results pattern
        # Example: "[PASS] testReentrancy() (gas: 123456)"
        test_pattern = r'\[(PASS|FAIL)\]\s+(\w+)\(\)\s+\(gas:\s+(\d+)\)'
        
        for match in re.finditer(test_pattern, output):
            status, test_name, gas = match.groups()
            results['total_tests'] += 1
            results['test_names'].append(test_name)
            
            if status == 'PASS':
                results['passed'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    def _extract_gas_usage(self, output: str) -> int:
        """Extract total gas usage from output"""
        # Look for gas usage in test output
        gas_pattern = r'gas:\s+(\d+)'
        matches = re.findall(gas_pattern, output)
        
        if matches:
            # Return max gas usage
            return max(int(g) for g in matches)
        
        return 0
    
    def _save_evidence(self, vulnerability_id: int, output: str, evidence_type: str):
        """Save verification output as evidence"""
        session = db.get_session()
        
        try:
            # Save output to file
            evidence_dir = "reports/evidence"
            os.makedirs(evidence_dir, exist_ok=True)
            
            filename = f"vuln_{vulnerability_id}_{evidence_type}_{int(datetime.now().timestamp())}.txt"
            filepath = os.path.join(evidence_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(output)
            
            # Create evidence record
            evidence = Evidence(
                vulnerability_id=vulnerability_id,
                evidence_type=evidence_type,
                file_path=filepath,
                description="POC verification output from Foundry"
            )
            
            session.add(evidence)
            session.commit()
            
        except Exception as e:
            print(f"   ⚠️  Failed to save evidence: {e}")
            session.rollback()
        
        finally:
            session.close()
    
    def _update_vulnerability_status(self, vulnerability_id: int, success: bool, result: Dict):
        """Update vulnerability record with verification results"""
        session = db.get_session()
        
        try:
            vuln = session.query(Vulnerability).filter_by(id=vulnerability_id).first()
            
            if vuln:
                vuln.poc_verified = success
                vuln.verified_at = datetime.utcnow()
                
                # Update metadata with verification results
                if not vuln.metadata:
                    vuln.metadata = {}
                
                vuln.metadata['verification'] = {
                    'success': success,
                    'gas_used': result.get('gas_used', 0),
                    'test_results': result.get('test_results', {}),
                    'verified_at': result.get('verified_at')
                }
                
                session.commit()
                print(f"   ✓ Updated vulnerability #{vulnerability_id} status")
            
        except Exception as e:
            print(f"   ⚠️  Failed to update vulnerability: {e}")
            session.rollback()
        
        finally:
            session.close()


if __name__ == "__main__":
    # Test POC verifier
    verifier = PoCVerifier()
    verifier.setup_foundry_project()
    
    # Check if there's a POC to verify
    poc_dir = "reports/pocs"
    if os.path.exists(poc_dir):
        poc_files = [f for f in os.listdir(poc_dir) if f.endswith('.t.sol')]
        
        if poc_files:
            poc_file = os.path.join(poc_dir, poc_files[0])
            print(f"\nTesting with: {poc_file}")
            
            result = verifier.verify_poc(poc_file)
            
            print("\n" + "=" * 50)
            print("Verification Result:")
            print(json.dumps(result, indent=2))
        else:
            print("No POC files found to verify")
    else:
        print("POC directory not found")
