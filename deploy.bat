@echo off
REM Quick Docker Deployment Script for Windows

echo ================================
echo Logical Version ERP - Docker Deployment
echo ================================

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose is not installed.
    pause
    exit /b 1
)

echo [OK] Docker and Docker Compose are installed

REM Check if .env exists
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
    echo [OK] .env created
    echo WARNING: Please update .env file with your settings
    pause
)

REM Build images
echo.
echo Building Docker images...
docker-compose build

if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo [OK] Build successful

REM Start services
echo.
echo Starting services...
docker-compose up -d

if %errorlevel% neq 0 (
    echo ERROR: Failed to start services
    pause
    exit /b 1
)

echo [OK] Services started

REM Wait for API
echo.
echo Waiting for API to be ready...
timeout /t 10 /nobreak

REM Show status
echo.
echo Service Status:
docker-compose ps

echo.
echo =====================================
echo Deployment complete!
echo =====================================
echo.
echo Access points:
echo    API:       http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo    Health:    http://localhost:8000/health
echo.
echo Useful commands:
echo    View logs:      docker-compose logs -f
echo    Stop services:  docker-compose down
echo    Restart:        docker-compose restart
echo.
pause
