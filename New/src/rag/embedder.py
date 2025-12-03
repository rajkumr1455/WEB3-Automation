"""
RAG Embedder
Generate embeddings using Ollama's nomic-embed-text
"""

import httpx
import os
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LLM Router URL
LLM_ROUTER_URL = os.getenv("LLM_ROUTER_URL", "http://llm-router:8000")


class Embedder:
    """Embedding generator using LLM Router"""
    
    def __init__(self, llm_router_url: str = LLM_ROUTER_URL):
        self.llm_router_url = llm_router_url
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.llm_router_url}/embed",
                    json={"texts": texts}
                )
                response.raise_for_status()
                result = response.json()
                return result["embeddings"]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.embed_texts([text])
        return embeddings[0] if embeddings else []


# Singleton instance
embedder = Embedder()
