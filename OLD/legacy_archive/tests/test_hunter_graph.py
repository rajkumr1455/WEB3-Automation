import os
import sys
import logging
import unittest
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestration.hunter_graph import HunterGraph, HunterState

logging.basicConfig(level=logging.INFO)

class TestHunterGraph(unittest.TestCase):
    def setUp(self):
        self.graph = HunterGraph()
        
        # Mock Fetcher to return local test data path
        self.test_data_path = os.path.abspath("tests/data")
        self.graph.fetcher.fetch_from_git = MagicMock(return_value=self.test_data_path)
        
        # Mock get_main_contract to avoid "test" dir exclusion issue
        test_contract_path = os.path.join(self.test_data_path, "Test.sol")
        self.graph.flattener.get_main_contract = MagicMock(return_value=test_contract_path)
        
        # Mock VectorStore if needed (optional, as it has fallback)
        # self.graph.vector_store.query = MagicMock(return_value=["Mock Context"])

    def test_analyze_node(self):
        print("\n[Test] Running analyze_node...")
        
        # Initial state
        state = {
            "target_url": "https://github.com/mock/repo",
            "local_path": self.test_data_path,
            "slither_results": [],
            "mythril_results": [],
            "vulnerabilities": "",
            "flattened_code": "",
            "graph_path": "",
            "poc_code": "",
            "is_verified": False,
            "report": ""
        }
        
        # Run analyze_node
        result = self.graph.analyze_node(state)
        
        # Verify results
        self.assertIn("flattened_code", result)
        self.assertIn("vulnerabilities", result)
        self.assertIn("slither_results", result)
        
        print(f"[OK] Flattened Code Length: {len(result['flattened_code'])}")
        print(f"[OK] Vulnerabilities: {result['vulnerabilities'][:100]}...")
        
        # Check if call graph was generated (it might fail but key should be there)
        if "call_graph" in result:
            print(f"[OK] Call Graph Key Present. Content Length: {len(result['call_graph'])}")
        else:
            print("[WARN] Call Graph Key Missing")

if __name__ == "__main__":
    unittest.main()
