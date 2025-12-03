"""
RAG Query
Semantic search and retrieval from Qdrant
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import os
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Qdrant configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")


class QueryEngine:
    """Semantic search engine for Web3 security knowledge"""
    
    def __init__(self, qdrant_url: str = QDRANT_URL):
        self.client = QdrantClient(url=qdrant_url)
        self.collections = {
            "contracts": "web3_contracts",
            "vulnerabilities": "web3_vulnerabilities",
            "documentation": "web3_documentation"
        }
    
    async def search_similar_contracts(self, query_embedding: List[float], 
                                      limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar contracts"""
        try:
            results = self.client.search(
                collection_name=self.collections["contracts"],
                query_vector=query_embedding,
                limit=limit
            )
            
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "code": hit.payload.get("code"),
                    "metadata": hit.payload.get("metadata")
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Contract search failed: {e}")
            return []
    
    async def search_similar_vulnerabilities(self, query_embedding: List[float],
                                            limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar vulnerabilities"""
        try:
            results = self.client.search(
                collection_name=self.collections["vulnerabilities"],
                query_vector=query_embedding,
                limit=limit
            )
            
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    **hit.payload
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Vulnerability search failed: {e}")
            return []
    
    async def search_documentation(self, query_embedding: List[float],
                                  limit: int = 5) -> List[Dict[str, Any]]:
        """Search documentation"""
        try:
            results = self.client.search(
                collection_name=self.collections["documentation"],
                query_vector=query_embedding,
                limit=limit
            )
            
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "text": hit.payload.get("text"),
                    "metadata": hit.payload.get("metadata")
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Documentation search failed: {e}")
            return []
    
    async def get_vulnerability_context(self, vulnerability_type: str,
                                       query_embedding: List[float]) -> str:
        """Get context for a vulnerability type"""
        # Search for similar vulnerabilities
        similar = await self.search_similar_vulnerabilities(query_embedding, limit=3)
        
        if not similar:
            return "No similar vulnerabilities found in knowledge base."
        
        context = f"Similar known vulnerabilities:\n\n"
        for i, vuln in enumerate(similar, 1):
            context += f"{i}. {vuln.get('title', 'Unknown')}\n"
            context += f"   Severity: {vuln.get('severity', 'unknown')}\n"
            context += f"   Description: {vuln.get('description', 'N/A')[:200]}...\n\n"
        
        return context


# Singleton instance
query_engine = QueryEngine()
