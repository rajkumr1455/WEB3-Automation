import subprocess
import json
import logging
import sys
from typing import Dict, Any, List

logger = logging.getLogger("SlitherWrapper")

class SlitherWrapper:
    def run(self, target: str) -> List[Dict[str, Any]]:
        """
        Run Slither on the target file/directory and return structured findings.
        """
        logger.info(f"Running Slither on {target}...")
        try:
            cmd = [sys.executable, "-m", "slither", target, "--json", "-"]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            output = result.stdout.strip()
            logger.info(f"Slither Output: {output[:500]}...") # Log first 500 chars
            if not output:
                logger.warning("Slither returned empty output.")
                return []

            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                # Fallback for mixed output
                if "{" in output:
                    start = output.find("{")
                    try:
                        data = json.loads(output[start:])
                    except json.JSONDecodeError:
                        return []
                else:
                    return []

            findings = []
            if "results" in data and "detectors" in data["results"]:
                for d in data["results"]["detectors"]:
                    findings.append({
                        "type": d.get("check", "Unknown"),
                        "severity": d.get("impact", "Medium"),
                        "description": d.get("description", ""),
                        "location": d.get("elements", [{}])[0].get("source_mapping", {})
                    })
            return findings

        except Exception as e:
            logger.error(f"Error running Slither: {e}")
            return [{"error": str(e)}]

if __name__ == "__main__":
    wrapper = SlitherWrapper()
    # Test (requires a file)
    # print(wrapper.run("test.sol"))
