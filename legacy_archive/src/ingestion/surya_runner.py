import subprocess
import logging
import os

logger = logging.getLogger(__name__)

class SuryaRunner:
    """
    Runs Sūrya to generate visualization graphs.
    """

    def generate_graph(self, target_path: str, output_dir: str) -> str:
        """
        Generates a call graph using Sūrya.
        Returns the path to the generated dot file.
        """
        logger.info(f"Running Sūrya on {target_path}...")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "call_graph.dot")
        
        try:
            # Command: surya graph <target> > output.dot
            # We use shell=True for the redirection, or handle it in python
            cmd = ["surya", "graph", target_path]
            
            with open(output_file, "w") as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=False)
            
            if result.returncode != 0:
                logger.warning(f"Sūrya failed. Stderr: {result.stderr}")
                return ""
                
            return output_file

        except Exception as e:
            logger.error(f"Error running Sūrya: {e}")
            return ""
