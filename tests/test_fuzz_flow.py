import os
import sys
import logging
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.verification.foundry_runner import FoundryRunner
from src.verification.poc_generator import PoCGenerator

logging.basicConfig(level=logging.INFO)

class TestFuzzFlow(unittest.TestCase):
    def setUp(self):
        self.runner = FoundryRunner()
        self.generator = PoCGenerator()
        self.generator.llm = MagicMock()

    @patch('subprocess.run')
    def test_foundry_runner_fuzz_args(self, mock_run):
        # Mock subprocess to avoid actual execution
        mock_run.return_value.returncode = 0
        
        # Run test with fuzz_runs
        self.runner.run_test("test/Fuzz.t.sol", ".", fuzz_runs=500)
        
        # Check if --fuzz-runs was passed
        args, kwargs = mock_run.call_args
        cmd = args[0]
        self.assertIn("--fuzz-runs", cmd)
        self.assertIn("500", cmd)
        print("[OK] FoundryRunner correctly passes --fuzz-runs arg.")

    @patch('src.verification.poc_generator.ChatOllama')
    def test_generator_fuzz_method(self, MockOllama):
        from langchain_core.messages import AIMessage
        
        # Setup mock instance
        mock_llm = MockOllama.return_value
        mock_llm.invoke.return_value = AIMessage(content="contract FuzzTest is Test { ... }")
        
        # Re-instantiate generator to use mocked LLM
        generator = PoCGenerator()
        
        # Call generate_fuzz_test
        code = generator.generate_fuzz_test("contract Target {}", "balance >= 0")
        
        # Verify
        self.assertIn("contract FuzzTest", code)
        print("[OK] PoCGenerator.generate_fuzz_test returns code.")

if __name__ == "__main__":
    unittest.main()
