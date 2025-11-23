import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    import chromadb
    from langchain_openai import OpenAIEmbeddings
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False
    logger.warning("ChromaDB or LangChain OpenAI not found. Using Mock VectorStore.")

class VectorStore:
    """
    Manages the Vector Database for RAG.
    Uses ChromaDB to store and retrieve security knowledge.
    """

    def __init__(self, persist_directory: str = "data/vector_db"):
        if HAS_CHROMA:
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.collection = self.client.get_or_create_collection(name="security_knowledge")
            self.embedding_function = OpenAIEmbeddings(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="nomic-embed-text",
                check_embedding_ctx_length=False
            )
        else:
            self.client = None
            self.collection = None

    def add_knowledge(self, texts: List[str], metadatas: List[Dict[str, Any]] = None):
        """
        Adds knowledge (CVEs, patterns) to the vector store.
        """
        if not HAS_CHROMA:
            logger.info("Mock VectorStore: Adding knowledge skipped.")
            return

        logger.info(f"Adding {len(texts)} documents to Vector DB...")
        embeddings = self.embedding_function.embed_documents(texts)
        ids = [str(i) for i in range(len(texts))]
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text: str, n_results: int = 3) -> List[str]:
        """
        Retrieves relevant knowledge for a given query.
        """
        if not HAS_CHROMA:
            logger.info("Mock VectorStore: Returning empty context.")
            return []

        logger.info(f"Querying Vector DB for: {query_text[:50]}...")
        query_embedding = self.embedding_function.embed_query(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results['documents'][0] if results['documents'] else []
