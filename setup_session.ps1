# Quick Configuration Script
# Run this after installation to add tools to current session PATH

# Add Ollama to PATH for current session
$env:Path += ";C:\Users\patel\AppData\Local\Programs\Ollama"
# Add local Foundry to PATH
$env:Path += ";C:\Users\patel\Desktop\web3_hunter\foundry"
# Add Python Scripts to PATH (for solc-select, slither)
$env:Path += ";C:\Users\patel\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts"
# Add solc to PATH
$env:Path += ";C:\Users\patel\.solc-select\artifacts\solc-0.8.20"

# Verify Ollama
Write-Host "[+] Checking Ollama..." -ForegroundColor Green
ollama --version

# List available models
Write-Host "`n[+] Available models:" -ForegroundColor Green
ollama list

# Check if codellama is available
$models = ollama list
if ($models -match "codellama") {
    Write-Host "[+] CodeLlama model ready!" -ForegroundColor Green
} else {
    Write-Host "[!] CodeLlama not found. Run: ollama pull codellama:13b" -ForegroundColor Yellow
}

# Check for Forge (Foundry)
Write-Host "`n[+] Checking Foundry..." -ForegroundColor Green
$forgeExists = Get-Command forge -ErrorAction SilentlyContinue
if ($forgeExists) {
    forge --version
    Write-Host "[+] Foundry is installed!" -ForegroundColor Green
} else {
    Write-Host "[-] Foundry not found" -ForegroundColor Red
    Write-Host "    Option 1: Download pre-built binaries from:" -ForegroundColor Yellow
    Write-Host "    https://github.com/foundry-rs/foundry/releases" -ForegroundColor Cyan
    Write-Host "    Option 2: Install Rust and build from source:" -ForegroundColor Yellow
    Write-Host "    https://rustup.rs" -ForegroundColor Cyan
}

Write-Host "`n[+] Running environment validation..." -ForegroundColor Green
python validate_env.py

Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "Configuration loaded for current session" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host "`nTo make permanent, add to System PATH:" -ForegroundColor Yellow
Write-Host "  C:\Users\patel\AppData\Local\Programs\Ollama" -ForegroundColor Cyan
