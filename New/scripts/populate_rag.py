"""
RAG Knowledge Base Population Script
Indexes vulnerability patterns, OpenZeppelin contracts, and security knowledge
"""

import asyncio
import httpx
import json
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.embedder import embed_text
from src.rag.indexer import index_documents

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
LLM_ROUTER_URL = os.getenv("LLM_ROUTER_URL", "http://localhost:8000")


async def fetch_swc_registry():
    """Fetch SWC (Smart Contract Weakness Classification) registry"""
    swc_data = []
    
    # SWC registry (simplified - in production, fetch from official source)
    swc_patterns = [
        {
            "id": "SWC-101",
            "title": "Integer Overflow and Underflow",
            "description": "An overflow/underflow happens when an arithmetic operation reaches the maximum or minimum size of a type.",
            "remediation": "Use SafeMath library or Solidity 0.8+ which has built-in overflow checks."
        },
        {
            "id": "SWC-107",
            "title": "Reentrancy",
            "description": "External calls to untrusted contracts can allow the called contract to make unexpected state changes.",
            "remediation": "Use Checks-Effects-Interactions pattern, reentrancy guards, or pull payment patterns."
        },
        {
            "id": "SWC-105",
            "title": "Unprotected Ether Withdrawal",
            "description": "Smart contracts that hold ether without proper access control can be drained by attackers.",
            "remediation": "Implement proper access control using modifiers like onlyOwner."
        },
        {
            "id": "SWC-104",
            "title": "Unchecked Call Return Value",
            "description": "The return value of a message call is not checked, which can lead to unexpected behavior.",
            "remediation": "Always check return values of external calls or use Solidity's require() to fail on errors."
        },
        {
            "id": "SWC-115",  
            "title": "Authorization through tx.origin",
            "description": "tx.origin should not be used for authorization as it can be exploited in phishing attacks.",
            "remediation": "Use msg.sender for authorization instead of tx.origin."
        }
    ]
    
    for swc in swc_patterns:
        swc_data.append({
            "id": swc["id"],
            "content": f"{swc['title']}: {swc['description']} Remediation: {swc['remediation']}",
            "metadata": {
                "type": "vulnerability_pattern",
                "source": "SWC",
                **swc
            }
        })
    
    return swc_data


async def fetch_openzeppelin_patterns():
    """Common OpenZeppelin security patterns"""
    oz_patterns = [
        {
            "title": "ReentrancyGuard",
            "description": "Prevent reentrant calls to a function using a mutex pattern.",
            "example": "contract MyContract is ReentrancyGuard { function withdraw() external nonReentrant { ... } }"
        },
        {
            "title": "Ownable",
            "description": "Basic access control mechanism with a single owner.",
            "example": "contract MyContract is Ownable { function sensitiveFunction() external onlyOwner { ... } }"
        },
        {
            "title": "Pausable",
            "description": "Emergency stop mechanism to pause contract functionality.",
            "example": "contract MyContract is Pausable { function transfer() external whenNotPaused { ... } }"
        },
        {
            "title": "SafeERC20",
            "description": "Wrappers around ERC20 operations that throw on failure.",
            "example": "using SafeERC20 for IERC20; token.safeTransfer(recipient, amount);"
        }
    ]
    
    oz_data = []
    for pattern in oz_patterns:
        oz_data.append({
            "id": f"OZ-{pattern['title']}",
            "content": f"{pattern['title']}: {pattern['description']} Example: {pattern['example']}",
            "metadata": {
                "type": "security_pattern",
                "source": "OpenZeppelin",
                **pattern
            }
        })
    
    return oz_data


async def fetch_common_vulnerabilities():
    """Common smart contract vulnerability knowledge"""
    vulns = [
        {
            "name": "Flash Loan Attack",
            "description": "Exploiting price oracle manipulation using flash loans to borrow large amounts without collateral.",
            "mitigation": "Use time-weighted average prices (TWAP), multiple oracle sources, and flash loan detection."
        },
        {
            "name": "Front-Running",
            "description": "Attacker observes pending transactions and submits their own with higher gas to execute first.",
            "mitigation": "Use commit-reveal schemes, batch auctions, or private mempools."
        },
        {
            "name": "Access Control Bypass",
            "description": "Missing or incorrect access control allows unauthorized users to call privileged functions.",
            "mitigation": "Use role-based access control (RBAC) and thoroughly test authorization logic."
        },
        {
            "name": "Logic Error in Complex Interactions",
            "description": "Subtle bugs in complex state transitions or calculations.",
            "mitigation": "Comprehensive testing, formal verification, and security audits."
        }
    ]
    
    vuln_data = []
    for vuln in vulns:
        vuln_data.append({
            "id": f"VULN-{vuln['name'].replace(' ', '-')}",
            "content": f"{vuln['name']}: {vuln['description']} Mitigation: {vuln['mitigation']}",
            "metadata": {
                "type": "vulnerability_knowledge",
                "source": "Common",
                **vuln
            }
        })
    
    return vuln_data


async def populate_knowledge_base():
    """Main function to populate Qdrant with security knowledge"""
    print("🔧 Populating RAG Knowledge Base...\n")
    
    all_documents = []
    
    # Fetch SWC registry
    print("📚 Fetching SWC vulnerability patterns...")
    swc_data = await fetch_swc_registry()
    all_documents.extend(swc_data)
    print(f"   ✅ Added {len(swc_data)} SWC patterns\n")
    
    # Fetch OpenZeppelin patterns
    print("📚 Fetching OpenZeppelin security patterns...")
    oz_data = await fetch_openzeppelin_patterns()
    all_documents.extend(oz_data)
    print(f"   ✅ Added {len(oz_data)} OpenZeppelin patterns\n")
    
    # Fetch common vulnerabilities
    print("📚 Fetching common vulnerability knowledge...")
    vuln_data = await fetch_common_vulnerabilities()
    all_documents.extend(vuln_data)
    print(f"   ✅ Added {len(vuln_data)} vulnerability types\n")
    
    # Generate embeddings and index
    print("🔮 Generating embeddings with nomic-embed-text...")
    
    documents_with_embeddings = []
    for doc in all_documents:
        try:
            # Call LLM router for embeddings
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{LLM_ROUTER_URL}/embed",
                    json={"text": doc["content"]}
                )
                response.raise_for_status()
                embedding = response.json()["embedding"]
                
                documents_with_embeddings.append({
                    **doc,
                    "vector": embedding
                })
                print(f"   ✅ {doc['id']}")
        except Exception as e:
            print(f"   ❌ Failed to embed {doc['id']}: {e}")
    
    print(f"\n📥 Indexing {len(documents_with_embeddings)} documents to Qdrant...")
    
    # Index to Qdrant
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Create collection
            await client.put(
                f"{QDRANT_URL}/collections/security_knowledge",
                json={
                    "vectors": {
                        "size": 768,  # nomic-embed-text dimension
                        "distance": "Cosine"
                    }
                }
            )
            print("   ✅ Created collection 'security_knowledge'")
            
            # Upsert points
            points = [
                {
                    "id": i,
                    "vector": doc["vector"],
                    "payload": {
                        "content": doc["content"],
                        "metadata": doc["metadata"]
                    }
                }
                for i, doc in enumerate(documents_with_embeddings)
            ]
            
            await client.put(
                f"{QDRANT_URL}/collections/security_knowledge/points",
                json={"points": points}
            )
            print(f"   ✅ Indexed {len(points)} documents\n")
            
    except Exception as e:
        print(f"   ❌ Failed to index to Qdrant: {e}\n")
        return False
    
    print("━" * 60)
    print("✅ Knowledge base population complete!")
    print(f"📊 Total documents indexed: {len(documents_with_embeddings)}")
    print(f"🔍 Collection: security_knowledge")
    print(f"🌐 Qdrant URL: {QDRANT_URL}")
    print("━" * 60)
    
    return True


async def test_rag_query():
    """Test RAG query functionality"""
    print("\n🧪 Testing RAG query...\n")
    
    test_query = "How do I prevent reentrancy attacks?"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Generate query embedding
            response = await client.post(
                f"{LLM_ROUTER_URL}/embed",
                json={"text": test_query}
            )
            query_vector = response.json()["embedding"]
            
            # Search Qdrant
            search_response = await client.post(
                f"{QDRANT_URL}/collections/security_knowledge/points/search",
                json={
                    "vector": query_vector,
                    "limit": 3,
                    "with_payload": True
                }
            )
            
            results = search_response.json()["result"]
            
            print(f"Query: '{test_query}'")
            print(f"\nTop {len(results)} results:\n")
            
            for i, result in enumerate(results, 1):
                print(f"{i}. Score: {result['score']:.4f}")
                print(f"   Content: {result['payload']['content'][:100]}...")
                print(f"   Type: {result['payload']['metadata']['type']}\n")
            
            print("✅ RAG query successful!\n")
            return True
            
    except Exception as e:
        print(f"❌ RAG query failed: {e}\n")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  WEB3 BOUNTY HUNTER - RAG KNOWLEDGE BASE SETUP")
    print("=" * 60 + "\n")
    
    # Run population
    success = asyncio.run(populate_knowledge_base())
    
    if success:
        # Test query
        asyncio.run(test_rag_query())
        
        print("\n💡 RAG is now ready to enhance vulnerability analysis!")
        print("   Agents can query this knowledge base for context.\n")
    else:
        print("\n⚠️  Failed to populate knowledge base.")
        print("   Make sure Qdrant and LLM Router are running.\n")
        sys.exit(1)
