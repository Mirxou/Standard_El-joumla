#!/bin/bash
# Quick Docker Deployment Script

echo "🐳 Logical Version ERP - Docker Deployment"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    
    # Generate random JWT secret
    JWT_SECRET=$(openssl rand -hex 32)
    sed -i "s/change-this-to-random-32-char-string-in-production/$JWT_SECRET/" .env
    
    echo "✅ .env created with random JWT secret"
    echo "⚠️  Please review and update .env file with your settings"
fi

# Build images
echo "🔨 Building Docker images..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"

# Start services
echo "🚀 Starting services..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start services"
    exit 1
fi

echo "✅ Services started"

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    echo -n "."
    sleep 2
done

# Show status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✨ Deployment complete!"
echo ""
echo "📍 Access points:"
echo "   API:       http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Health:    http://localhost:8000/health"
echo ""
echo "📝 Useful commands:"
echo "   View logs:      docker-compose logs -f"
echo "   Stop services:  docker-compose down"
echo "   Restart:        docker-compose restart"
echo ""
