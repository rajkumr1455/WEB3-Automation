import os
import subprocess
import logging
import sys

logger = logging.getLogger(__name__)

class SolidityFlattener:
    """
    Flattens Solidity contracts using slither-flat.
    """

    def flatten(self, contract_path: str, output_dir: str) -> str:
        """
        Flattens a Solidity contract.
        Returns the path to the flattened file.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Construct the output filename
        base_name = os.path.basename(contract_path)
        flat_name = base_name.replace(".sol", ".flat.sol")
        output_path = os.path.join(output_dir, flat_name)

        logger.info(f"Flattening {contract_path} to {output_dir}...")

        try:
            # Prepare environment with local Foundry path
            env = os.environ.copy()

            # Use python -m slither.tools.flattening.main to avoid script path issues
            # The slither-flat tool expects the output directory as the last argument
            # and the contract path as the second to last.
            # It also expects the output directory to be created beforehand.
            cmd = [sys.executable, "-m", "slither.tools.flattening.main", contract_path, output_dir]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                env=env
            )
            logger.debug(f"Slither-flat stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"Slither-flat stderr: {result.stderr}")

            # Slither-flat creates a file named after the main contract in the output_dir
            # We need to find that file.
            # The tool doesn't directly return the path, so we infer it.
            # It usually names it <ContractName>.sol or similar.
            # We'll look for the newest file in the output dir that ends with .sol
            files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.sol')]
            if not files:
                logger.error(f"No .sol files found in output directory {output_dir} after flattening.")
                return ""
                
            # Return the most recently modified file
            return max(files, key=os.path.getmtime)

        except Exception as e:
            logger.error(f"Error during flattening: {e}")
            return ""

    def get_main_contract(self, repo_path: str) -> str:
        """
        Identifies the main contract file in a repository.
        Heuristic: Look for contracts in 'src' or 'contracts' dir, 
        prioritize files that import others or have matching name to repo.
        """
        candidates = []
        for root, _, files in os.walk(repo_path):
            if "test" in root.lower() or "script" in root.lower() or "lib" in root.lower():
                continue
            for file in files:
                if file.endswith(".sol"):
                    candidates.append(os.path.join(root, file))
        
        if not candidates:
            return ""
            
        # Simple heuristic: Return the largest file (likely contains main logic)
        # or the one with "Router", "Factory", "Manager" in name
        # For now, just largest
        return max(candidates, key=os.path.getsize)
