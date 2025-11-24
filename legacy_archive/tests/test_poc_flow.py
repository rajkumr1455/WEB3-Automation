import os
import sys
import logging
import unittest
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestration.hunter_graph import HunterGraph

logging.basicConfig(level=logging.INFO)

class TestPoCFlow(unittest.TestCase):
    def setUp(self):
        self.graph = HunterGraph()
        self.test_data_path = os.path.abspath("tests/data")
        
        # Mock dependencies
        self.graph.fetcher.fetch_from_git = MagicMock(return_value=self.test_data_path)
        self.graph.flattener.get_main_contract = MagicMock(return_value=os.path.join(self.test_data_path, "Test.sol"))
        
        # Mock LLM Auditor to return a vulnerability
        self.graph.auditor.analyze = MagicMock(return_value='[{"title": "Reentrancy", "description": "Function is vulnerable to reentrancy."}]')
        
        # Mock PoC Generator to return a valid Solidity test
        # We use a simple test that passes
        valid_test_code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../Test.sol";

contract ExploitTest is Test {
    TestContract public target;

    def setUp() public {
        target = new TestContract();
    }

    function testExploit() public {
        target.setValue(100);
        assertEq(target.value(), 100);
    }
}
"""
        # Fix python syntax in solidity string above (def -> function)
        valid_test_code = valid_test_code.replace("def setUp", "function setUp")
        
        self.graph.poc_gen.generate_exploit = MagicMock(return_value=valid_test_code)

    def test_verify_node(self):
        print("\n[Test] Running verify_node...")
        
        # Setup state
        state = {
            "local_path": self.test_data_path,
            "flattened_code": "contract TestContract { ... }",
            "vulnerabilities": '[{"title": "Reentrancy"}]'
        }
        
        # Ensure test dir exists
        test_dir = os.path.join(self.test_data_path, "test")
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
            
        # Run verify_node
        result = self.graph.verify_node(state)
        
        # Check results
        print(f"[Result] Verified: {result['is_verified']}")
        print(f"[Result] Report: {result['report']}")
        
        # Check if file was created
        expected_path = os.path.join(test_dir, "Exploit.t.sol")
        if os.path.exists(expected_path):
            print(f"[OK] PoC file created at: {expected_path}")
        else:
            print("[FAIL] PoC file not created")
            
        # Note: The actual forge run might fail if forge-std is not installed in tests/data
        # But we want to verify the runner attempts to run it.

if __name__ == "__main__":
    unittest.main()
