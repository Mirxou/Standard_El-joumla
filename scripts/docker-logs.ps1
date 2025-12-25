# Docker Logs Script for PowerShell
# Usage: .\scripts\docker-logs.ps1 [service_name]

param(
    [string]$Service = ""
)

if ($Service -eq "") {
    Write-Host "Showing logs for all services..." -ForegroundColor Cyan
    docker-compose logs -f
} else {
    Write-Host "Showing logs for service: $Service" -ForegroundColor Cyan
    docker-compose logs -f $Service
}
