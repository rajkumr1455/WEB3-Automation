# Web3 Hunter ML Enhancement - Quick Start Guide

## 🚀 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: For GPU support, install PyTorch with CUDA:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. Run Setup

```bash
python setup_ml.py
```

This will:
- ✅ Initialize SQLite database
- ✅ Collect training data from SmartBugs
- ✅ Test all components
- ✅ Check dependencies

---

## 📊 Training the ML Model

### Collect More Training Data

```bash
python training_data_collector.py
```

This collects vulnerability examples from:
- SmartBugs curated dataset
- GitHub security advisories  
- Public CVE databases

### Train the Model

```bash
python ml_trainer.py
```

Training options:
- **GPU**: Automatically uses RTX 4060 if available
- **CPU Fallback**: Switches to CPU if no GPU
- **MLflow Tracking**: View experiments at `http://localhost:5000`

Expected output:
```
🔧 Initializing ML Trainer on device: CUDA
   GPU: NVIDIA GeForce RTX 4060
   VRAM: 8.0 GB

📊 Loading training data from database...
✓ Loaded 234 verified training samples

🏋️  Training started...
✓ Training completed in 145.3s

🎉 Training Complete!
Accuracy:  0.8734
Precision: 0.8521
Recall:    0.8912
F1 Score:  0.8712
```

---

## 🔍 Running Enhanced Scans

### Basic Scan

```python
from unified_scanner import UnifiedScanner

scanner = UnifiedScanner(chain="eth")

contract_code = """
pragma solidity ^0.8.0;
contract Vault {
    mapping(address => uint) balances;
    function withdraw() public {
        uint amt = balances[msg.sender];
        (bool s,) = msg.sender.call{value: amt}("");
        balances[msg.sender] = 0;
    }
}
"""

result = await scanner.scan_contract(contract_code, "MyVault")
```

### What You Get

1. **Vulnerabilities Detected** with ML confidence scores
2. **Verified POCs** that compile and run
3. **Visual Evidence**:
   - State transition diagrams
   - Transaction flow charts
   - Impact analysis graphs
4. **Impact Metrics**:
   - CVSS score
   - Financial impact (USD/ETH)
   - Attack cost
   - ROI calculation
5. **Bug Bounty Report** ready to submit

---

## 📸 Evidence Generation

The system automatically generates visual proofs:

### State Transition Diagram
Shows before/after contract states with balance changes.

### Transaction Flow
Step-by-step visualization of the exploit sequence.

### Impact Chart
Financial impact, severity, affected users.

All evidence is saved to `reports/evidence/` and linked in the database.

---

## 🎯 POC Verification

Every generated POC is automatically tested:

```bash
# Manual verification
python poc_verifier.py
```

Verification includes:
- ✅ Foundry compilation check
- ✅ Test execution
- ✅ Gas usage tracking
- ✅ Success/failure logging
- ✅ Console output capture

Results stored in database with `poc_verified = true/false`.

---

## 💰 Impact Calculation

Automatic CVSS scoring and financial impact:

```python
from impact_calculator import ImpactCalculator

calc = ImpactCalculator()

report = calc.generate_full_impact_report(
    vulnerability_type="Reentrancy",
    funds_at_risk_eth=25.0,
    num_transactions=3,
    exploitability='high'
)

print(report['cvss_score'])      # 9.1
print(report['estimated_bounty']) # $125,000
```

---

## 🔄 Continuous Learning

### Provide Feedback

After scanning, rate the vulnerability detection:

```python
from database.models import db, Vulnerability

session = db.get_session()
vuln = session.query(Vulnerability).filter_by(id=123).first()

# Mark as false positive
vuln.is_false_positive = True
vuln.user_rating = 1  # 1-5 stars

# Or track bounty result
vuln.bounty_submitted = True
vuln.bounty_accepted = True
vuln.bounty_reward = 5000.00

session.commit()
```

### Retrain Model

The system learns from feedback:

```bash
# Retrain with new data
python ml_trainer.py --incremental
```

This creates a better model based on:
- ✅ False positive corrections
- ✅ Bounty acceptance/rejection
- ✅ User ratings
- ✅ POC verification results

---

## 📁 Project Structure

```
web3_hunter/
├── database/
│   ├── models.py          # SQLAlchemy models
│   └── __init__.py        # Database initialization
├── models/
│   └── vulnerability_classifier/  # Trained ML model
├── reports/
│   ├── pocs/             # Generated POCs
│   └── evidence/         # Visual evidence (PNG, diagrams)
├── training_data/         # (Created automatically)
│   ├── vulnerabilities.jsonl
│   └── feedback.jsonl
├── ml_trainer.py          # ML training pipeline
├── training_data_collector.py  # Data collection
├── poc_generator.py       # Enhanced POC generator
├── poc_verifier.py        # Foundry verification
├── evidence_generator.py  # Visual evidence
├── impact_calculator.py   # CVSS & financial impact
├── unified_scanner.py     # Main scanner (uses ML)
└── setup_ml.py           # One-command setup
```

---

## 🐛 Troubleshooting

### "CUDA out of memory"
Reduce batch size in `ml_trainer.py`:
```python
classifier.train(batch_size=4)  # Default is 8
```

### "No training data found"
Run data collector:
```bash
python training_data_collector.py
```

### "Foundry not found"
Install Foundry:
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### "Missing matplotlib/seaborn"
Install visualization libraries:
```bash
pip install matplotlib seaborn pillow
```

---

## 📈 Success Metrics

Track your system's improvement:

```sql
-- View detection accuracy over time
SELECT 
    DATE(detected_at) as date,
    COUNT(*) as total,
    SUM(CASE WHEN is_false_positive = 0 THEN 1 ELSE 0 END) as accurate
FROM vulnerabilities
GROUP BY DATE(detected_at);

-- POC success rate
SELECT 
    COUNT(*) as total_pocs,
    SUM(CASE WHEN poc_verified = 1 THEN 1 ELSE 0 END) as verified
FROM vulnerabilities
WHERE poc_generated = 1;

-- Bounty performance
SELECT 
    vulnerability_type,
    COUNT(*) as submitted,
    SUM(CASE WHEN bounty_accepted = 1 THEN 1 ELSE 0 END) as accepted,
    AVG(bounty_reward) as avg_reward
FROM vulnerabilities
WHERE bounty_submitted = 1
GROUP BY vulnerability_type;
```

---

## 🎓 Next Steps

1. **Collect Real Data**: Scan actual contracts and save results
2. **Train Custom Model**: Use your data for better accuracy
3. **Submit to Bounties**: Test with real bug bounty platforms
4. **Tune Parameters**: Adjust severity thresholds, gas estimates
5. **Add New Patterns**: Expand vulnerability types detected

---

## 📞 Support

Need help? Check:
- Implementation plan: `implementation_plan.md`
- System overview: `enhancements_overview.md`
- Database schema: `database/models.py`
