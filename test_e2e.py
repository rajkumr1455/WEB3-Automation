#!/usr/bin/env python3
"""
End-to-End Testing Script for Web3 Hunter
Tests all components and workflows systematically
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test 1: Check if all required modules can be imported"""
    print("\n" + "="*80)
    print("TEST 1: Module Imports")
    print("="*80)
    
    tests = [
        ("Config", "from src.config import config"),
        ("HunterGraph", "from src.orchestration.hunter_graph import HunterGraph"),
        ("ReportGenerator", "from src.reporting.report_generator import ReportGenerator"),
        ("SlitherRunner", "from src.analysis.slither_runner import SlitherRunner"),
        ("LLMAuditor", "from src.analysis.llm_auditor import LLMAuditor"),
        ("EtherscanAPI", "from src.integrations.etherscan_api import EtherscanAPI"),
        ("ContractFetcher", "from src.ingestion.contract_fetcher import ContractFetcher"),
    ]
    
    results = []
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✓ {name:20s} - OK")
            results.append(True)
        except Exception as e:
            print(f"✗ {name:20s} - FAILED: {str(e)[:50]}")
            results.append(False)
    
    return all(results)

def test_config():
    """Test 2: Check configuration"""
    print("\n" + "="*80)
    print("TEST 2: Configuration")
    print("="*80)
    
    try:
        from src.config import config
        
        # Check settings.yaml exists
        settings_path = Path("config/settings.yaml")
        if not settings_path.exists():
            print("✗ settings.yaml not found")
            return False
        print(f"✓ settings.yaml exists")
        
        # Check required fields
        llm_config = config.get_llm_config()
        required_fields = ['base_url', 'model', 'temperature']
        
        for field in required_fields:
            if field in llm_config:
                print(f"✓ LLM config has '{field}': {llm_config[field]}")
            else:
                print(f"✗ LLM config missing '{field}'")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

def test_ollama():
    """Test 3: Check Ollama connection"""
    print("\n" + "="*80)
    print("TEST 3: Ollama Connection")
    print("="*80)
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"✓ Ollama is running")
            print(f"✓ Available models: {len(models)}")
            for model in models:
                print(f"  - {model.get('name', 'unknown')}")
            return True
        else:
            print(f"✗ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to Ollama: {e}")
        print("  Make sure Ollama is running: ollama serve")
        return False

def test_slither():
    """Test 4: Check Slither installation"""
    print("\n" + "="*80)
    print("TEST 4: Slither Installation")
    print("="*80)
    
    try:
        import subprocess
        result = subprocess.run(['slither', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ Slither installed: {version}")
            return True
        else:
            print(f"✗ Slither command failed")
            return False
    except FileNotFoundError:
        print("✗ Slither not found")
        print("  Install with: pip install slither-analyzer")
        return False
    except Exception as e:
        print(f"✗ Slither test failed: {e}")
        return False

def test_hunter_graph_init():
    """Test 5: Initialize HunterGraph"""
    print("\n" + "="*80)
    print("TEST 5: HunterGraph Initialization")
    print("="*80)
    
    try:
        from src.orchestration.hunter_graph import HunterGraph
        
        print("Initializing HunterGraph...")
        graph = HunterGraph()
        print("✓ HunterGraph initialized successfully")
        
        # Check components
        components = ['fetcher', 'flattener', 'slither', 'auditor', 'vector_store']
        for comp in components:
            if hasattr(graph, comp):
                print(f"✓ Component '{comp}' exists")
            else:
                print(f"✗ Component '{comp}' missing")
                return False
        
        return True
    except Exception as e:
        print(f"✗ HunterGraph initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analysis_workflow():
    """Test 6: Run analysis on test contract"""
    print("\n" + "="*80)
    print("TEST 6: Analysis Workflow")
    print("="*80)
    
    try:
        from src.orchestration.hunter_graph import HunterGraph
        
        # Check if test contract exists
        test_contract = Path("data/uploads/TestContract.sol")
        if not test_contract.exists():
            print(f"✗ Test contract not found at {test_contract}")
            return False
        
        print(f"✓ Test contract found: {test_contract}")
        
        graph = HunterGraph()
        
        state = {
            "target_url": "test://TestContract.sol",
            "local_path": str(test_contract.parent),
            "slither_results": [],
            "flattened_code": "",
            "vulnerabilities": ""
        }
        
        print("Running analysis...")
        result = graph.analyze_node(state)
        
        print(f"✓ Analysis completed")
        print(f"  - Flattened code length: {len(result.get('flattened_code', ''))} chars")
        print(f"  - Slither results: {len(result.get('slither_results', []))} issues")
        print(f"  - Vulnerabilities: {len(result.get('vulnerabilities', ''))} chars")
        
        return True
    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_report_generation():
    """Test 7: Generate report"""
    print("\n" + "="*80)
    print("TEST 7: Report Generation")
    print("="*80)
    
    try:
        from src.reporting.report_generator import ReportGenerator
        
        report_gen = ReportGenerator()
        
        # Create simple test data
        test_findings = '{"vulnerabilities": [{"name": "Test Vuln", "severity": "High"}]}'
        
        print("Generating test report...")
        report_path = report_gen.generate_html_report(
            contract_name="TestContract",
            source_code="// Test contract",
            findings=test_findings,
            slither_results=[],
            poc_code=""
        )
        
        if Path(report_path).exists():
            print(f"✓ Report generated: {report_path}")
            print(f"  Size: {Path(report_path).stat().st_size} bytes")
            return True
        else:
            print(f"✗ Report file not created")
            return False
            
    except Exception as e:
        print(f"✗ Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_ui():
    """Test 8: Check Web UI files"""
    print("\n" + "="*80)
    print("TEST 8: Web UI Files")
    print("="*80)
    
    files_to_check = [
        "web_ui/app.py",
        "web_ui/templates/index.html",
    ]
    
    all_exist = True
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path} exists ({path.stat().st_size} bytes)")
        else:
            print(f"✗ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("WEB3 HUNTER - END-TO-END TESTING")
    print("="*80)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("Ollama Connection", test_ollama),
        ("Slither Installation", test_slither),
        ("HunterGraph Init", test_hunter_graph_init),
        ("Analysis Workflow", test_analysis_workflow),
        ("Report Generation", test_report_generation),
        ("Web UI Files", test_web_ui),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
