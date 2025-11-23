import subprocess
import json
import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SlitherRunner:
    """
    Runs Slither static analysis on smart contracts.
    """

    def run(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Runs slither on the target path (file or directory) and returns the JSON report.
        """
        try:
            # Convert to absolute path for Windows compatibility
            abs_target = os.path.abspath(target_path)
            
            # Prepare environment with local Foundry path
            import sys
            env = os.environ.copy()
            env["SOLC"] = "solc"
            
            foundry_path = os.path.abspath("foundry")
            if os.path.exists(foundry_path):
                env["PATH"] = foundry_path + os.pathsep + env["PATH"]

            # Run Slither via python module
            cmd = [sys.executable, "-m", "slither", abs_target, "--json", "-"]
            
            logger.info(f"Running Slither on {abs_target}...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, encoding='utf-8', env=env)
            
            if not result.stdout:
                logger.warning(f"Slither produced no output. Stderr: {result.stderr}")
                return []

            try:
                data = json.loads(result.stdout)
                return data.get("results", {}).get("detectors", [])
            except json.JSONDecodeError:
                # Sometimes slither outputs logs before the JSON
                # Try to find the first '{'
                start_idx = result.stdout.find('{')
                if start_idx != -1:
                    try:
                        data = json.loads(result.stdout[start_idx:])
                        return data.get("results", {}).get("detectors", [])
                    except:
                        pass
                
                logger.error("Failed to parse Slither JSON output.")
                return []

        except Exception as e:
            logger.error(f"Error running Slither: {e}")
            return []

    def generate_call_graph(self, target_path: str, output_dir: str = "data/graphs") -> str:
        """
        Generates a call graph using Slither's printer.
        Returns the path to the generated DOT file.
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Generating call graph for {target_path}...")
        
        try:
            # Command: slither <target> --print call-graph
            # We run this in the output directory so the dot file is generated there?
            # Slither usually generates files in the current working directory.
            # So we might need to change cwd or move the file.
            
            # Use python -m slither for Windows compatibility
            cmd = ["python", "-m", "slither", target_path, "--print", "call-graph"]
            
            # Run in the output directory to capture the dot file there
            # But target_path must be absolute or relative to output_dir
            abs_target_path = os.path.abspath(target_path)
            
            # Prepare environment with solc path
            env = os.environ.copy()
            solc_dir = os.path.expanduser("~/.solc-select/artifacts/solc-0.8.20")
            solc_bin = os.path.join(solc_dir, "solc.exe")
            if os.path.exists(solc_dir):
                env["PATH"] = solc_dir + os.pathsep + env["PATH"]
            if os.path.exists(solc_bin):
                env["SOLC"] = solc_bin
            
            result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True, check=False, env=env)
            
            if result.returncode != 0 and "Error" in result.stderr:
                logger.warning(f"Slither call-graph generation warning: {result.stderr}")
            
            # Find the generated dot file
            # Usually named all_contracts.call-graph.dot or <Contract>.call-graph.dot
            files = [f for f in os.listdir(output_dir) if f.endswith('.dot')]
            if not files:
                logger.warning("No DOT file generated.")
                return ""
                
            # Return the most recently modified dot file
            latest_file = max([os.path.join(output_dir, f) for f in files], key=os.path.getmtime)
            return latest_file

        except Exception as e:
            logger.error(f"Error generating call graph: {e}")
            return ""
