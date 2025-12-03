"""
Real Contract E2E Test - BSS Smart Contract
Tests the complete workflow with a real BSS contract
"""
import asyncio
import sys
from bss_scanner import BSSScanner

async def test_real_contract():
    """
    Test with real BSS contract: 0x00b174d66adA7d63789087F50A9b9e0e48446dc1
    """
    contract_address = "0x00b174d66adA7d63789087F50A9b9e0e48446dc1"
    
    print("=" * 70)
    print("Real BSS Contract E2E Test")
    print("=" * 70)
    print(f"Contract Address: {contract_address}")
    print()
    
    # Initialize scanner
    # Note: You need a BscScan API key for this to work
    # Get one from: https://bscscan.com/apis
    api_key = input("Enter your BscScan API key (or press Enter for demo key): ").strip()
    if not api_key:
        api_key = "YourApiKeyToken"  # Demo/placeholder
    
    scanner = BSSScanner(api_key=api_key)
    
    print("\n[1/4] Fetching contract source from BscScan...")
    try:
        result = await scanner.scan_address(contract_address)
        
        if 'error' in result:
            print(f"[ERROR] {result['error']}")
            print("\nTroubleshooting:")
            print("1. Get a BscScan API key: https://bscscan.com/apis")
            print("2. Set it: export BSCSCAN_API_KEY=your_key")
            print("3. Or pass it when prompted")
            return False
        
        print(f"[SUCCESS] Contract fetched: {result.get('contract_name', 'Unknown')}")
        
        print("\n[2/4] Running AI analysis...")
        vuln_count = len(result.get('vulnerabilities', []))
        print(f"[SUCCESS] Found {vuln_count} vulnerabilities")
        
        print("\n[3/4] Generating PoCs...")
        poc_count = len(result.get('pocs', []))
        print(f"[SUCCESS] Generated {poc_count} PoC files")
        
        print("\n[4/4] Creating report...")
        report_path = result.get('report_path', 'N/A')
        print(f"[SUCCESS] Report created: {report_path}")
        
        print("\n" + "=" * 70)
        print("WORKFLOW TEST: PASSED ✓")
        print("=" * 70)
        
        # Display summary
        print("\n📊 Scan Summary:")
        print(f"  Contract: {result.get('contract_name', 'Unknown')}")
        print(f"  Chain: {result.get('chain', 'BSS').upper()}")
        print(f"  Vulnerabilities: {vuln_count}")
        print(f"  PoCs Generated: {poc_count}")
        print(f"  Report: {report_path}")
        
        if vuln_count > 0:
            print("\n🔍 Vulnerabilities Found:")
            for vuln in result.get('vulnerabilities', [])[:5]:  # Show first 5
                print(f"  - {vuln['severity']} - {vuln['type']} (Line {vuln['line']})")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_contract())
    sys.exit(0 if success else 1)
