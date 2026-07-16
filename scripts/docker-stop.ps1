# Docker Stop Script for PowerShell
# Usage: .\scripts\docker-stop.ps1

Write-Host "Stopping Docker Containers..." -ForegroundColor Yellow

docker-compose down

Write-Host ""
Write-Host "All containers stopped!" -ForegroundColor Green
