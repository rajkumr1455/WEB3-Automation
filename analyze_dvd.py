import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestration.hunter_graph import HunterGraph
from src.reporting.report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_dvd_contract(challenge_name: str):
    """
    Analyzes a Damn Vulnerable DeFi contract and generates a report.
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Analyzing DVD Challenge: {challenge_name}")
    logger.info(f"{'='*80}\n")
    
    # Initialize graph
    graph = HunterGraph()
    report_gen = ReportGenerator()
    
    # Path to DVD challenge
    dvd_base = Path(os.getcwd()) / "damn-vulnerable-defi-4.1.0" / "src"
    challenge_path = dvd_base / challenge_name
    
    if not challenge_path.exists():
        logger.error(f"Challenge not found: {challenge_path}")
        return
    
    # Mock the fetch to return local path
    from unittest.mock import MagicMock
    graph.fetcher.fetch_from_git = MagicMock(return_value=str(challenge_path.absolute()))
    
    # Initial state
    state = {
        "target_url": f"local://dvd/{challenge_name}",
        "local_path": str(challenge_path.absolute()),
        "slither_results": [],
        "flattened_code": "",
        "vulnerabilities": ""
    }
    
    try:
        # Run analysis
        result = graph.analyze_node(state)
        
        logger.info(f"\n✅ Analysis Complete for {challenge_name}")
        logger.info(f"   Flattened Code: {len(result.get('flattened_code', ''))} bytes")
        logger.info(f"   Slither Issues: {len(result.get('slither_results', []))}")
        
        # Parse vulnerabilities
        vulns_str = result.get('vulnerabilities', '{}')
        
        # Generate HTML report
        report_path = report_gen.generate_html_report(
            contract_name=challenge_name,
            source_code=result.get('flattened_code', ''),
            findings=vulns_str,
            slither_results=result.get('slither_results', []),
            poc_code=result.get('poc_code', '')
        )
        
        logger.info(f"   📄 Report: {report_path}\n")
        return report_path
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with popular DVD challenges
    challenges = [
        "unstoppable",
        "naive-receiver",
        "truster",
        "side-entrance"
    ]
    
    for challenge in challenges:
        analyze_dvd_contract(challenge)
        print("\n" + "="*80 + "\n")
