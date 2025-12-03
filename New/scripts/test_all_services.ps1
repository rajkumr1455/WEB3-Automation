# Automated Service Health Check Script
# Tests all services systematically

$services = @(
    @{Name="Orchestrator"; Port=8001; Endpoint="/health"},
    @{Name="LLM Router"; Port=8000; Endpoint="/health"},
    @{Name="Recon Agent"; Port=8002; Endpoint="/health"},
    @{Name="Static Agent"; Port=8003; Endpoint="/health"},
    @{Name="Fuzzing Agent"; Port=8004; Endpoint="/health"},
    @{Name="Monitoring Agent"; Port=8005; Endpoint="/health"},
    @{Name="Triage Agent"; Port=8006; Endpoint="/health"},
    @{Name="Reporting Agent"; Port=8007; Endpoint="/health"},
    @{Name="Address Scanner"; Port=8008; Endpoint="/health"},
    @{Name="Guardrail"; Port=8009; Endpoint="/health"},
    @{Name="Validator Worker"; Port=8010; Endpoint="/health"},
    @{Name="MLOps Engine"; Port=8011; Endpoint="/health"},
    @{Name="Signature Generator"; Port=8012; Endpoint="/health"},
    @{Name="Remediator"; Port=8013; Endpoint="/health"},
    @{Name="Streaming Indexer"; Port=8014; Endpoint="/health"}
)

Write-Host "`n=== Service Health Check Results ===`n" -ForegroundColor Cyan

$results = @()

foreach ($service in $services) {
    $url = "http://localhost:$($service.Port)$($service.Endpoint)"
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing
        $status = if ($response.StatusCode -eq 200) { "✅ HEALTHY" } else { "⚠️  DEGRADED ($($response.StatusCode))" }
        $color = if ($response.StatusCode -eq 200) { "Green" } else { "Yellow" }
        
        Write-Host "$($service.Name) (Port $($service.Port)): $status" -ForegroundColor $color
        
        $results += [PSCustomObject]@{
            Service = $service.Name
            Port = $service.Port
            Status = $status
            Response = $response.Content.Substring(0, [Math]::Min(100, $response.Content.Length))
        }
    }
    catch {
        Write-Host "$($service.Name) (Port $($service.Port)): ❌ FAILED - $($_.Exception.Message)" -ForegroundColor Red
        
        $results += [PSCustomObject]@{
            Service = $service.Name
            Port = $service.Port
            Status = "❌ FAILED"
            Response = $_.Exception.Message
        }
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
$healthy = ($results | Where-Object { $_.Status -like "*HEALTHY*" }).Count
$failed = ($results | Where-Object { $_.Status -like "*FAILED*" }).Count
Write-Host "Healthy: $healthy | Failed: $failed | Total: $($results.Count)" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Yellow" })

$results | Export-Csv -Path "service_health_results.csv" -NoTypeInformation
Write-Host "`nResults saved to: service_health_results.csv" -ForegroundColor Gray
