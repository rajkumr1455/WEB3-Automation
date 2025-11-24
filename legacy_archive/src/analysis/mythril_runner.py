import subprocess
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MythrilRunner:
    """
    Runs Mythril symbolic execution on smart contracts.
    """

    def run(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Runs mythril on the target path and returns the JSON report.
        """
        logger.info(f"Running Mythril on {target_path}...")
        
        try:
            # Command: myth analyze <target> -o json
            # Note: Mythril can be slow. We might want to add a timeout in production.
            cmd = ["myth", "analyze", target_path, "-o", "json"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if not result.stdout:
                logger.warning(f"Mythril produced no output. Stderr: {result.stderr}")
                return []

            try:
                data = json.loads(result.stdout)
                return data.get("issues", [])
            except json.JSONDecodeError:
                logger.error("Failed to parse Mythril JSON output.")
                return []

        except Exception as e:
            logger.error(f"Error running Mythril: {e}")
            return []
