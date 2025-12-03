import logging
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.knowledge.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_2025_threats():
    """
    Ingests 2025-specific vulnerability patterns and emerging threats
    """
    store = VectorStore()
    
    # 2025 Emerging Threats
    threats_2025 = [
        # MEV Attacks
        {"category": "MEV", "topic": "Sandwich Attacks", "content": "MEV bots front-run and back-run user transactions to extract value. Protection: Use deadlines, slippage limits, private mempools (Flashbots), or commit-reveal schemes."},
        {"category": "MEV", "topic": "Front-Running", "content": "Miners/validators reorder transactions to profit. Vulnerable: DEX swaps, liquidations, NFT mints. Mitigation: Commit-reveal, submarine sends, fair ordering protocols."},
        {"category": "MEV", "topic": "Back-Running", "content": "Execute transaction immediately after target tx. Common in arbitrage and liquidations. Protection: Private transaction submission (Flashbots Protect)."},
        {"category": "MEV", "topic": "Time-Bandit Attacks", "content": "Validators reorganize blocks to extract MEV from past blocks. Risk in PoS with weak finality. Use: Longer confirmation times for high-value transactions."},
        
        # Cross-Chain Vulnerabilities
        {"category": "CrossChain", "topic": "Bridge Replay Attacks", "content": "Transactions replayed across different chains if chainId not validated. Fix: Include chainId in all signatures and verify it against block.chainid."},
        {"category": "CrossChain", "topic": "Bridge Message Validation", "content": "Improper validation of cross-chain messages leads to unauthorized actions. Verify: Message origin, signature, nonce, and destination chain."},
        {"category": "CrossChain", "topic": "Atomic Swap Failures", "content": "Failed swaps on one chain can lock funds on another. Use: Timelock-based refunds and proper state synchronization."},
        {"category": "CrossChain", "topic": "Liquidity Fragmentation", "content": "Bridges split liquidity across chains creating price manipulation opportunities. Monitor: Cross-chain price differentials and arbitrage patterns."},
        
        # Layer 2 Risks
        {"category": "Layer2", "topic": "Optimistic Rollup Fraud Proofs", "content": "Fraud proof windows create risks. Invalid state roots can be challenged within ~7 days. Ensure: Robust challenge mechanisms and validator incentives."},
        {"category": "Layer2", "topic": "Sequencer Centralization", "content": "Centralized sequencers can censor txs or manipulate ordering. Risk: MEV extraction, censorship. Use: Decentralized sequencer networks or forced inclusion."},
        {"category": "Layer2", "topic": "ZK-Rollup Circuit Bugs", "content": "Bugs in zero-knowledge circuits can break soundness. Ensure: Formal verification of circuits, audited proof systems (Groth16, PLONK)."},
        {"category": "Layer2", "topic": "State Root Validation", "content": "Improper L2->L1 state root validation enables invalid withdrawals. Verify: Merkle proofs, state commitments, and challenge periods."},
        {"category": "Layer2", "topic": "Timestamp Manipulation", "content": "L2 sequencers control timestamps. Don't rely on block.timestamp for critical logic. Use: Block numbers or L1 anchoring."},
        
        # ERC-4337 Account Abstraction
        {"category": "ERC4337", "topic": "Paymaster Drain", "content": "Paymasters without validation can be drained by malicious UserOperations. Implement: validatePaymasterUserOp with strict gas and value checks."},
        {"category": "ERC4337", "topic": "UserOp Signature Validation", "content": "Invalid signature checks allow unauthorized operations. Use: ECDSA.recover and verify against account owner. Check nonce to prevent replay."},
        {"category": "ERC4337", "topic": "EntryPoint Griefing", "content": "Malicious bundlers can grief accounts by submitting failing UserOps. Mitigation: Simulate ops before submission, use trusted bundlers."},
        {"category": "ERC4337", "topic": "Gas Sponsor Exploitation", "content": "Attackers abuse gas sponsorship to drain paymasters. Limit: Sponsored gas per user, implement whitelist/blacklist, rate limiting."},
        
        # Upgradeable Contract Risks
        {"category": "Upgrades", "topic": "Storage Collision", "content": "Upgrading contracts without storage gaps causes variable collisions. Reserve: uint256[50] __gap in base contracts. Use transparent upgrade pattern."},
        {"category": "Upgrades", "topic": "Initialize Front-Running", "content": "Unprotected initializer allows attackers to initialize first. Use: initializer modifier, deploy and initialize atomically, or disable initializers in implementation."},
        {"category": "Upgrades", "topic": "Selfdestruct in Implementation", "content": "Selfdestruct in implementation bricks proxy permanently. Never: Use selfdestruct in upgradeable contracts. Alternative: Pause mechanisms."},
        {"category": "Upgrades", "topic": "Constructor in Upgradeable", "content": "Constructors don't execute when called via proxy. State initialized in constructor is lost. Use: initializer functions instead."},
        
        # DeFi-Specific 2025 Threats
        {"category": "DeFi2025", "topic": "Flash Loan Governance Attacks", "content": "Attackers use flash loans to temporarily gain voting power in governance. Protection: Time-weighted voting, vote delegation locks, snapshot-based governance."},
        {"category": "DeFi2025", "topic": "Read-Only Reentrancy", "content": "View functions called during state transitions return stale data. Vulnerable: Price oracles, balance checks. Use: Reentrancy guards even on view functions."},
        {"category": "DeFi2025", "topic": "Curve LP Reentrancy", "content": "Curve and Balancer LP tokens vulnerable to read-only reentrancy via callback hooks. Use: Check-effects-interactions even for view calls."},
        {"category": "DeFi2025", "topic": "Oracle Staleness", "content": "Stale oracle prices enable arbitrage and liquidations. Enforce: Heartbeat checks, compare multiple oracles (Chainlink, Uniswap TWAP, Band)."},
        
        # NFT & Gaming
        {"category": "NFT2025", "topic": "Metadata Manipulation", "content": "Mutable metadata in NFT contracts allows rug pulls. Use: IPFS with CID verification or on-chain metadata for critical attributes."},
        {"category": "NFT2025", "topic": "Royalty Bypass", "content": "NFT marketplaces bypassing ERC2981 royalties. Not enforceable on-chain. Consider: Operator filtering (OpenSea's OperatorFilter)."},
        {"category": "NFT2025", "topic": "Rarity Snipping", "content": "Bots analyze rarity before reveal and snipe valuable traits. Use: Commit-reveal minting or VRF-based randomness."},
        
        # Privacy & Compliance
        {"category": "Privacy2025", "topic": "Tornado Cash Compliance", "content": "Privacy mixers face regulatory scrutiny. Risk: Sanctions on addresses interacting with mixers. Consider: Compliant privacy solutions (Aztec, Railgun with compliance)."},
        {"category": "Privacy2025", "topic": "On-Chain Data Leakage", "content": "Private data revealed via events or storage. Even deleted data remains in history. Encrypt: Sensitive data off-chain or use zk-SNARKs."},
        
        # Gas & Performance
        {"category": "Gas2025", "topic": "EIP-1559 Priority Fee", "content": "Insufficient priority fees cause tx delays in congestion. Set: Adaptive base fee + priority fee based on network conditions."},
        {"category": "Gas2025", "topic": "Blob Transactions EIP-4844", "content": "Proto-danksharding introduces blob transactions for L2 data availability. Understand: Blob gas pricing, KZG commitments for L2 rollups."}
    ]
    
    texts = [f"[{item['category']}] {item['topic']}: {item['content']}" for item in threats_2025]
    metadatas = [{"category": item["category"], "topic": item["topic"], "year": "2025"} for item in threats_2025]
    
    logger.info(f"Ingesting {len(threats_2025)} 2025-specific threats...")
    store.add_knowledge(texts, metadatas)
    logger.info("2025 Threats ingestion complete.")
    
    return len(threats_2025)

if __name__ == "__main__":
    count = ingest_2025_threats()
    print(f"\nIngested {count} cutting-edge 2025 vulnerability patterns")
    print("   Coverage expanded to include:")
    print("   - MEV Attacks (4 patterns)")
    print("   - Cross-Chain Risks (4 patterns)")
    print("   - Layer 2 Issues (5 patterns)")
    print("   - ERC-4337 Account Abstraction (4 patterns)")
    print("   - Upgradeable Contract Risks (4 patterns)")
    print("   - DeFi 2025 Threats (4 patterns)")
    print("   - NFT/Gaming (3 patterns)")
    print("   - Privacy & Compliance (2 patterns)")
    print("   - Gas & Performance (2 patterns)")
