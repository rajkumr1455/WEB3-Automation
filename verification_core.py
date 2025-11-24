import os
import subprocess
import json
import time
import requests
from typing import Dict, Any, Optional

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = "qwen2.5-coder:7b"

def generate_test_harness(finding: Dict[str, Any], source_code: str) -> str:
    """
    Generates a Foundry test file content using local LLM.
    """
    prompt = f"""
You are an expert security researcher and Foundry developer.
Your task is to write a Foundry test (`.t.sol`) to verify a potential vulnerability.

Vulnerability Details:
Type: {finding.get('vuln_type')}
File: {finding.get('file')}
Details: {finding.get('details')}

Target Contract Source Code:
```solidity
{source_code}
```

Instructions:
1. Create a test contract inheriting from `Test`.
2. Setup the environment (deploy the target contract).
3. Write a test function `testExploit()` that attempts to trigger the vulnerability.
4. If the vulnerability exists, the test should PASS (proving the exploit works) or FAIL with a specific revert if checking for a bug that causes a revert. 
   - For Reentrancy/Logic bugs: The test should assert the exploited state (e.g., stolen funds).
   - For Access Control: The test should try to call a restricted function as an attacker.
5. Assume standard Foundry std-libs are available.
6. Return ONLY the Solidity code for the test file. Do not include markdown formatting or explanation.

Output:
"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2 # Lower temp for code generation
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        text = result.get("response", "").strip()
        
        # Clean up markdown code blocks if present
        if "```solidity" in text:
            text = text.split("```solidity")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return text
    except Exception as e:
        print(f"Error generating test: {e}")
        return ""

def run_forge_test(test_file_path: str) -> Dict[str, Any]:
    """
    Runs `forge test` on the generated file.
    """
    try:
        # Assuming forge is installed and we are in a foundry project root or can run it.
        # We might need to handle project structure. For now, we assume we can run it.
        cmd = ["forge", "test", "--match-path", test_file_path, "--json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        output = result.stdout.strip()
        # Parse JSON output from forge if possible, or just check return code/stdout
        # Forge json output is a bit complex, sometimes multiple lines.
        
        success = result.returncode == 0
        
        return {
            "success": success,
            "output": output,
            "command": " ".join(cmd)
        }
    except FileNotFoundError:
        return {"success": False, "output": "Forge executable not found", "command": ""}
    except Exception as e:
        return {"success": False, "output": str(e), "command": ""}

def verify_finding(finding: Dict[str, Any], source_code: str) -> Dict[str, Any]:
    """
    Orchestrates the verification process.
    """
    print(f"Generating verification test for {finding['vuln_type']}...", flush=True)
    test_code = generate_test_harness(finding, source_code)
    
    if not test_code:
        return {"verified": False, "reason": "Failed to generate test harness"}
    
    # Save test file
    # We need a place to put it. `test/generated/`
    test_dir = "test/generated"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a unique filename
    safe_type = "".join(x for x in finding['vuln_type'] if x.isalnum())
    filename = f"Exploit_{safe_type}_{int(time.time())}.t.sol"
    file_path = os.path.join(test_dir, filename)
    
    with open(file_path, "w") as f:
        f.write(test_code)
        
    print(f"Saved test to {file_path}. Running forge test...", flush=True)
    
    result = run_forge_test(file_path)
    
    # Analyze result
    # If test passed, it means exploit succeeded (based on prompt instructions)
    verified = result["success"]
    
    return {
        "verified": verified,
        "test_file": file_path,
        "forge_output": result["output"]
    }
