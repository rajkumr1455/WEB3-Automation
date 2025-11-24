# Foundry Installation Script
# Run this script to complete Foundry installation

Write-Host "[*] Installing Foundry..." -ForegroundColor Cyan

# Wait for file to be unlocked
Start-Sleep -Seconds 3

# Create destination directory
$foundryDir = "$env:USERPROFILE\.foundry\bin"
New-Item -ItemType Directory -Force -Path $foundryDir | Out-Null

# Extract the zip file
try {
    Expand-Archive -Path "foundry.zip" -DestinationPath $foundryDir -Force
    Write-Host "[+] Foundry extracted successfully!" -ForegroundColor Green
} catch {
    Write-Host "[!] Error extracting. Please manually extract foundry.zip to $foundryDir" -ForegroundColor Yellow
    Write-Host "    Right-click foundry.zip -> Extract All -> Browse to: $foundryDir" -ForegroundColor Yellow
    exit 1
}

# Add to PATH for current session
$env:Path += ";$foundryDir"

# Test installation
Write-Host "`n[*] Testing Foundry installation..." -ForegroundColor Cyan
& "$foundryDir\forge.exe" --version
& "$foundryDir\cast.exe" --version  
& "$foundryDir\anvil.exe" --version

Write-Host "`n[+] Foundry installed successfully!" -ForegroundColor Green
Write-Host "`n[!] To use Foundry in future sessions, add to your PATH:" -ForegroundColor Yellow
Write-Host "    $foundryDir" -ForegroundColor Cyan

# Clean up
Remove-Item "foundry.zip" -ErrorAction SilentlyContinue

Write-Host "`nDone! You can now use: forge, cast, anvil, chisel" -ForegroundColor Green
