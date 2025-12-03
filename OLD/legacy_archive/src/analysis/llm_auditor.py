import logging
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

import yaml
from langchain_community.chat_models import ChatOllama

class LLMAuditor:
    """
    Agent responsible for analyzing smart contracts using LLM.
    """

    def __init__(self):
        with open("config/settings.yaml", "r") as f:
            config = yaml.safe_load(f)
            
        self.llm = ChatOllama(
            base_url=config["llm"]["base_url"],
            api_key="ollama",  # Ollama doesn't need a real key
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"]
        )

    def analyze(self, source_code: str, slither_results: List[Dict[str, Any]], context: List[str] = []) -> str:
        """
        Analyzes the source code and slither results to find vulnerabilities.
        """
        logger.info("Starting LLM analysis...")

        # Format Slither results for the prompt
        slither_summary = json.dumps(slither_results, indent=2) if slither_results else "No issues found by Slither."
        
        # Format Context
        rag_context = "\n".join([f"- {c}" for c in context]) if context else "No relevant past knowledge found."

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Smart Contract Security Auditor with expertise in 2025 Web3 threats.
Your goal is to find ALL vulnerabilities and classify them using the comprehensive Threat Model below:

RED (High/Critical Severity):
- Reentrancy (classic, cross-function, read-only)
- Integer Overflow/Underflow
- Signature Replay & Malleability
- Weak Randomness (blockhash, timestamp)
- Access Control / tx.origin Authorization
- Unprotected Self-destruct
- Hash Collisions (abi.encodePacked with dynamic types)
- MEV Front-Running & Sandwich Attacks
- Cross-Chain Replay Attacks (missing chainId)
- Bridge Message Validation Failures
- Layer 2 Fraud Proof Vulnerabilities
- ERC-4337 Paymaster Drain
- Proxy Storage Collisions
- Unprotected Upgrade Functions
- Flash Loan Governance Attacks

YELLOW (Config & Coding):
- Deprecated Functions (suicide, throw, sha3)
- Floating Pragma (^0.8.0)
- Visibility Issues (missing public/private/internal)
- Hardcoded Gas Amounts
- Input Validation Missing
- Code With No Effects (dead code)
- Constructor in Upgradeable Contracts
- State Variable Default Visibility
- Uninitialized Storage Pointers

BLUE (Logical & Operational):
- Gas Griefing & DoS with Block Gas Limit
- Oracle Manipulation (price feeds, TWAP)
- DoS with Failed Call (unbounded loops)
- Unchecked Return Values (call, send)
- Unencrypted Private Data On-Chain
- Timestamp Manipulation (block.timestamp)
- Layer 2 Sequencer Centralization
- MEV Liquidation Front-Running
- NFT Metadata Manipulation
- Read-Only Reentrancy (Curve LP)
- Oracle Staleness

2025 EMERGING THREATS (Auto-classify severity):
- Cross-Chain Bridge Atomicity Failures
- ZK-Rollup Circuit Bugs
- ERC-4337 UserOp Signature Validation
- EntryPoint Griefing
- Proxy Initialize Front-Running
- Selfdestruct in Implementation
- L2 State Root Validation
- Blob Transaction Issues (EIP-4844)
- Gas Sponsor Exploitation
- Royalty Bypass (ERC-2981)
- Rarity Snipping (NFT reveals)
- Tornado Cash Compliance Risks

Output Format (JSON only):
{{
  "vulnerabilities": [
    {{
      "name": "Exact Vulnerability Name",
      "category": "RED" | "YELLOW" | "BLUE",
      "description": "Detailed description with impact and affected code",
      "location": "Function name or line numbers",
      "severity": "Critical" | "High" | "Medium" | "Low"
    }}
  ]
}}

IMPORTANT: 
- Analyze EVERY function and state variable
- Check for ALL patterns above
- If no bugs are found, return: {{"vulnerabilities": []}}
- Do NOT include markdown formatting like ```json
- Return ONLY the raw JSON string"""),
            ("user", """Context (Known Patterns/CVEs):
{rag_context}

Static Analysis Results (Slither + Advanced Detectors):
{slither_summary}

Target Contract Code:
```solidity
{source_code}
```

Perform comprehensive analysis covering:
1. All RED/YELLOW/BLUE categories
2. 2025 emerging threats (MEV, Cross-chain, Layer 2, ERC-4337, Proxy)
3. DeFi-specific risks (flash loans, oracles, governance)
4. NFT/Gaming vulnerabilities

Return detailed JSON with ALL findings:""")
        ])

        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = chain.invoke({
                "source_code": source_code,
                "slither_summary": slither_summary,
                "rag_context": rag_context
            })
            return response
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return "Error during analysis."

import json
