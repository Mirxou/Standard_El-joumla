#!/bin/bash
# Docker Start Script (Linux/Mac)
# Usage: bash scripts/docker-start.sh

set -e

echo "🚀 بدء تشغيل Docker Containers..."
echo ""

# Disable BuildKit to avoid gRPC errors
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0

# Stop any existing containers
echo "🛑 إيقاف الـ Containers الموجودة..."
docker-compose down 2>/dev/null || true

# Build images (if needed)
echo ""
echo "🔨 بناء Docker Images..."
docker-compose build --no-cache

# Start services
echo ""
echo "🚀 تشغيل الخدمات..."
docker-compose up -d

# Wait a bit for services to start
echo ""
echo "⏳ انتظار بدء الخدمات..."
sleep 10

# Check status
echo ""
echo "📊 حالة الخدمات:"
docker-compose ps

echo ""
echo "✅ تم تشغيل Docker Containers!"
echo ""
echo "📋 Access Points:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Grafana: http://localhost:3001 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "📝 لعرض Logs: docker-compose logs -f"

