# E-commerce Assistant Agent Template - Setup Script (Windows)
# Usage: .\setup.ps1
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  E-commerce Assistant Agent - Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check Python version
$pythonCmd = $null
foreach ($cmd in @("python", "python3")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "(\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                $pythonCmd = $cmd
                break
            }
        }
    } catch { }
}

if (-not $pythonCmd) {
    Write-Host "Error: Python 3.10+ is required but not found." -ForegroundColor Red
    Write-Host "Install from: https://www.python.org/downloads/"
    exit 1
}

Write-Host "[1/4] Python found: $(& $pythonCmd --version)" -ForegroundColor Green

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "[2/4] Creating virtual environment..." -ForegroundColor Yellow
    & $pythonCmd -m venv .venv
} else {
    Write-Host "[2/4] Virtual environment already exists" -ForegroundColor Green
}

# Activate and install
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
& pip install -e ".[dev]" --quiet

# Configure environment
if (-not (Test-Path ".env")) {
    Write-Host "[4/4] Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "  Warning: Edit .env and add your API key:" -ForegroundColor Yellow
    Write-Host "     OPENAI_API_KEY=sk-your-key-here"
} else {
    Write-Host "[4/4] .env already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Activate:  .\.venv\Scripts\Activate.ps1"
Write-Host "  Run:       python -m ecommerce_assistant"
Write-Host "  Test:      pytest -v"
Write-Host ""
