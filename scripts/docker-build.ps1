# Docker Build Script for PowerShell (Windows)
# Usage: .\scripts\docker-build.ps1

Write-Host "Building Docker Images (with BuildKit disabled)..." -ForegroundColor Cyan
Write-Host ""

# Disable BuildKit to avoid gRPC errors
$env:DOCKER_BUILDKIT = "0"
$env:COMPOSE_DOCKER_CLI_BUILD = "0"

# Build API image directly
Write-Host "Building API image..." -ForegroundColor Yellow
docker build -f Dockerfile.api -t erp_api:latest . --no-cache

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Docker Images built successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Build failed. Trying alternative method..." -ForegroundColor Yellow
    
    # Try with compose but without BuildKit
    docker-compose build --no-cache
}
