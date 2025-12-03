# Quick Fix Script for All Unhealthy Services
# Rebuilds all services with working healthchecks

Write-Host "Fixing Unhealthy Services..." -ForegroundColor Cyan

# Services that need healthcheck fixes
$services = @(
    "llm-router",
    "validator-worker", 
    "mlops-engine",
    "signature-generator",
    "remediator",
    "streaming-indexer",
    "guardrail",
    "address-scanner"
)

Write-Host "`nStep 1: Rebuilding services with fixed healthchecks..."
docker-compose up -d --build @services

Write-Host "`nStep 2: Waiting for services to stabilize (30 seconds)..."
Start-Sleep -Seconds 30

Write-Host "`nStep 3: Checking service health..."
docker-compose ps | Select-String -Pattern "unhealthy"

$unhealthy = docker-compose ps | Select-String -Pattern "unhealthy"
if ($unhealthy.Count -eq 0) {
    Write-Host "`n✅ All services healthy!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Still unhealthy: $($unhealthy.Count) services" -ForegroundColor Yellow
    docker-compose ps
}

Write-Host "`n✅ Fix script complete!" -ForegroundColor Green
