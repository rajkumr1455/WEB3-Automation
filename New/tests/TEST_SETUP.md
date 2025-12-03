# Test Environment Setup Guide

## Quick Start (Isolated Environment)

### Option 1: Using Virtual Environment (Recommended)

```powershell
# Create isolated test environment
python -m venv test-venv

# Activate
.\test-venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r tests/backend/requirements.txt

# Run tests
python -m pytest tests/backend -v

# Deactivate when done
deactivate
```

### Option 2: Using Current Environment

```powershell
# Upgrade conflicting packages
pip install --upgrade pydantic>=2.7.4 httpx>=0.27.0

# Run tests
python -m pytest tests/backend -v
```

## Troubleshooting

### Issue: eth_typing ImportError
**Solution:** The web3.py pytest plugin conflicts with test dependencies.
```powershell
# Uninstall web3 pytest plugin if not needed
pip uninstall web3[tester]

# Or use isolated venv (recommended)
```

### Issue: Services showing unhealthy
**Solution:** Check individual service logs
```powershell
docker logs mlops-engine
docker logs validator-worker
docker logs remediator
```

Common causes:
- Missing Python package in Docker image
- Health check endpoint not responding
- Startup time exceeds health check grace period

**Fix:** Rebuild affected services
```powershell
docker-compose build mlops-engine
docker-compose up -d mlops-engine
```

## Running Specific Tests

```powershell
# Single test file
python -m pytest tests/backend/test_address_scan_flow.py -v

# Single test function
python -m pytest tests/backend/test_address_scan_flow.py::test_health_endpoint -v

# All tests
python -m pytest tests/backend -v

# With coverage
python -m pytest tests/backend --cov=. --cov-report=html
```

## CI/CD Setup

Tests are configured to run automatically in GitHub Actions.
See `.github/workflows/e2e.yml` for configuration.

**Local CI simulation:**
```powershell
# Start all services
docker-compose up -d

# Wait for health
.\tests\e2e\bootstrap.ps1

# Run tests
python -m pytest tests/backend -v
npx playwright test

# Teardown
docker-compose down --volumes
```
