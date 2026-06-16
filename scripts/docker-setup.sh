#!/bin/bash
# Docker Setup Script for ERP System
# Usage: ./scripts/docker-setup.sh

set -e

echo "🚀 Setting up ERP System with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .docker.env if it doesn't exist
if [ ! -f .docker.env ]; then
    echo "📝 Creating .docker.env from example..."
    cp .docker.env.example .docker.env
    echo "⚠️  Please edit .docker.env with your configuration before continuing."
    read -p "Press Enter to continue after editing .docker.env..."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data logs monitoring/grafana/dashboards monitoring/grafana/datasources

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Access Points:"
echo "  - API: http://localhost:8001"
echo "  - API Docs: http://localhost:8001/docs"
echo "  - Grafana: http://localhost:3001 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "📝 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"

