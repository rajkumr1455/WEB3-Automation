#!/usr/bin/env pwsh
# Automated CORS fix for all backend services

Write-Host "🔧 Applying CORS fixes to all backend services..." -ForegroundColor Cyan
Write-Host ""

$services = @(
    "llm-router", "orchestrator", "recon-agent", "static-agent",
    "fuzzing-agent", "monitoring-agent", "triage-agent", "reporting-agent",
    "address-scanner", "guardrail", "validator-worker", "mlops-engine",
    "signature-generator", "remediator", "streaming-indexer"
)

$fixedCount = 0

foreach ($service in $services) {
    $appFile = "services\$service\app.py"
    
    if (Test-Path $appFile) {
        Write-Host "📝 Fixing $service..." -ForegroundColor Yellow
        
        # Read file content
        $content = Get-Content $appFile -Raw
        
        # Check if already has CORS
        if ($content -match "CORSMiddleware") {
            Write-Host "   ⏭️  Already has CORS, skipping" -ForegroundColor Gray
            continue
        }
        
        # Add import after fastapi imports
        if ($content -notmatch "from fastapi.middleware.cors import CORSMiddleware") {
            $content = $content -replace "(from fastapi import [^\r\n]+)", "`$1`r`nfrom fastapi.middleware.cors import CORSMiddleware"
        }
        
        # Find where app = FastAPI is defined and add CORS middleware after it
        if ($content -match "app = FastAPI\([^)]*\)") {
            $corsConfig = @"


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # Next.js UI
        "http://localhost:3000",  # Grafana
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"@
            $content = $content -replace "(app = FastAPI\([^)]*\))", "`$1$corsConfig"
        }
        
        # Write back
        Set-Content $appFile -Value $content -NoNewline
        Write-Host "   ✅ Fixed" -ForegroundColor Green
        $fixedCount++
    } else {
        Write-Host "   ⚠️  File not found: $appFile" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ CORS fixes applied to $fixedCount services!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Rebuild services: docker-compose build" -ForegroundColor White
Write-Host "2. Restart services: docker-compose up -d" -ForegroundColor White
Write-Host "3. Test UI: http://localhost:3001" -ForegroundColor White
Write-Host ""
