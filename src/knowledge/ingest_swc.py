import logging
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.knowledge.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_swc_registry():
    """
    Ingests SWC (Smart Contract Weakness Classification) Registry data.
    """
    store = VectorStore()
    
    # SWC Registry - Common Smart Contract Weaknesses
    swc_data = [
        {"id": "SWC-101", "category": "Attacks", "topic": "Integer Overflow", "content": "Integer overflow/underflow occurs when arithmetic operations exceed type limits. In Solidity <0.8, use SafeMath. In >=0.8, overflow checks are built-in unless using unchecked{}."},
        {"id": "SWC-107", "category": "Attacks", "topic": "Reentrancy", "content": "Reentrancy allows external contract to callback before state update. Classic example: DAO hack. Fix: Checks-Effects-Interactions pattern, ReentrancyGuard, or pull-over-push."},
        {"id": "SWC-115", "category": "Attacks", "topic": "Authorization via tx.origin", "content": "Using tx.origin for authorization is vulnerable to phishing. Always use msg.sender instead. tx.origin returns original transaction sender, not immediate caller."},
        {"id": "SWC-120", "category": "Attacks", "topic": "Weak Randomness", "content": "Using blockhash, timestamp, or block.number for randomness is predictable by miners. Use Chainlink VRF, commit-reveal, or other secure sources."},
        {"id": "SWC-131", "category": "Attacks", "topic": "Signature Malleability", "content": "ECDSA signatures can be flipped (v->v'). Use OpenZeppelin ECDSA library which checks for malleability. Include nonce and chainId in signed messages."},
        {"id": "SWC-114", "category": "Attacks", "topic": "Transaction Order Dependence", "content": "Front-running and MEV attacks exploit transaction ordering. Mitigate with commit-reveal, batch processing, or submarine sends."},
        {"id": "SWC-116", "category": "Attacks", "topic": "Time Manipulation", "content": "Block timestamp can be manipulated by miners within ~15 seconds. Don't use for critical logic. Use block.number for time-based conditions."},
        {"id": "SWC-104", "category": "Logic", "topic": "Unchecked Call Return Value", "content": "Low-level calls (call, delegatecall, send) don't revert on failure. Always check return value or use transfer/require pattern."},
        {"id": "SWC-105", "category": "Logic", "topic": "Unprotected Ether Withdrawal", "content": "Missing access control on withdrawal functions. Use onlyOwner or proper role-based access control (OpenZeppelin AccessControl)."},
        {"id": "SWC-106", "category": "Logic", "topic": "Unprotected SELFDESTRUCT", "content": "Unprotected selfdestruct can destroy contract and send all funds. Implement access control and consider upgrade patterns instead."},
        {"id": "SWC-103", "category": "Config", "topic": "Floating Pragma", "content": "Using ^0.8.0 allows any 0.8.x version. Lock to specific version in production: pragma solidity 0.8.20;"},
        {"id": "SWC-108", "category": "Config", "topic": "State Variable Default Visibility", "content": "State variables without visibility default to internal. Always explicitly declare: public, private, internal, or external."},
        {"id": "SWC-100", "category": "Config", "topic": "Function Default Visibility", "content": "Functions without visibility are public. Explicitly declare to avoid unintended exposure: public, external, internal, private."},
        {"id": "SWC-102", "category": "Logic", "topic": "Outdated Compiler Version", "content": "Old compilers have known bugs. Use latest stable: >=0.8.20. Check known bugs: solidity.readthedocs.io"},
        {"id": "SWC-118", "category": "Logic", "topic": "Incorrect Constructor Name", "content": "Pre-0.5.0: constructor had contract name. Now use constructor() keyword. Misnamed functions are regular functions."},
        {"id": "SWC-127", "category": "Logic", "topic": "Arbitrary Jump with Function Type Variable", "content": "Don't use assembly jumps with function pointers. Can lead to arbitrary code execution."},
        {"id": "SWC-109", "category": "Config", "topic": "Uninitialized Storage Pointer", "content": "In <0.5.0, uninitialized struct/array pointed to storage slot 0. Use memory keyword explicitly or upgrade compiler."},
        {"id": "SWC-134", "category": "Attacks", "topic": "Message call with hardcoded gas", "content": "Using .gas(amount) can break due to EIP-150 or future gas cost changes. Let EVM provide gas automatically."},
        {"id": "SWC-132", "category": "Attacks", "topic": "Unexpected Ether Balance", "content": "Contract balance can be force-fed via selfdestruct. Don't rely on this.balance for logic. Track deposits explicitly."},
        {"id": "SWC-113", "category": "Logic", "topic": "DoS with Failed Call", "content": "Iterating over unbounded array with external calls can hit gas limit or fail. Use withdraw pattern instead of push payments."},
    ]
    
    texts = [f"[{item['id']}] {item['topic']}: {item['content']}" for item in swc_data]
    metadatas = [{"swc_id": item["id"], "category": item["category"], "topic": item["topic"]} for item in swc_data]
    
    logger.info(f"Ingesting {len(swc_data)} SWC Registry entries...")
    store.add_knowledge(texts, metadatas)
    logger.info("SWC Registry ingestion complete.")

if __name__ == "__main__":
    ingest_swc_registry()
