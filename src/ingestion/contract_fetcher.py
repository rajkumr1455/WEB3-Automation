import os
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ContractFetcher:
    """
    Fetches smart contract source code from various sources.
    """

    def __init__(self, data_dir: str = "data/contracts"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_from_git(self, repo_url: str, commit_hash: Optional[str] = None) -> str:
        """
        Clones a git repository and optionally checks out a specific commit.
        Returns the path to the cloned repository.
        """
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        target_dir = os.path.join(self.data_dir, repo_name)

        if os.path.exists(target_dir):
            logger.info(f"Repository already exists at {target_dir}. Pulling latest changes...")
            subprocess.run(["git", "-C", target_dir, "pull"], check=True)
        else:
            logger.info(f"Cloning {repo_url} to {target_dir}...")
            subprocess.run(["git", "clone", repo_url, target_dir], check=True)

        if commit_hash:
            logger.info(f"Checking out commit {commit_hash}...")
            subprocess.run(["git", "-C", target_dir, "checkout", commit_hash], check=True)

        return target_dir

    def fetch_from_etherscan(self, address: str, chain: str = "mainnet") -> str:
        """
        Fetches contract source code from Etherscan (Placeholder).
        """
        # TODO: Implement Etherscan API integration
        logger.warning("Etherscan fetching not yet implemented.")
        return ""
