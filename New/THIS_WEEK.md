# This Week's Action Items - Quick Start Guide

## ✅ Completed
- [x] Security audit (NO MALWARE - all clear!)
- [x] RPC connection pool implementation
- [x] Monitoring agent updated with failover
- [x] `.env.example` updated with RPC configs

## 🎯 This Week (Execute Now)

### 1. Update Your `.env` File (2 minutes)

Add RPC URLs with backup providers:

```bash
# Copy from .env.example and add your API keys
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
ETHEREUM_RPC_URL_BACKUP=https://mainnet.infura.io/v3/YOUR_INFURA_KEY

BSC_RPC_URL=https://bsc-dataseed.binance.org/
BSC_RPC_URL_BACKUP=https://rpc.ankr.com/bsc

POLYGON_RPC_URL=https://polygon-rpc.com/
POLYGON_RPC_URL_BACKUP=https://polygon-mainnet.public.blastapi.io
```

### 2. Install Pre-commit Hooks (1 minute)

```bash
cd "c:\Users\patel\Desktop\web3_hunter\New"

# Install pre-commit
pip install pre-commit

# Install hooks to git
pre-commit install

# Test (optional)
pre-commit run --all-files
```

**What this does**: Blocks commits with secrets, runs security scans locally.

### 3. Activate CI Security Pipeline (2 minutes)

The workflow file is already created at `.github/workflows/security-scan.yml`.

**Option A - Enable via Git**:
```bash
git add .github/workflows/security-scan.yml
git add .pre-commit-config.yaml
git commit -m "feat: Add CI security pipeline with Bandit, Semgrep, Pip-Audit"
git push origin main
```

**Option B - Test First**:
```bash
# Create feature branch
git checkout -b security-pipeline-test

git add .github/workflows/security-scan.yml .pre-commit-config.yaml
git commit -m "test: CI security pipeline"
git push origin security-pipeline-test

# Open PR on GitHub - CI will run automatically
# Review results, then merge to main
```

**Verify**: Check GitHub Actions tab - you should see "Security Scan" workflow running.

### 4. Test RPC Pool Integration (5 minutes)

```bash
# Restart monitoring agent with new config
docker-compose restart monitoring-agent

# Check RPC pool status
curl http://localhost:8005/rpc-status

# Expected output:
# {
#   "ethereum": {
#     "healthy": 2,
#     "total_providers": 2,
#     ...
#   }
# }

# Test health endpoint
curl http://localhost:8005/health
```

## 📋 Quick Verification Checklist

- [ ] `.env` has RPC_URL and RPC_URL_BACKUP for each chain
- [ ] `pre-commit install` completed successfully
- [ ] Git commit triggers pre-commit hooks (test with dummy commit)
- [ ] GitHub Actions security scan visible in Actions tab
- [ ] `docker-compose logs monitoring-agent` shows "RPC pool initialized"
- [ ] `/rpc-status` endpoint returns healthy providers

## 🐛 Troubleshooting

### Pre-commit hooks not running?
```bash
# Reinstall
pre-commit uninstall
pre-commit install
pre-commit run --all-files
```

### CI workflow not appearing?
- Ensure pushed to `main` or opened PR
- Check `.github/workflows/` directory exists
- Verify YAML syntax: `cat .github/workflows/security-scan.yml`

### RPC pool errors?
```bash
# Check logs
docker-compose logs -f monitoring-agent | grep "RPC"

# Verify .env loaded
docker-compose exec monitoring-agent env | grep RPC
```

## 📚 Next Steps (After This Week)

1. **Integrate RPC pool into orchestrator** (see [docs/RPC_POOL_INTEGRATION.md](file:///c:/Users/patel/Desktop/web3_hunter/New/docs/RPC_POOL_INTEGRATION.md))
2. **Apply subprocess sanitization patch** (H2 fix)
3. **Implement transaction simulation service** (H1 fix)

---

**Estimated Time**: 10-15 minutes total  
**Questions?** See [final_report.md](file:///C:/Users/patel/.gemini/antigravity/brain/f85791a0-6b15-4085-819c-cc1cdf3f650b/audit/final_report.md) for full context.
