# Run Tests in Isolated Docker Environment
# This avoids conflicts with local Python packages (web3.py, eth_typing)

# Build test image
Write-Host "Building test Docker image..." -ForegroundColor Cyan
docker build -t web3-tests:latest -f tests/Dockerfile .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build test image" -ForegroundColor Red
    exit 1
}

# Start test services
Write-Host "Starting test services..." -ForegroundColor Cyan
docker-compose -f tests/docker-compose.test.yml up -d `
    address-scanner `
    guardrail `
    validator-worker `
    mlops-engine `
    signature-generator `
    remediator `
    streaming-indexer

# Wait for services to be healthy
Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Run tests
Write-Host "Running backend tests..." -ForegroundColor Cyan  
docker-compose -f tests/docker-compose.test.yml run --rm backend-tests

$testExitCode = $LASTEXITCODE

# Cleanup
Write-Host "Cleaning up test environment..." -ForegroundColor Yellow
docker-compose -f tests/docker-compose.test.yml down --volumes

if ($testExitCode -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Tests failed with exit code $testExitCode" -ForegroundColor Red
}

exit $testExitCode
