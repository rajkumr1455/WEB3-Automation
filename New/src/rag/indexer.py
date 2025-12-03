"""
RAG Indexer
Index contracts, documentation, and vulnerability patterns in Qdrant
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os
import logging
from typing import List, Dict, Any
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Qdrant configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
EMBEDDING_DIM = 768  # nomic-embed-text dimension


class Indexer:
    """Qdrant indexer for Web3 security knowledge"""
    
    def __init__(self, qdrant_url: str = QDRANT_URL):
        self.client = QdrantClient(url=qdrant_url)
        self.collections = {
            "contracts": "web3_contracts",
            "vulnerabilities": "web3_vulnerabilities",
            "documentation": "web3_documentation"
        }
        self._ensure_collections()
    
    def _ensure_collections(self):
        """Ensure all collections exist"""
        for collection_name in self.collections.values():
            try:
                self.client.get_collection(collection_name)
                logger.info(f"Collection {collection_name} exists")
            except:
                logger.info(f"Creating collection {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM,
                        distance=Distance.COSINE
                    )
                )
    
    async def index_contract(self, contract_code: str, metadata: Dict[str, Any], 
                            embedding: List[float]) -> str:
        """Index a smart contract"""
        point_id = str(uuid.uuid4())
        
        self.client.upsert(
            collection_name=self.collections["contracts"],
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "code": contract_code[:5000],  # Truncate for storage
                        "metadata": metadata
                    }
                )
            ]
        )
        
        logger.info(f"Indexed contract: {point_id}")
        return point_id
    
    async def index_vulnerability(self, vulnerability: Dict[str, Any], 
                                 embedding: List[float]) -> str:
        """Index a vulnerability finding"""
        point_id = str(uuid.uuid4())
        
        self.client.upsert(
            collection_name=self.collections["vulnerabilities"],
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=vulnerability
                )
            ]
        )
        
        logger.info(f"Indexed vulnerability: {point_id}")
        return point_id
    
    async def index_documentation(self, doc_text: str, metadata: Dict[str, Any],
                                 embedding: List[float]) -> str:
        """Index documentation"""
        point_id = str(uuid.uuid4())
        
        self.client.upsert(
            collection_name=self.collections["documentation"],
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": doc_text,
                        "metadata": metadata
                    }
                )
            ]
        )
        
        logger.info(f"Indexed documentation: {point_id}")
        return point_id
    
    def delete_by_scan_id(self, scan_id: str):
        """Delete all data for a specific scan"""
        for collection_name in self.collections.values():
            try:
                # This is simplified - real implementation would use filters
                logger.info(f"Cleaning up scan {scan_id} from {collection_name}")
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")


# Singleton instance
indexer = Indexer()
