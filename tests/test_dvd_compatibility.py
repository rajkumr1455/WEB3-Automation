import os
import sys
import logging
import unittest
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestration.hunter_graph import HunterGraph

logging.basicConfig(level=logging.INFO)

class TestDVDCompatibility(unittest.TestCase):
    def setUp(self):
        self.graph = HunterGraph()
        # Path to 'unstoppable' challenge
        self.dvd_path = os.path.abspath("damn-vulnerable-defi-4.1.0/src/unstoppable")
        
        # Mock Fetcher to return the local path directly
        self.graph.fetcher.fetch_from_git = MagicMock(return_value=self.dvd_path)
        
        # Mock LLM to avoid long wait, we just want to check if Slither/Flattening works
        self.graph.auditor.analyze = MagicMock(return_value='{"vulnerabilities": []}')
        
        # Mock VectorStore
        self.graph.vector_store.query = MagicMock(return_value=[])

    def test_analyze_unstoppable(self):
        print(f"\n[Test] Analyzing DVD Challenge: {self.dvd_path}")
        
        if not os.path.exists(self.dvd_path):
            print("[SKIP] DVD directory not found.")
            return

        # Initial state
        state = {
            "target_url": "local_test",
            "local_path": self.dvd_path,
            "slither_results": [],
            "flattened_code": "",
            "vulnerabilities": ""
        }
        
        # Run analyze_node directly
        # This triggers: get_main_contract -> flatten -> slither -> llm
        try:
            result = self.graph.analyze_node(state)
            
            print(f"[Result] Flattened Code Length: {len(result.get('flattened_code', ''))}")
            print(f"[Result] Slither Issues: {len(result.get('slither_results', []))}")
            
            # Check if flattening succeeded (should be > 0 if compatible)
            if len(result.get('flattened_code', '')) > 0:
                print("[PASS] Flattening successful.")
            else:
                print("[FAIL] Flattening failed (empty output).")
                
        except Exception as e:
            print(f"[FAIL] Analysis crashed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    unittest.main()
