import sys
from tasks import scan_contract
import time

def trigger(file_path):
    print(f"Reading {file_path}...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print("Triggering Celery task...")
    task = scan_contract.delay(code)
    print(f"Task ID: {task.id}")
    print("Waiting for result (this might take a while if worker is busy)...")
    
    # Simple polling for result (optional, usually we just fire and forget or use a callback)
    # But for a CLI tool, it's nice to see the result.
    try:
        result = task.get(timeout=300) # Wait up to 5 mins
        print("\n--- Scan Result ---")
        print(result)
    except Exception as e:
        print(f"Error getting result: {e}")
        print("Check Celery worker logs for details.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python trigger_scan.py <path_to_solidity_file>")
    else:
        trigger(sys.argv[1])
