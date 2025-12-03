import ollama
import asyncio
import json
import logging
import os
import lancedb
from sentence_transformers import SentenceTransformer
from typing import Dict, Any, List

logger = logging.getLogger("LLMService")

class LLMService:
    def __init__(self, model_name: str = "qwen2.5-coder:7b", use_rag: bool = True):
        self.model_name = model_name
        self.use_rag = use_rag
        self.embedding_model = None
        self.db = None
        
        if use_rag:
            self._init_rag()
        
        self.system_prompt = """
<|im_start|>system
You are an expert Smart Contract Security Auditor. 
Your goal is to analyze Solidity code for vulnerabilities.
You MUST output your analysis in strict JSON format.
Do not include any markdown formatting (like ```json) in your response.
The JSON structure must be:
{
    "vulnerabilities": [
        {
            "type": "string (e.g., Reentrancy)",
            "severity": "string (High/Medium/Low)",
            "line": number,
            "description": "string",
            "confidence": float (0.0 to 1.0)
        }
    ],
    "summary": "string"
}
If no vulnerabilities are found, the "vulnerabilities" list should be empty.
<|im_end|>
"""

    def _init_rag(self):
        """Initialize RAG components (LanceDB and embedding model)."""
        try:
            data_dir = os.path.join(os.path.dirname(__file__), "data")
            db_path = os.path.join(data_dir, "lancedb")
            
            if os.path.exists(db_path):
                self.db = lancedb.connect(db_path)
                self.embedding_model = SentenceTransformer('BAAI/bge-m3')
                logger.info("RAG initialized successfully")
            else:
                logger.warning(f"LanceDB not found at {db_path}. RAG disabled.")
                self.use_rag = False
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            self.use_rag = False

    async def retrieve_context(self, query: str, limit: int = 3) -> List[str]:
        """Retrieve relevant code snippets from RAG database."""
        if not self.use_rag or not self.db:
            return []
        
        try:
            table = self.db.open_table("smart_contracts")
            query_vector = self.embedding_model.encode(query).tolist()
            
            results = table.search(query_vector).limit(limit).to_list()
            contexts = [r['text'] for r in results]
            return contexts
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return []

    async def analyze_code(self, source_code: str) -> Dict[str, Any]:
        """
        Analyze the provided source code using the local LLM with RAG enhancement.
        """
        logger.info(f"Analyzing code with {self.model_name}...")
        
        # Retrieve similar vulnerable code examples from RAG
        context_snippets = []
        if self.use_rag:
            context_snippets = await self.retrieve_context(source_code[:500], limit=2)
        
        # Build context section
        context_section = ""
        if context_snippets:
            context_section = "\n\n<CONTEXT>Here are similar contract patterns from the vulnerability database:\n"
            for idx, snippet in enumerate(context_snippets, 1):
                context_section += f"\nExample {idx}:\n```solidity\n{snippet[:300]}...\n```\n"
            context_section += "</CONTEXT>\n"
        
        prompt = f"""
<|im_start|>user
{context_section}
Analyze the following Solidity contract for security vulnerabilities:

```solidity
{source_code}
```
<|im_end|>
<|im_start|>assistant
"""
        
        try:
            client = ollama.AsyncClient()
            response = await client.generate(
                model=self.model_name,
                prompt=self.system_prompt + prompt,
                format="json",
                stream=False
            )
            
            response_text = response['response']
            logger.debug(f"LLM Response: {response_text}")
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response from LLM")
                return {"error": "Invalid JSON", "raw_response": response_text}
                
        except Exception as e:
            logger.error(f"Error during LLM analysis: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Test the service
    async def test():
        service = LLMService(use_rag=True)
        code = """
        pragma solidity ^0.8.0;
        contract Test {
            function withdraw() public {
                (bool s, ) = msg.sender.call{value: address(this).balance}("");
            }
        }
        """
        result = await service.analyze_code(code)
        print(json.dumps(result, indent=2))

    asyncio.run(test())
