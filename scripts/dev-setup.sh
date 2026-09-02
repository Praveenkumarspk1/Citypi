#!/bin/bash
# dev-setup.sh - One-command development environment startup
# Usage: ./scripts/dev-setup.sh

set -e

echo "🚀 Starting AI Smart City Concierge Development Environment"
echo "============================================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

echo "✅ All prerequisites installed"

# Check for .env files
echo "📋 Checking environment files..."
if [ ! -f apps/api/.env ]; then
    echo "📝 Creating apps/api/.env from example..."
    cp apps/api/.env.example apps/api/.env
fi

if [ ! -f apps/worker/.env ]; then
    echo "📝 Creating apps/worker/.env from example..."
    cp apps/worker/.env.example apps/worker/.env
fi

if [ ! -f apps/websocket/.env ]; then
    echo "📝 Creating apps/websocket/.env from example..."
    cp apps/websocket/.env.example apps/websocket/.env
fi

echo "✅ Environment files ready"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
poetry install --all-extras

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd apps/frontend && npm ci && cd ../..

# Start Docker services
echo "🐳 Starting Docker services..."
docker compose -f docker/docker-compose.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Run database migrations
echo "🗄️  Running database migrations..."
cd apps/api && poetry run alembic upgrade head && cd ../..

# Seed database
echo "🌱 Seeding database..."
python scripts/db-seed.py

# Verify all services
echo "🔍 Verifying all services..."
./scripts/health-check.sh

echo ""
echo "✅ Development environment ready!"
echo "============================================================="
echo "🌐 Frontend:     http://localhost:3000"
echo "🔧 API Docs:     http://localhost:8000/docs"
echo "📊 Grafana:      http://localhost:3001 (admin/admin)"
echo "📈 Prometheus:   http://localhost:9090"
echo "🔍 Jaeger:       http://localhost:16686"
echo "🗄️  MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)"
echo ""
echo "To stop: docker compose -f docker/docker-compose.yml down"
echo "To view logs: docker compose -f docker/docker-compose.yml logs -f"