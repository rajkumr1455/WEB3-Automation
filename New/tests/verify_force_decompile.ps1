# Force Decompile Verification Script
# Test the UI and backend integration for force_de compile functionality

Write-Host "======================================================================"
Write-Host "  Force Decompile Feature - Verification Tests"
Write-Host "======================================================================"
Write-Host ""

# Test 1: API Test WITHOUT force_decompile (should return structured error)
Write-Host "[Test 1] Scanning without force_decompile..."
try {
    $response1 = Invoke-RestMethod -Uri "http://localhost:8001/address-scanner/scan-address" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body '{"address":"0xb3116013c55d49f575ace3cb0d123f3dbf6cac35","chain":"ethereum","force_decompile":false}' `
        -ErrorAction Stop
    
    Write-Host "✅ Response received:"
    $response1 | ConvertTo-Json -Depth 5
    
    if ($response1.status -eq "source_not_found" -or $response1.detail -like "*force_decompile*") {
        Write-Host "✅ Test 1 PASSED: Correct error/suggestion returned" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Test 1: Unexpected response" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ℹ️  Test 1: Got error (expected): $($_.Exception.Message)" -ForegroundColor Cyan
    if ($_.Exception.Message -like "*force_decompile*") {
        Write-Host "✅ Test 1 PASSED: Error contains force_decompile suggestion" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "----------------------------------------------------------------------"
Write-Host ""

# Test 2: API Test WITH force_decompile=true (should decompile and analyze)
Write-Host "[Test 2] Scanning WITH force_decompile=true..."
try {
    $response2 = Invoke-RestMethod -Uri "http://localhost:8001/address-scanner/scan-address" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body '{"address":"0xb3116013c55d49f575ace3cb0d123f3dbf6cac35","chain":"ethereum","force_decompile":true}' `
        -TimeoutSec 180 `
        -ErrorAction Stop
    
    Write-Host "✅ Response received:"
    $response2 | ConvertTo-Json -Depth 5
    
    if ($response2.decompiled -eq $true) {
        Write-Host "✅ Test 2 PASSED: Decompilation successful!" -ForegroundColor Green
        Write-Host "   - Scan ID: $($response2.scan_id)"
        Write-Host "   - Decompiled: $($response2.decompiled)"
        Write-Host "   - Status: $($response2.status)"
    } else {
        Write-Host "⚠️  Test 2: Decompiled flag not set" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Test 2 FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "----------------------------------------------------------------------"
Write-Host ""

# Test 3: Check UI is accessible
Write-Host "[Test 3] Checking UI accessibility..."
try {
    $uiResponse = Invoke-WebRequest -Uri "http://localhost:3001/address-scan" -TimeoutSec 10 -UseBasicParsing
    if ($uiResponse.StatusCode -eq 200) {
        Write-Host "✅ Test 3 PASSED: UI is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Test 3 FAILED: UI not accessible - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================================================"
Write-Host "  Manual UI Test Instructions"
Write-Host "======================================================================"
Write-Host ""
Write-Host "1. Open browser: http://localhost:3001/address-scan"
Write-Host "2. Enter address: 0xb3116013c55d49f575ace3cb0d123f3dbf6cac35"
Write-Host "3. Select chain: ethereum"
Write-Host "4. ✅ CHECK the 'Force Bytecode Decompilation' checkbox"
Write-Host "5. Click 'Scan Contract'"
Write-Host "6. Expected: Scan proceeds without error"
Write-Host ""
Write-Host "Alternative test (error + retry flow):"
Write-Host "1. Enter same address WITHOUT checking the checkbox"
Write-Host "2. Click 'Scan Contract'"
Write-Host "3. Expected: Yellow warning box appears"
Write-Host "4. Click '🔧 Scan with Bytecode Decompilation' button"
Write-Host "5. Expected: Scan proceeds with decompilation"
Write-Host ""
Write-Host "======================================================================" 
