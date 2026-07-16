# Fixed Docker Start Script - Handles BuildKit issues
# Usage: .\scripts\docker-start-fixed.ps1

$ErrorActionPreference = "Continue"

Write-Host "=== Docker Start Script (Fixed) ===" -ForegroundColor Cyan
Write-Host ""

# Method 1: Try with BuildKit disabled
Write-Host "[1/3] Attempting build with BuildKit disabled..." -ForegroundColor Yellow
$env:DOCKER_BUILDKIT = "0"
$env:COMPOSE_DOCKER_CLI_BUILD = "0"

# Stop existing containers
docker-compose down 2>$null | Out-Null

# Try to build
Write-Host "Building API image..." -ForegroundColor Gray
$buildResult = docker build -f Dockerfile.api -t erp_api:latest . 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build successful!" -ForegroundColor Green
} else {
    Write-Host "Build failed, trying alternative..." -ForegroundColor Yellow
    
    # Method 2: Use docker-compose without BuildKit
    Write-Host "[2/3] Trying docker-compose build..." -ForegroundColor Yellow
    docker-compose build api 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[3/3] Skipping build, starting services only..." -ForegroundColor Yellow
        Write-Host "Note: Services will use pre-built images or pull from registry" -ForegroundColor Gray
    }
}

# Start services
Write-Host ""
Write-Host "Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait
Write-Host "Waiting for services..." -ForegroundColor Gray
Start-Sleep -Seconds 15

# Check status
Write-Host ""
Write-Host "=== Service Status ===" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "=== Access Points ===" -ForegroundColor Cyan
Write-Host "API: http://localhost:8001"
Write-Host "Docs: http://localhost:8001/docs"
Write-Host ""
Write-Host "To view logs: docker-compose logs -f api" -ForegroundColor Gray

