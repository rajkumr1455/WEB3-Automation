#!/usr/bin/env python3
"""
Automatically add CORS middleware to all backend services
"""

import os
import re
from pathlib import Path

CORS_IMPORT = "from fastapi.middleware.cors import CORSMiddleware"

CORS_CONFIG = '''
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''

def add_cors_to_service(service_name):
    """Add CORS middleware to a service's app.py"""
    app_py = Path(f"services/{service_name}/app.py")
    
    if not app_py.exists():
        print(f"[X] {service_name}: app.py not found")
        return False
    
    content = app_py.read_text(encoding='utf-8')
    
    # Check if already has CORS
    if "CORSMiddleware" in content:
        print(f"[SKIP] {service_name}: Already has CORS")
        return False
    
    # Add import if missing
    if CORS_IMPORT not in content:
        # Find first 'from fastapi import' and add after it
        content = re.sub(
            r'(from fastapi import [^\n]+)',
            r'\1\n' + CORS_IMPORT,
            content,
            count=1
        )
    
    # Add middleware after app = FastAPI(...) 
    # Match across multiple lines
    content = re.sub(
        r'(app = FastAPI\([^)]*\))',
        r'\1' + CORS_CONFIG,
        content,
        count=1,
        flags=re.DOTALL
    )
    
    app_py.write_text(content, encoding='utf-8')
    print(f"[OK] {service_name}: CORS added")
    return True

def main():
    print("Applying CORS to all backend services...\n")
    
    services = [
        "fuzzing-agent", "monitoring-agent", "triage-agent", 
        "reporting-agent", "guardrail", "validator-worker",
        "mlops-engine", "signature-generator", "remediator",
        "streaming-indexer"
    ]
    
    fixed_count = 0
    for service in services:
        if add_cors_to_service(service):
            fixed_count += 1
    
    print(f"\n============================================")
    print(f"CORS applied to {fixed_count} services!")
    print(f"============================================")
    
    return fixed_count

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    count = main()
    exit(0 if count > 0 else 1)
