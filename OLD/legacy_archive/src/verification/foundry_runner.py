import subprocess
import logging
import os

logger = logging.getLogger(__name__)

class FoundryRunner:
    """
    Runs Foundry (forge) tests.
    """

    def run_test(self, test_path: str, project_root: str, fuzz_runs: int = None) -> bool:
        """
        Runs a specific Foundry test file.
        Returns True if the test passed, False otherwise.
        """
        logger.info(f"Running Foundry test: {test_path}...")
        
        try:
            # Prepare environment with local Foundry path
            env = os.environ.copy()
            foundry_path = os.path.abspath("foundry")
            if os.path.exists(foundry_path):
                env["PATH"] = foundry_path + os.pathsep + env["PATH"]

            # Command: forge test --match-path <test_path> -vv
            # Use absolute path to forge.exe
            forge_bin = os.path.join(foundry_path, "forge.exe")
            cmd = [forge_bin, "test", "--match-path", test_path, "-vv"]
            
            if fuzz_runs:
                cmd.extend(["--fuzz-runs", str(fuzz_runs)])
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, check=False, env=env)
            
            if result.returncode == 0:
                logger.info("Test Passed!")
                return True
            else:
                logger.warning(f"Test Failed.\nStdout: {result.stdout}\nStderr: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error running Foundry: {e}")
            return False
