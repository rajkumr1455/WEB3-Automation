"""
End-to-End System Test
Verifies all components are working together
"""

import asyncio
import httpx
import time
from datetime import datetime


async def test_component(name: str, url: str, expected_status: int = 200):
    """Test individual component health"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            if response.status_code == expected_status:
                print(f"✅ {name:<25} - OK")
                return True
            else:
                print(f"❌ {name:<25} - HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ {name:<25} - {str(e)[:50]}")
        return False


async def test_llm_router():
    """Test LLM Router functionality"""
    print("\n🧪 Testing LLM Router...")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Test generation
            response = await client.post(
                "http://localhost:8000/generate",
                json={
                    "task_type": "code_analysis",
                    "prompt": "What is a reentrancy attack?",
                    "system_prompt": "You are a security expert."
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("response"):
                print(f"   ✅ Generation works (got {len(result['response'])} chars)")
                return True
            else:
                print("   ❌ No response from LLM")
                return False
                
    except Exception as e:
        print(f"   ❌ LLM Router test failed: {e}")
        return False


async def test_full_scan():
    """Test complete scan pipeline"""
    print("\n🔍 Testing Full Scan Pipeline...")
    
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            # Start scan
            print("   Initiating scan...")
            start_time = time.time()
            
            scan_response = await client.post(
                "http://localhost:8001/scan",
                json={
                    "target_url": "https://github.com/OpenZeppelin/openzeppelin-contracts",
                    "chain": "ethereum",
                    "scan_config": {
                        "enable_fuzzing": False,  # Skip fuzzing for speed
                        "monitor_duration": 1  # 1 minute monitoring
                    }
                }
            )
            scan_response.raise_for_status()
            scan_data = scan_response.json()
            scan_id = scan_data["scan_id"]
            
            print(f"   ✅ Scan started: {scan_id}")
            
            # Poll for completion
            print("   Monitoring progress...")
            max_wait = 300  # 5 minutes max
            last_progress = 0
            
            while time.time() - start_time < max_wait:
                status_response = await client.get(f"http://localhost:8001/scan/{scan_id}")
                status_data = status_response.json()
                
                status = status_data.get("status")
                progress = status_data.get("progress", 0)
                current_stage = status_data.get("current_stage", "unknown")
                
                if progress != last_progress:
                    print(f"   Progress: {progress}% - {current_stage}")
                    last_progress = progress
                
                if status == "completed":
                    duration = time.time() - start_time
                    print(f"\n   ✅ Scan completed in {duration:.1f}s")
                    
                    # Check results
                    results = status_data.get("results", {})
                    print(f"\n   📊 Results Summary:")
                    print(f"      Recon: {len(results.get('recon', {}).get('contracts', []))} contracts found")
                    print(f"      Static: {results.get('static', {}).get('total_issues', 0)} issues found")
                    print(f"      Triage: {results.get('triage', {}).get('total_vulnerabilities', 0)} vulnerabilities confirmed")
                    
                    return True
                    
                elif status == "failed":
                    error = status_data.get("error", "Unknown error")
                    print(f"\n   ❌ Scan failed: {error}")
                    return False
                
                await asyncio.sleep(5)
            
            print(f"\n   ⚠️  Scan timeout after {max_wait}s")
            return False
            
    except Exception as e:
        print(f"\n   ❌ Full scan test failed: {e}")
        return False


async def run_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  WEB3 BOUNTY HUNTER - END-TO-END SYSTEM TEST")
    print("=" * 70 + "\n")
    
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Component health checks
    print("📋 Component Health Checks:\n")
    
    components = [
        ("Web UI", "http://localhost:3001"),
        ("LLM Router", "http://localhost:8000/health"),
        ("Orchestrator", "http://localhost:8001/health"),
        ("Recon Agent", "http://localhost:8002/health"),
        ("Static Agent", "http://localhost:8003/health"),
        ("Fuzzing Agent", "http://localhost:8004/health"),
        ("Monitoring Agent", "http://localhost:8005/health"),
        ("Triage Agent", "http://localhost:8006/health"),
        ("Reporting Agent", "http://localhost:8007/health"),
        ("Qdrant", "http://localhost:6333"),
        ("Prometheus", "http://localhost:9090"),
        ("Grafana", "http://localhost:3000"),
    ]
    
    results = []
    for name, url in components:
        result = await test_component(name, url)
        results.append((name, result))
    
    # LLM Router functional test
    llm_ok = await test_llm_router()
    results.append(("LLM Router (Functional)", llm_ok))
    
    # Full scan test
    scan_ok = await test_full_scan()
    results.append(("Full Scan Pipeline", scan_ok))
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70 + "\n")
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status:<10} {name}")
    
    print("\n" + "=" * 70)
    print(f"  TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 70 + "\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is fully operational.\n")
        return 0
    else:
        print(f"⚠️  {total-passed} test(s) failed. Check logs above for details.\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    exit(exit_code)
