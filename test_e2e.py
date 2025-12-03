"""
End-to-End Test Suite for Web3 Hunter
Tests the complete workflow and identifies issues
"""
import asyncio
import os
import sys
from pathlib import Path

# Test results tracking
test_results = []

def log_test(name, passed, error=None):
    status = "[PASS]" if passed else "[FAIL]"
    test_results.append({"name": name, "passed": passed, "error": error})
    print(f"{status} {name}")
    if error:
        print(f"  Error: {error}")

async def test_llm_service():
    """Test LLM Service"""
    try:
        from llm_service import LLMService
        service = LLMService(use_rag=False)  # Disable RAG for faster testing
        
        code = """
        pragma solidity ^0.8.0;
        contract Test {
            function withdraw() public {
                (bool s,) = msg.sender.call{value: 1 ether}("");
            }
        }
        """
        
        result = await service.analyze_code(code)
        
        if 'vulnerabilities' in result:
            log_test("LLM Service", True)
            return True
        else:
            log_test("LLM Service", False, "No vulnerabilities key in response")
            return False
    except Exception as e:
        log_test("LLM Service", False, str(e))
        return False

async def test_poc_generator():
    """Test PoC Generator"""
    try:
        from poc_generator import PoCGenerator
        gen = PoCGenerator()
        
        vuln = {
            "type": "Reentrancy",
            "line": 5,
            "severity": "High",
            "description": "Test vulnerability"
        }
        
        code = "contract Test {}"
        result = await gen.generate(vuln, code, "TestContract")
        
        if result and 'poc_file' in result:
            # Check if file was created
            if os.path.exists(result['poc_file']):
                log_test("PoC Generator", True)
                return True
            else:
                log_test("PoC Generator", False, "PoC file not created")
                return False
        else:
            log_test("PoC Generator", False, "No PoC generated")
            return False
    except Exception as e:
        log_test("PoC Generator", False, str(e))
        return False

def test_report_generator():
    """Test Report Generator"""
    try:
        from report_generator import ReportGenerator
        gen = ReportGenerator()
        
        vulns = [{
            "type": "Reentrancy",
            "severity": "High",
            "line": 10,
            "confidence": 0.95,
            "description": "Test vulnerability"
        }]
        
        result = gen.create_report(
            contract_name="TestContract",
            chain="eth",
            source_code="contract Test {}",
            vulnerabilities=vulns,
            pocs=[],
            summary="Test report"
        )
        
        if result and 'markdown_path' in result:
            if os.path.exists(result['markdown_path']):
                log_test("Report Generator", True)
                return True
            else:
                log_test("Report Generator", False, "Report file not created")
                return False
        else:
            log_test("Report Generator", False, "No report generated")
            return False
    except Exception as e:
        log_test("Report Generator", False, str(e))
        return False

async def test_unified_scanner():
    """Test Unified Scanner E2E"""
    try:
        from unified_scanner import UnifiedScanner
        scanner = UnifiedScanner(chain="eth")
        
        code = """
        pragma solidity ^0.8.0;
        contract VulnContract {
            mapping(address => uint) balances;
            function withdraw() public {
                uint amt = balances[msg.sender];
                (bool s,) = msg.sender.call{value: amt}("");
                balances[msg.sender] = 0;
            }
        }
        """
        
        result = await scanner.scan_contract(code, "E2ETestContract")
        
        if result and 'report_path' in result:
            if os.path.exists(result['report_path']):
                log_test("Unified Scanner E2E", True)
                return True
            else:
                log_test("Unified Scanner E2E", False, "Report not created")
                return False
        else:
            log_test("Unified Scanner E2E", False, "Scan failed")
            return False
    except Exception as e:
        log_test("Unified Scanner E2E", False, str(e))
        return False

def test_celery_config():
    """Test Celery Configuration"""
    try:
        from tasks import app as celery_app
        
        # Check if broker is configured
        if celery_app.conf.broker_url:
            log_test("Celery Configuration", True)
            return True
        else:
            log_test("Celery Configuration", False, "No broker configured")
            return False
    except Exception as e:
        log_test("Celery Configuration", False, str(e))
        return False

def test_file_structure():
    """Test File Structure"""
    required_files = [
        "unified_scanner.py",
        "poc_generator.py",
        "report_generator.py",
        "llm_service.py",
        "bss_scanner.py",
        "tasks.py",
        "requirements.txt"
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
    
    if not missing:
        log_test("File Structure", True)
        return True
    else:
        log_test("File Structure", False, f"Missing: {', '.join(missing)}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Web3 Hunter - End-to-End Test Suite")
    print("=" * 60)
    print()
    
    # Phase 1: Module Tests
    print("[Phase 1] Module Testing...")
    await test_llm_service()
    await test_poc_generator()
    test_report_generator()
    test_celery_config()
    test_file_structure()
    
    print()
    print("[Phase 2] Integration Testing...")
    await test_unified_scanner()
    
    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total = len(test_results)
    passed = sum(1 for t in test_results if t['passed'])
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed > 0:
        print("FAILED TESTS:")
        for t in test_results:
            if not t['passed']:
                print(f"  - {t['name']}: {t['error']}")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
