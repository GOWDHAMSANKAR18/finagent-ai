# PowerShell Startup Script for FinAgent AI Platform
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "       FINAGENT AI | MULTI-AGENT FINANCIAL INTELLIGENCE PLATFORM" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan

# Set location to script directory (project root)
Set-Location -Path $PSScriptRoot

$pythonExe = "python"
if (Test-Path "$PSScriptRoot\.venv\Scripts\python.exe") {
    $pythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
}

Write-Host "[INFO] Launching FastAPI App via $pythonExe run.py..." -ForegroundColor Green
& $pythonExe run.py
