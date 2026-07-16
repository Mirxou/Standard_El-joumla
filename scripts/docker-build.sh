#!/bin/bash
# Docker Build Script with BuildKit disabled
# Usage: bash scripts/docker-build.sh

set -e

echo "🔨 بناء Docker Images (مع تعطيل BuildKit)..."
echo ""

# Disable BuildKit to avoid gRPC errors
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0

# Build images
docker-compose build --no-cache

echo ""
echo "✅ تم بناء Docker Images بنجاح!"

