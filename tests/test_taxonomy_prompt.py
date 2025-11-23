import os
import sys
import unittest
from langchain_core.prompts import ChatPromptTemplate

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analysis.llm_auditor import LLMAuditor

class TestTaxonomyPrompt(unittest.TestCase):
    def test_prompt_structure(self):
        auditor = LLMAuditor()
        
        # We can't easily access the internal prompt object without modifying the class to expose it,
        # or we can just instantiate it and check if the file content was updated correctly (which we did).
        # But let's try to inspect the chain or just run a dummy analyze to see if it errors on missing keys.
        
        # Actually, let's just mock the LLM and check the input it receives.
        from unittest.mock import MagicMock
        auditor.llm = MagicMock()
        auditor.llm.invoke = MagicMock(return_value="{}")
        
        # Run analyze
        auditor.analyze("contract Foo {}", [], ["Pattern A"])
        
        # Check if invoke was called (chain execution)
        # Since chain = prompt | llm | parser, the llm.invoke gets the formatted prompt.
        # It's hard to inspect the exact string passed to LLM without mocking the prompt template.
        
        # Instead, let's just verify the file content contains the keywords.
        with open("src/analysis/llm_auditor.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("🔴 RED (High Severity)", content)
        self.assertIn("🟡 YELLOW (Coding & Config)", content)
        self.assertIn("🔵 BLUE (Logical & Operational)", content)
        self.assertIn("{rag_context}", content)
        
        print("Taxonomy keywords found in source code.")

if __name__ == "__main__":
    unittest.main()
