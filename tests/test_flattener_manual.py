import os
import sys
import logging

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion.flattener import SolidityFlattener

logging.basicConfig(level=logging.INFO)

def test_flattener():
    flattener = SolidityFlattener()
    contract_path = os.path.abspath("tests/data/Test.sol")
    output_dir = os.path.abspath("tests/data/flattened")
    
    print(f"Testing flattener on {contract_path}...")
    
    flattened_path = flattener.flatten(contract_path, output_dir)
    
    if flattened_path and os.path.exists(flattened_path):
        print(f"[OK] Success! Flattened file at: {flattened_path}")
        with open(flattened_path, 'r') as f:
            print("--- Content ---")
            print(f.read()[:200]) # Print first 200 chars
            print("--- End Content ---")
    else:
        print("[FAIL] Failed to flatten.")

if __name__ == "__main__":
    test_flattener()
