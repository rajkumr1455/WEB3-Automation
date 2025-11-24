import os
import json
import time
import requests
from typing import Dict, Any

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = "qwen2.5-coder:7b"

def analyze_finding(finding: Dict[str, Any], source_code: str) -> Dict[str, Any]:
    """
    Analyzes a finding to determine if it's a false positive using local LLM.
    """
    prompt = f"""
You are a smart contract auditor.
Here is a potential vulnerability:
Tool: {finding.get('tool')}
Type: {finding.get('vuln_type')}
Severity: {finding.get('severity')}
Details: {finding.get('details')}
File: {finding.get('file')}
Line: {finding.get('line')}

Here is the source code context:
```solidity
{source_code}
```

Determine if this is a False Positive. 
- If the function has modifiers like `nonReentrant` or `onlyOwner` that mitigate the issue, it is likely a False Positive.
- If the logic is sound, it is a True Positive.

Return ONLY a valid JSON object with the following structure:
{{
  "is_valid": bool, 
  "confidence": float, 
  "reasoning": "string"
}}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    retries = 3
    for attempt in range(retries):
        try:
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            text = result.get("response", "").strip()
            
            # Clean up markdown code blocks if present (though format: json should help)
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            return json.loads(text)
        except Exception as e:
            print(f"LLM Error (Attempt {attempt+1}): {e}")
            time.sleep(1)
            continue
    
    return {"error": "LLM failed", "is_valid": True, "confidence": 0.0, "reasoning": "LLM failed to respond"}

if __name__ == "__main__":
    # Test run
    sample_finding = {
        "tool": "slither",
        "vuln_type": "reentrancy",
        "file": "Vault.sol",
        "line": 10,
        "severity": "High",
        "details": "Reentrancy in withdraw function"
    }
    sample_code = """
    contract Vault {
        mapping(address => uint) public balances;
        bool locked;

        modifier nonReentrant() {
            require(!locked, "Reentrant");
            locked = true;
            _;
            locked = false;
        }

        function withdraw() public nonReentrant {
            uint amount = balances[msg.sender];
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success);
            balances[msg.sender] = 0;
        }
    }
    """
    print(json.dumps(analyze_finding(sample_finding, sample_code), indent=2))
