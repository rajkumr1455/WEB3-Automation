# 🔍 Web3 Hunter - Quick Start Guide

## Automated Vulnerability Detection

Your automation is ready! Give it a contract and it will automatically find all vulnerabilities.

---

## 🚀 Usage

### 1. Analyze GitHub Repository
```powershell
python hunt.py --github https://github.com/user/vulnerable-contract
```

### 2. Analyze Deployed Contract (Etherscan)
```powershell
python hunt.py --etherscan 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984
```

### 3. Analyze Local File
```powershell
python hunt.py --local contracts/MyToken.sol
```

### 4. Analyze Local Directory
```powershell
python hunt.py --local contracts/
```

### 5. With Etherscan API Key
```powershell
python hunt.py --etherscan 0x... --etherscan-key YOUR_API_KEY
```

---

## 🎯 What It Does Automatically

```
┌─────────────────────────────────────────────────┐
│ INPUT: Contract (GitHub/Etherscan/Local)       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ STEP 1: Fetch & Extract Source Code            │
│ - Clone GitHub repo                             │
│ - Download from Etherscan                       │
│ - Read local files                              │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ STEP 2: Static Analysis (Slither)              │
│ - Detect common vulnerabilities                 │
│ - Check coding best practices                   │
│ - Find potential exploits                       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ STEP 3: AI Analysis (LLM Auditor)              │
│ - Deep code understanding                       │
│ - Classify by severity (Red/Yellow/Blue)        │
│ - Context from 55-entry knowledge base          │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ STEP 4: PoC Generation (Optional)              │
│ - Generate exploit code                         │
│ - Create Foundry tests                          │
│ - Verify exploitability                         │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ OUTPUT: Beautiful HTML Report                   │
│ - All vulnerabilities listed                    │
│ - Categorized by severity                       │
│ - Includes fix recommendations                  │
│ - PoC code included                             │
└─────────────────────────────────────────────────┘
```

---

## 📊 Example Output

```
================================================================================
🎯 TARGET: GitHub Repository
📍 URL: https://github.com/user/vulnerable-defi
================================================================================

📥 Fetching repository...
✓ Cloned to: data/repos/vulnerable-defi

🔍 Found 5 contract(s) to analyze

────────────────────────────────────────────────────────────────────────────────
📝 [1/5] Analyzing: VulnerableVault.sol
────────────────────────────────────────────────────────────────────────────────

   ✓ Source: 2,345 bytes
   ✓ Slither: 12 issues
   📊 Report: VulnerableVault_20251123_212500.html

────────────────────────────────────────────────────────────────────────────────
📝 [2/5] Analyzing: Token.sol
────────────────────────────────────────────────────────────────────────────────

   ✓ Source: 1,890 bytes
   ✓ Slither: 3 issues
   📊 Report: Token_20251123_212505.html

... (3 more contracts)

================================================================================
✅ SCAN COMPLETE
   Contracts Analyzed: 5
   Reports Generated: 5
   Reports Location: data/reports/
================================================================================
```

---

## 🎨 Report Features

Each HTML report includes:

- **🔴 RED Vulnerabilities** (High Severity)
  - Reentrancy attacks
  - Access control issues
  - Integer overflow/underflow
  - Weak randomness
  
- **🟡 YELLOW Issues** (Config & Coding)
  - Floating pragma
  - Visibility issues
  - Deprecated functions
  
- **🔵 BLUE Risks** (Logical)
  - Gas griefing
  - Oracle manipulation
  - DoS patterns

- **📊 Slither Static Analysis**
- **💣 Proof of Concept Code** (when applicable)

---

## 🔧 Advanced Options

### Custom Etherscan API Key
Get faster rate limits:
```powershell
python hunt.py --etherscan 0x... --etherscan-key YOUR_KEY
```

### Different Chains
```powershell
# Polygon
python hunt.py --etherscan 0x... --chain polygon

# BSC (Future)
python hunt.py --etherscan 0x... --chain bsc
```

---

## 📁 Output Structure

```
web3_hunter/
├── data/
│   ├── reports/              # 📊 HTML Reports (main output)
│   │   ├── Contract1_timestamp.html
│   │   ├── Contract2_timestamp.html
│   │   └── ...
│   ├── repos/                # Cloned GitHub repos
│   ├── flattened/            # Flattened contracts
│   └── temp_etherscan/       # Downloaded Etherscan contracts
```

---

## 🎯 Real-World Examples

### Example 1: Analyze Uniswap V2
```powershell
python hunt.py --github https://github.com/Uniswap/v2-core
```

### Example 2: Analyze USDT Contract
```powershell
python hunt.py --etherscan 0xdac17f958d2ee523a2206206994597c13d831ec7
```

### Example 3: Analyze Your Local Project
```powershell
python hunt.py --local C:\MyProjects\DeFiToken\contracts
```

---

## ⚙️ Configuration

Edit `config/settings.yaml` to customize:
```yaml
llm:
  model: codellama:13b      # Change AI model
  temperature: 0.1          # Adjust creativity (0.0-1.0)

slither:
  exclude_low: true         # Hide low-severity issues
```

---

## 🚨 Troubleshooting

### Issue: "Slither failed"
**Solution**: Ensure contract has `foundry.toml` or is standalone Solidity file

### Issue: "Contract not verified"
**Solution**: Only works with verified contracts on Etherscan

### Issue: "No vulnerabilities found"
**Solution**: Good news! But review report for suggestions

---

## 🎓 Knowledge Base

The AI draws from:
- **20 SWC Registry patterns** (common vulnerabilities)
- **35 Security workflow items** (best practices)
- **Past exploit patterns** (real-world attacks)

---

## 🔄 Workflow Integration

### Run on Git Commit (Manual)
```powershell
# Add to .git/hooks/pre-push
python hunt.py --local .
```

### Daily Scans
```powershell
# Windows Task Scheduler
python hunt.py --local C:\contracts --schedule daily
```

---

**Your automation is production-ready!** 🚀

Just run `python hunt.py --help` for quick reference.
