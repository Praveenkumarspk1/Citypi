# Development Guide

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+
- Poetry 1.7+
- Docker Desktop

### Initial Setup
```bash
# Run the dev setup script
./scripts/dev-setup.sh

# Or manually:
# 1. Install Python dependencies
poetry install

# 2. Install frontend dependencies
cd apps/frontend && npm install && cd ../..

# 3. Start infrastructure services
docker compose -f docker/docker-compose.yml up -d postgres redis chromadb minio

# 4. Run migrations
make db-migrate

# 5. Start API (terminal 1)
make run-api

# 6. Start worker (terminal 2)
make run-worker

# 7. Start frontend (terminal 3)
cd apps/frontend && npm run dev
```

## Project Structure
```
apps/
├── api/          # FastAPI backend (Clean Architecture)
├── worker/       # Background task worker
├── websocket/    # WebSocket real-time service
└── frontend/     # React + TypeScript frontend
packages/
├── shared-types/     # Shared TypeScript/Python types
├── shared-config/    # Shared configuration
├── api-client/       # Generated API client
└── ui-components/    # Shared UI components
```

## Code Quality
```bash
# Linting
make lint

# Type checking
make typecheck

# Testing
make test

# All checks
make lint && make typecheck && make test
```

## Testing Strategy
- **Unit Tests**: Domain logic, application services (pytest, vitest)
- **Integration Tests**: API endpoints, database repositories
- **Contract Tests**: API schema validation
- **E2E Tests**: Critical user journeys (Playwright)

## Debugging
- API: http://localhost:8000/docs (Swagger UI)
- Grafana: http://localhost:3001 (admin/admin)
- Jaeger: http://localhost:16686 (distributed traces)
- MinIO: http://localhost:9001 (minioadmin/minioadmin)
