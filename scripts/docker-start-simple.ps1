# Simple Docker Start Script (without building)
# Usage: .\scripts\docker-start-simple.ps1

Write-Host "Starting Docker Containers (using pre-built images)..." -ForegroundColor Cyan
Write-Host ""

# Stop any existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null

# Start services without building
Write-Host "Starting services..." -ForegroundColor Yellow
docker-compose up -d --no-build

# Wait for services to start
Write-Host ""
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check status
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "Access Points:" -ForegroundColor Cyan
Write-Host "  - API: http://localhost:8001"
Write-Host "  - API Docs: http://localhost:8001/docs"

