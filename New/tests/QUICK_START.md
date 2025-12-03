# Quick Test Commands

## Problem: PowerShell Execution Policy
If you see: `cannot be loaded because running scripts is disabled`

## Solutions:

### Option 1: Bypass Execution Policy (Recommended)
```powershell
powershell -ExecutionPolicy Bypass -File .\tests\run-tests.ps1
```

### Option 2: Run Docker Commands Directly
```powershell
# Build test image
docker build -t web3-tests:latest -f tests\Dockerfile .

# Start test services
docker-compose -f tests\docker-compose.test.yml up -d

# Wait for services
Start-Sleep -Seconds 15

# Run tests
docker-compose -f tests\docker-compose.test.yml run --rm backend-tests

# Cleanup
docker-compose -f tests\docker-compose.test.yml down --volumes
```

### Option 3: Change Execution Policy (Requires Admin)
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run normally
.\tests\run-tests.ps1
```

## Quick Test (Single Service)
```powershell
# Test just the address scanner
docker run --rm --network host web3-tests:latest python -m pytest tests/backend/test_address_scan_flow.py::test_health_endpoint -v
```
