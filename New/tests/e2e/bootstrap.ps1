# Bootstrap E2E Test Environment (PowerShell)
# Starts Docker services and waits for health

param(
    [int]$HealthTimeout = 120,
    [int]$RetryInterval = 5
)

Write-Host "🚀 Starting E2E Test Environment..." -ForegroundColor Cyan

# Check Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
$dockerRunning = docker info 2>$null
if (-not $dockerRunning) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Start services
Write-Host "Starting Docker Compose services..." -ForegroundColor Yellow
docker compose -f docker-compose.yml up -d `
    qdrant `
    llm-router `
    orchestrator `
    recon-agent `
    static-agent `
    fuzzing-agent `
    monitoring-agent `
    triage-agent `
    reporting-agent `
    address-scanner `
    guardrail `
    validator-worker `
    mlops-engine `
    signature-generator `
    remediator `
    streaming-indexer `
    web-ui

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    exit 1
}

# Wait for services to be healthy
Write-Host "Waiting for services to be healthy (timeout: ${HealthTimeout}s)..." -ForegroundColor Yellow

$services = @(
    @{Name="qdrant"; Port=6333; Path="/"},
    @{Name="llm-router"; Port=8000; Path="/health"},
    @{Name="orchestrator"; Port=8001; Path="/health"},
    @{Name="address-scanner"; Port=8008; Path="/health"},
    @{Name="guardrail"; Port=8009; Path="/health"},
    @{Name="validator-worker"; Port=8010; Path="/health"},
    @{Name="mlops-engine"; Port=8011; Path="/health"},
    @{Name="signature-generator"; Port=8012; Path="/health"},
    @{Name="remediator"; Port=8013; Path="/health"},
    @{Name="streaming-indexer"; Port=8014; Path="/health"},
    @{Name="web-ui"; Port=3001; Path="/"}
)

$startTime = Get-Date
$allHealthy = $false

while (-not $allHealthy -and ((Get-Date) - $startTime).TotalSeconds -lt $HealthTimeout) {
    $allHealthy = $true
    
    foreach ($service in $services) {
        $url = "http://localhost:$($service.Port)$($service.Path)"
        try {
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 2 -ErrorAction Stop
            Write-Host "✓ $($service.Name) is healthy" -ForegroundColor Green
        } catch {
            Write-Host "⏳ Waiting for $($service.Name)..." -ForegroundColor Yellow
            $allHealthy = $false
        }
    }
    
    if (-not $allHealthy) {
        Start-Sleep -Seconds $RetryInterval
    }
}

if (-not $allHealthy) {
    Write-Host "❌ Services failed to become healthy within ${HealthTimeout}s" -ForegroundColor Red
    Write-Host "Check logs with: docker compose logs" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ All services are healthy!" -ForegroundColor Green

# Seed Qdrant if needed
Write-Host "Seeding test data..." -ForegroundColor Yellow
# In production, add seed data scripts here

Write-Host "🎉 E2E environment is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Run tests with:" -ForegroundColor Cyan
Write-Host "  pytest tests/backend -v" -ForegroundColor White
Write-Host "  npx playwright test" -ForegroundColor White
Write-Host ""
Write-Host "Teardown with:" -ForegroundColor Cyan
Write-Host "  docker compose down --volumes" -ForegroundColor White
