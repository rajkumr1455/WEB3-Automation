"""
Web3 Hunter ML Enhancement - Setup Script
Initializes database, collects training data, and trains initial model
"""
import asyncio
import os
import sys
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def setup_ml_system():
    """Complete setup for ML-enhanced vulnerability detection"""
    
    print("Web3 Hunter ML Enhancement - Setup")
    print("=" * 70)
    print()
    
    # Step 1: Initialize Database
    print("Step 1/4: Database Initialization")
    print("-" * 70)
    try:
        from src.database.models import db
        db.create_tables()
        print("[OK] Database initialized successfully\n")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}\n")
        return False
    
    # Step 2: Collect Training Data
    print("Step 2/4: Training Data Collection")
    print("-" * 70)
    try:
        from src.ml.collector import bootstrap_training_data
        await bootstrap_training_data()
        print("[OK] Training data collected\n")
    except Exception as e:
        print(f"[ERROR] Training data collection failed: {e}\n")
        print("   You can skip this and add data manually later\n")
    
    # Step 3: Test Components
    print("Step 3/4: Component Testing")
    print("-" * 70)
    
    components = [
        ("POC Verifier", "src.poc.verifier", "PoCVerifier"),
        ("Evidence Generator", "src.analysis.evidence", "EvidenceGenerator"),
        ("Impact Calculator", "src.analysis.impact", "ImpactCalculator"),
    ]
    
    for name, module, class_name in components:
        try:
            mod = __import__(module)
            cls = getattr(mod, class_name)
            instance = cls()
            print(f"[OK] {name} - OK")
        except Exception as e:
            print(f"[WARN] {name} - Warning: {e}")
    
    print()
    
    # Step 4: Check Dependencies
    print("Step 4/4: Dependency Check")
    print("-" * 70)
    
    required_packages = [
        "torch",
        "transformers",
        "sklearn",
        "mlflow",
        "matplotlib",
        "sqlalchemy"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[MISSING] {package} - MISSING")
            missing.append(package)
    
    print()
    
    if missing:
        print("[WARN] Missing dependencies detected!")
        print(f"\nInstall with: pip install {' '.join(missing)}")
        print("Or run: pip install -r requirements.txt\n")
    
    # Setup Complete
    print("=" * 70)
    print("[OK] Setup Complete!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("1. Install missing dependencies (if any)")
    print("2. Review training data: python -c 'from database.models import db; s=db.get_session(); print(s.query(s.query_property()).count())'")
    print("3. Train ML model: python ml_trainer.py")
    print("4. Run enhanced scanner: python unified_scanner.py")
    print()
    
    return True


if __name__ == "__main__":
    # Force UTF-8 for Windows console if possible, otherwise just use the safe prints above
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        
    success = asyncio.run(setup_ml_system())
    sys.exit(0 if success else 1)
