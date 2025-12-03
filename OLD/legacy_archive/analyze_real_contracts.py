import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestration.hunter_graph import HunterGraph
from src.reporting.report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def analyze_real_contract(contract_path: str):
    """
    Analyzes a real smart contract and generates a comprehensive report.
    """
    contract_path = Path(contract_path)
    
    if not contract_path.exists():
        logger.error(f"Contract not found: {contract_path}")
        return None
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 Analyzing: {contract_path.name}")
    logger.info(f"{'='*80}\n")
    
    # Initialize components
    graph = HunterGraph()
    report_gen = ReportGenerator()
    
    # Mock the fetch to return contract directory
    from unittest.mock import MagicMock
    contract_dir = contract_path.parent if contract_path.is_file() else contract_path
    graph.fetcher.fetch_from_git = MagicMock(return_value=str(contract_dir.absolute()))
    
    # Initial state
    state = {
        "target_url": f"local://{contract_path.name}",
        "local_path": str(contract_dir.absolute()),
        "slither_results": [],
        "flattened_code": "",
        "vulnerabilities": ""
    }
    
    try:
        # Run analysis
        logger.info("Running analysis workflow...")
        result = graph.analyze_node(state)
        
        # Extract metrics
        flattened_code = result.get('flattened_code', '')
        slither_results = result.get('slither_results', [])
        vulns_str = result.get('vulnerabilities', '{}')
        
        logger.info(f"\n✅ Analysis Complete")
        logger.info(f"   📄 Source Code: {len(flattened_code)} bytes")
        logger.info(f"   🔍 Slither Detections: {len(slither_results)}")
        
        # Generate HTML report
        contract_name = contract_path.stem if contract_path.is_file() else contract_path.name
        report_path = report_gen.generate_html_report(
            contract_name=contract_name,
            source_code=flattened_code,
            findings=vulns_str,
            slither_results=slither_results,
            poc_code=result.get('poc_code', '')
        )
        
        logger.info(f"   📊 Report Generated: {report_path}")
        logger.info(f"\n{'='*80}\n")
        
        return report_path
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_directory(directory_path: str, pattern: str = "*.sol"):
    """
    Analyzes all Solidity contracts in a directory.
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return
    
    # Find all .sol files
    sol_files = list(directory.rglob(pattern))
    
    # Filter out test files and libraries
    main_contracts = [
        f for f in sol_files 
        if not any(x in str(f).lower() for x in ['test', 'mock', 'lib/', '.t.sol'])
    ]
    
    if not main_contracts:
        logger.warning(f"No main contracts found in {directory}")
        return
    
    logger.info(f"\n🎯 Found {len(main_contracts)} contract(s) to analyze:")
    for contract in main_contracts:
        logger.info(f"   - {contract.relative_to(directory)}")
    
    print("\n")
    
    # Analyze each contract
    reports = []
    for contract in main_contracts:
        report = analyze_real_contract(contract)
        if report:
            reports.append(report)
        print()  # Add spacing between analyses
    
    logger.info(f"\n✅ Generated {len(reports)} report(s)")
    return reports

if __name__ == "__main__":
    # Analyze contracts in damn-vulnerable-defi-4.1.0
    target_dir = "damn-vulnerable-defi-4.1.0"
    
    if os.path.exists(target_dir):
        analyze_directory(target_dir)
    else:
        logger.error(f"Target directory not found: {target_dir}")
        logger.info("Please update the target_dir variable to point to your contracts.")
