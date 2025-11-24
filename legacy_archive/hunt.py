#!/usr/bin/env python3
"""
Web3 Hunter - Automated Smart Contract Vulnerability Scanner
Usage:
    python hunt.py --github https://github.com/user/repo
    python hunt.py --etherscan 0x1234...
    python hunt.py --local path/to/contract.sol
    python hunt.py --local path/to/directory
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.orchestration.hunter_graph import HunterGraph
from src.reporting.report_generator import ReportGenerator
from src.integrations.etherscan_api import EtherscanAPI
from src.ingestion.contract_fetcher import ContractFetcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Web3Hunter:
    """
    Main automation class for vulnerability detection.
    """
    
    def __init__(self, etherscan_api_key: Optional[str] = None):
        self.graph = HunterGraph()
        self.report_gen = ReportGenerator()
        self.etherscan = EtherscanAPI(api_key=etherscan_api_key)
        self.fetcher = ContractFetcher()
    
    def hunt_github(self, repo_url: str) -> List[str]:
        """
        Automatically analyze a GitHub repository.
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🎯 TARGET: GitHub Repository")
        logger.info(f"📍 URL: {repo_url}")
        logger.info(f"{'='*80}\n")
        
        try:
            # Fetch from GitHub
            logger.info("📥 Fetching repository...")
            local_path = self.fetcher.fetch_from_git(repo_url)
            
            if not local_path:
                logger.error("Failed to fetch repository")
                return []
            
            logger.info(f"✓ Cloned to: {local_path}\n")
            
            # Analyze
            return self._analyze_path(local_path, f"GitHub: {repo_url}")
            
        except Exception as e:
            logger.error(f"GitHub analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def hunt_etherscan(self, contract_address: str, chain: str = "ethereum") -> List[str]:
        """
        Automatically analyze a deployed contract from Etherscan.
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🎯 TARGET: Deployed Contract")
        logger.info(f"📍 Address: {contract_address}")
        logger.info(f"⛓️  Chain: {chain}")
        logger.info(f"{'='*80}\n")
        
        try:
            # Fetch source from Etherscan
            logger.info("📥 Fetching contract source from Etherscan...")
            source_data = self.etherscan.get_contract_source(contract_address)
            
            if not source_data or not source_data.get('source_code'):
                logger.error("Contract not verified or not found on Etherscan")
                return []
            
            contract_name = source_data.get('contract_name', 'UnknownContract')
            logger.info(f"✓ Contract: {contract_name}")
            logger.info(f"✓ Compiler: {source_data.get('compiler_version', 'Unknown')}\n")
            
            # Save to temp directory
            temp_dir = Path("data/temp_etherscan")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            contract_file = temp_dir / f"{contract_name}.sol"
            with open(contract_file, 'w', encoding='utf-8') as f:
                f.write(source_data['source_code'])
            
            logger.info(f"✓ Saved to: {contract_file}\n")
            
            # Analyze
            return self._analyze_path(str(temp_dir), f"Etherscan: {contract_address}")
            
        except Exception as e:
            logger.error(f"Etherscan analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def hunt_local(self, path: str) -> List[str]:
        """
        Automatically analyze local contract(s).
        """
        target_path = Path(path)
        
        if not target_path.exists():
            logger.error(f"Path not found: {path}")
            return []
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🎯 TARGET: Local {'Directory' if target_path.is_dir() else 'File'}")
        logger.info(f"📍 Path: {target_path.absolute()}")
        logger.info(f"{'='*80}\n")
        
        return self._analyze_path(str(target_path.absolute()), f"Local: {path}")
    
    def _analyze_path(self, path: str, target_name: str) -> List[str]:
        """
        Core analysis logic for any path (directory or file).
        """
        path_obj = Path(path)
        
        # Find all Solidity files
        if path_obj.is_file():
            sol_files = [path_obj] if path_obj.suffix == '.sol' else []
        else:
            sol_files = list(path_obj.rglob("*.sol"))
            # Filter out tests and libs
            sol_files = [
                f for f in sol_files
                if not any(x in str(f).lower() for x in ['test', 'mock', 'lib/', '.t.sol', 'script'])
            ]
        
        if not sol_files:
            logger.warning("No Solidity contracts found")
            return []
        
        logger.info(f"🔍 Found {len(sol_files)} contract(s) to analyze\n")
        
        reports = []
        for idx, sol_file in enumerate(sol_files, 1):
            logger.info(f"{'─'*80}")
            logger.info(f"📝 [{idx}/{len(sol_files)}] Analyzing: {sol_file.name}")
            logger.info(f"{'─'*80}\n")
            
            try:
                # Run HunterGraph workflow
                state = {
                    "target_url": target_name,
                    "local_path": str(sol_file.parent.absolute()),
                    "slither_results": [],
                    "flattened_code": "",
                    "vulnerabilities": ""
                }
                
                result = self.graph.analyze_node(state)
                
                # Extract results
                flattened_code = result.get('flattened_code', '')
                slither_results = result.get('slither_results', [])
                vulns_str = result.get('vulnerabilities', '{}')
                
                logger.info(f"   ✓ Source: {len(flattened_code)} bytes")
                logger.info(f"   ✓ Slither: {len(slither_results)} issues")
                
                # Generate report
                report_path = self.report_gen.generate_html_report(
                    contract_name=sol_file.stem,
                    source_code=flattened_code,
                    findings=vulns_str,
                    slither_results=slither_results,
                    poc_code=result.get('poc_code', '')
                )
                
                reports.append(report_path)
                logger.info(f"   📊 Report: {Path(report_path).name}\n")
                
            except Exception as e:
                logger.error(f"   ❌ Analysis failed: {e}\n")
                continue
        
        # Summary
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ SCAN COMPLETE")
        logger.info(f"   Contracts Analyzed: {len(sol_files)}")
        logger.info(f"   Reports Generated: {len(reports)}")
        logger.info(f"   Reports Location: data/reports/")
        logger.info(f"{'='*80}\n")
        
        return reports

def main():
    parser = argparse.ArgumentParser(
        description="Web3 Hunter - Automated Smart Contract Vulnerability Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze GitHub repository
  python hunt.py --github https://github.com/OpenZeppelin/openzeppelin-contracts
  
  # Analyze deployed contract
  python hunt.py --etherscan 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984
  
  # Analyze local contract
  python hunt.py --local contracts/MyToken.sol
  
  # Analyze local directory
  python hunt.py --local contracts/
        """
    )
    
    # Input sources (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--github', help='GitHub repository URL')
    input_group.add_argument('--etherscan', help='Contract address on Etherscan')
    input_group.add_argument('--local', help='Local file or directory path')
    
    # Optional arguments
    parser.add_argument('--etherscan-key', help='Etherscan API key (optional)')
    parser.add_argument('--chain', default='ethereum', help='Blockchain network (default: ethereum)')
    
    args = parser.parse_args()
    
    # Initialize hunter
    hunter = Web3Hunter(etherscan_api_key=args.etherscan_key)
    
    # Run analysis based on input type
    if args.github:
        reports = hunter.hunt_github(args.github)
    elif args.etherscan:
        reports = hunter.hunt_etherscan(args.etherscan, args.chain)
    elif args.local:
        reports = hunter.hunt_local(args.local)
    
    # Exit code based on success
    sys.exit(0 if reports else 1)

if __name__ == "__main__":
    main()
