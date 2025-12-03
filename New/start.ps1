# Web3 Bounty Hunter - Startup Script
# Auto-start all services with health checks

Write-Host "🚀 Starting Web3 Bounty Hunter..." -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is running
Write-Host "Checking Ollama..." -ForegroundColor Yellow
try {
    $ollamaResponse = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Ollama is not running" -ForegroundColor Red
    Write-Host "   Starting Ollama..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
    
    try {
        $ollamaResponse = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ Ollama started successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to start Ollama. Please start it manually." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker Desktop..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "❌ .env file not found" -ForegroundColor Red
    Write-Host "   Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Please edit .env and add your CLAUDE_API_KEY" -ForegroundColor Yellow
    Write-Host "   Then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Start Docker Compose services
Write-Host "Starting Docker services..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Gray
Write-Host ""

docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ All services started" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    Write-Host "   Check logs with: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Health checks
Write-Host ""
Write-Host "Performing health checks..." -ForegroundColor Yellow
Write-Host ""

$services = @(
    @{Name = "LLM Router"; Url = "http://localhost:8000/health" },
    @{Name = "Orchestrator"; Url = "http://localhost:8001/health" },
    @{Name = "Recon Agent"; Url = "http://localhost:8002/health" },
    @{Name = "Static Agent"; Url = "http://localhost:8003/health" },
    @{Name = "Fuzzing Agent"; Url = "http://localhost:8004/health" },
    @{Name = "Monitoring Agent"; Url = "http://localhost:8005/health" },
    @{Name = "Triage Agent"; Url = "http://localhost:8006/health" },
    @{Name = "Reporting Agent"; Url = "http://localhost:8007/health" },
    @{Name = "Web UI"; Url = "http://localhost:3001" },
    @{Name = "Grafana"; Url = "http://localhost:3000" },
    @{Name = "Qdrant"; Url = "http://localhost:6333/dashboard" }
)

$allHealthy = $true
foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ $($service.Name) - OK" -ForegroundColor Green
    } catch {
        Write-Host "❌ $($service.Name) - NOT RESPONDING" -ForegroundColor Red
        $allHealthy = $false
    }
}

Write-Host ""

if ($allHealthy) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "✅ WEB3 BOUNTY HUNTER IS READY!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🌐 Web UI:         http://localhost:3001" -ForegroundColor Cyan
    Write-Host "📊 Grafana:        http://localhost:3000 (admin/admin)" -ForegroundColor Cyan
    Write-Host "🔍 Prometheus:     http://localhost:9090" -ForegroundColor Cyan
    Write-Host "💾 Qdrant:         http://localhost:6333/dashboard" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📝 To view logs:   docker-compose logs -f" -ForegroundColor Gray
    Write-Host "🛑 To stop:        docker-compose down" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Happy bug hunting! 🔒🎯" -ForegroundColor Magenta
    Write-Host ""
    
    # Open Web UI in browser
    Start-Process "http://localhost:3001"
} else {
    Write-Host "⚠️  Some services are not responding" -ForegroundColor Yellow
    Write-Host "   Check logs with: docker-compose logs -f" -ForegroundColor Gray
    Write-Host "   Services may still be starting up. Wait a minute and check again." -ForegroundColor Gray
}
