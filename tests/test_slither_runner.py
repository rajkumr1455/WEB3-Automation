import os
import sys
import logging

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analysis.slither_runner import SlitherRunner

logging.basicConfig(level=logging.INFO)

def test_slither_runner():
    runner = SlitherRunner()
    contract_path = os.path.abspath("tests/data/Test.sol")
    output_dir = os.path.abspath("tests/data/graphs")
    
    print(f"Testing SlitherRunner on {contract_path}...")
    
    # Test 1: Run Analysis
    print("\n[Test 1] Running Analysis...")
    results = runner.run(contract_path)
    if results:
        print(f"[OK] Analysis returned {len(results)} findings.")
    else:
        print("[INFO] Analysis returned no findings (expected for clean contract).")
        
    # Test 2: Generate Call Graph
    print("\n[Test 2] Generating Call Graph...")
    dot_file = runner.generate_call_graph(contract_path, output_dir)
    
    if dot_file and os.path.exists(dot_file):
        print(f"[OK] Success! Call graph generated at: {dot_file}")
        with open(dot_file, 'r') as f:
            content = f.read()
            if "digraph" in content:
                print("[OK] Content looks like a valid DOT file.")
            else:
                print("[WARN] Content does not look like a DOT file.")
    else:
        print("[FAIL] Failed to generate call graph.")

if __name__ == "__main__":
    test_slither_runner()
