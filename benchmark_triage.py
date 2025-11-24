import json
import os
from ai_triage import analyze_finding

SAFE_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

abstract contract ReentrancyGuard {
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;

    uint256 private _status;

    constructor() {
        _status = _NOT_ENTERED;
    }

    modifier nonReentrant() {
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");
        _status = _ENTERED;
        _;
        _status = _NOT_ENTERED;
    }
}

contract SafeVault is ReentrancyGuard {
    mapping(address => uint) public balances;

    function withdraw() public nonReentrant {
        uint amount = balances[msg.sender];
        require(amount > 0);
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] = 0;
    }
}
"""

FAKE_FINDING = {
    "tool": "slither",
    "vuln_type": "reentrancy-eth",
    "file": "SafeVault.sol",
    "line": 24,
    "severity": "High",
    "details": "Reentrancy in SafeVault.withdraw()"
}

def run_benchmark():
    print("Running False Positive Benchmark...")
    print("Target: SafeVault (uses nonReentrant)")
    print("Finding: Reentrancy (Simulated)")
    
    # Check for API Key
    if not os.getenv("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY not set. Benchmark will fail or return error.")
    
    result = analyze_finding(FAKE_FINDING, SAFE_CONTRACT)
    
    print("\nAI Analysis Result:")
    print(json.dumps(result, indent=2))
    
    # Logic: is_valid should be False for a False Positive
    # But my prompt says: "Determine if this is a False Positive... Return JSON: {'is_valid': bool...}"
    # Usually "is_valid" means "is this a valid vulnerability?".
    # So for a False Positive, is_valid should be False.
    
    if result.get("is_valid") is False:
        print("\nSUCCESS: AI correctly identified it as a False Positive (is_valid=False).")
    elif result.get("error"):
        print(f"\nERROR: {result.get('error')}")
    else:
        print("\nFAILURE: AI considered it a valid bug.")

if __name__ == "__main__":
    run_benchmark()
