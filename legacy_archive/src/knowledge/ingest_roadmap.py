import logging
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.knowledge.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_roadmap_data():
    """
    Ingests data structured according to the Ethereum Smart Contract Auditor Roadmap.
    """
    store = VectorStore()
    
    # Define the comprehensive Smart Contract Security Workflow
    roadmap_data = [
        # Foundations
        {"category": "Foundations", "topic": "Blockchain Basics", "content": "Ethereum uses Proof of Stake consensus. Understand block structure, transactions, gas costs, and EVM opcode execution."},
        {"category": "Foundations", "topic": "Solidity Fundamentals", "content": "Master Solidity >=0.8: state variables, memory vs storage, modifiers, inheritance, events, function types (external, payable, view)."},
        {"category": "Foundations", "topic": "Gas Optimization", "content": "Understand storage vs memory costs, loop optimization, struct packing, and gas griefing attack vectors."},
        
        # Tools & Testing
        {"category": "Tools", "topic": "Testing Frameworks", "content": "Use Hardhat, Foundry, Brownie for contract testing. Master fuzzing with Echidna and Foundry Fuzz."},
        {"category": "Tools", "topic": "Static Analysis", "content": "Run Slither, Mythril, MythX, Manticore for automated vulnerability detection. Use Solhint for linting."},
        {"category": "Tools", "topic": "Visualization", "content": "Generate call graphs with Surya, Solgraph, or Slither's printer. Use VSCode UML plugins."},
        {"category": "Tools", "topic": "Debugging", "content": "Debug contracts with Tenderly, VSCode Solidity Debugger, and Remix Debugger."},
        
        # Standards
        {"category": "Standards", "topic": "ERC20", "content": "ERC20 is the fungible token standard. Key functions: transfer, approve, transferFrom, balanceOf, totalSupply."},
        {"category": "Standards", "topic": "ERC721", "content": "ERC721 is the NFT standard. Each token has unique ID. Implements transferFrom, safeTransferFrom, ownerOf."},
        {"category": "Standards", "topic": "ERC777", "content": "ERC777 is advanced fungible token with hooks. Enables tokensReceived callback but introduces reentrancy risks."},
        {"category": "Standards", "topic": "ERC1155", "content": "ERC1155 multi-token standard supports both fungible and non-fungible tokens in one contract."},
        {"category": "Standards", "topic": "ERC4626", "content": "ERC4626 tokenized vault standard. Standardizes deposit/withdraw for yield-bearing vaults."},
        {"category": "Standards", "topic": "Proxy Patterns", "content": "UUPS, Transparent Proxy, Beacon Proxy enable upgradeable contracts. Understand storage collision risks."},
        
        # Attacks - High Severity (RED)
        {"category": "Attacks", "topic": "Reentrancy", "content": "Reentrancy occurs when external call hijacks control flow before state update. Fix: Checks-Effects-Interactions pattern or ReentrancyGuard."},
        {"category": "Attacks", "topic": "Integer Overflow", "content": "Pre-0.8: Integer overflow/underflow silently wraps. Post-0.8: Built-in overflow checks. Use unchecked{} only when safe."},
        {"category": "Attacks", "topic": "Access Control", "content": "Misuse of tx.origin for auth, missing onlyOwner, role misconfiguration. Use OpenZeppelin AccessControl."},
        {"category": "Attacks", "topic": "Signature Replay", "content": "Replay attacks reuse valid signatures across chains or nonces. Include chainId and nonce in signed messages."},
        {"category": "Attacks", "topic": "Weak Randomness", "content": "Using blockhash, timestamp for randomness is predictable. Use Chainlink VRF or commit-reveal."},
        {"category": "Attacks", "topic": "Unchecked Selfdestruct", "content": "Unprotected selfdestruct can destroy contracts. Ensure proper access control and upgrade patterns."},
        
        # Attacks - Logical/Operational (BLUE)
        {"category": "Attacks", "topic": "Flash Loans", "content": "Flash loans allow borrowing without collateral if repaid in same tx. Used for arbitrage, price manipulation, and governance attacks."},
        {"category": "Attacks", "topic": "Oracle Manipulation", "content": "Price oracles can be manipulated via flash loans. Use time-weighted oracles (TWAP) and multiple sources."},
        {"category": "Attacks", "topic": "DoS Patterns", "content": "Denial of Service via: unbounded loops, failed external calls blocking progress, block gas limit exploitation."},
        {"category": "Attacks", "topic": "Gas Griefing", "content": "Attackers force high gas consumption in victims. Prevent by limiting loop iterations and careful external calls."},
        {"category": "Attacks", "topic": "Signature Malleability", "content": "ECDSA signatures can have multiple valid forms. Use OpenZeppelin ECDSA library for validation."},
        
        # Audit Workflow
        {"category": "Workflow", "topic": "Audit Process", "content": "1. Gather docs 2. Map attack surfaces 3. Manual code review 4. Run automated tools 5. Exploit simulation 6. Confirm exploitability 7. Document findings."},
        {"category": "Workflow", "topic": "Attack Surface", "content": "Enumerate: external calls, token transfers, privileged functions, oracle dependencies, upgradeable interactions, reentrancy entry points."},
        {"category": "Workflow", "topic": "CTF Practice", "content": "Practice exploitation on: Ethernaut, Damn Vulnerable DeFi, Capture The Ether, Paradigm CTF."},
        {"category": "Workflow", "topic": "Postmortem Analysis", "content": "Study real exploits: Flash loan attacks, oracle manipulation, reentrancy variations, upgrade bypass, price manipulation."},
        
        # Reporting
        {"category": "Reporting", "topic": "Findings Format", "content": "Structure: Title, Classification (Red/Yellow/Blue), Impact + Likelihood, Proof-of-Concept, Fix recommendation, Test results."},
        {"category": "Reporting", "topic": "Risk Assessment", "content": "Rate findings by: Severity (Critical/High/Medium/Low) and Likelihood (Certain/Probable/Possible/Improbable)."}
    ]
    
    texts = [item["content"] for item in roadmap_data]
    metadatas = [{"category": item["category"], "topic": item["topic"]} for item in roadmap_data]
    
    logger.info("Ingesting Roadmap Data...")
    store.add_knowledge(texts, metadatas)
    logger.info("Ingestion Complete.")

if __name__ == "__main__":
    ingest_roadmap_data()
