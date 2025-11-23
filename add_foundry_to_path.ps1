# Add Foundry to Windows PATH permanently
# Run this script as Administrator

Write-Host "Adding Foundry to System PATH..." -ForegroundColor Cyan

# Get the absolute path to the foundry directory
$foundryPath = Join-Path $PSScriptRoot "foundry"

if (-not (Test-Path $foundryPath)) {
    Write-Host "ERROR: Foundry directory not found at: $foundryPath" -ForegroundColor Red
    exit 1
}

# Get current PATH from User environment
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Check if foundry is already in PATH
if ($currentPath -like "*$foundryPath*") {
    Write-Host "Foundry is already in PATH." -ForegroundColor Green
    exit 0
}

# Add foundry to PATH
$newPath = "$currentPath;$foundryPath"
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

Write-Host "✓ Successfully added Foundry to User PATH" -ForegroundColor Green
Write-Host "Path added: $foundryPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANT: Restart your terminal/IDE for the changes to take effect." -ForegroundColor Magenta
Write-Host ""

# Verify
Write-Host "Verifying installation..." -ForegroundColor Cyan
$env:Path = [Environment]::GetEnvironmentVariable("Path", "User")
$forgeCmd = Get-Command forge -ErrorAction SilentlyContinue

if ($forgeCmd) {
    Write-Host "✓ forge.exe is now accessible" -ForegroundColor Green
    & forge --version
} else {
    Write-Host "⚠ forge.exe not found. Please restart your terminal." -ForegroundColor Yellow
}
