# Docker Start Script for PowerShell (Windows)
# Usage: .\scripts\docker-start.ps1

Write-Host "Starting Docker Containers..." -ForegroundColor Cyan
Write-Host ""

# Disable BuildKit to avoid gRPC errors on Windows
$env:DOCKER_BUILDKIT = "0"
$env:COMPOSE_DOCKER_CLI_BUILD = "0"

# Stop any existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null

# Try building without BuildKit using docker build directly
Write-Host ""
Write-Host "Building Docker Images..." -ForegroundColor Yellow

# Build API image directly
Write-Host "Building API image..." -ForegroundColor Yellow
docker build -f Dockerfile.api -t erp_api:latest . --no-cache 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Build had issues, but continuing..." -ForegroundColor Yellow
}

# Start services (this will pull pre-built images if build failed)
Write-Host ""
Write-Host "Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait a bit for services to start
Write-Host ""
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check status
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "Docker Containers started!" -ForegroundColor Green
Write-Host ""
Write-Host "Access Points:" -ForegroundColor Cyan
Write-Host "  - API: http://localhost:8001" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8001/docs" -ForegroundColor White
Write-Host "  - Grafana: http://localhost:3001 (admin/admin)" -ForegroundColor White
Write-Host "  - Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host ""
Write-Host "To view logs: docker-compose logs -f" -ForegroundColor Yellow
