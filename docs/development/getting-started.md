# Getting Started

## Quick Start (5 minutes)

### Prerequisites
- Python 3.12+
- Node.js 20+
- Poetry 1.7+
- Docker Desktop

### 1. Clone and Setup
```bash
git clone <repo-url>
cd ai-smart-city-concierge
./scripts/dev-setup.sh
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Start Services
```bash
make dev-up        # Start all Docker services
make db-migrate    # Run database migrations
make db-seed       # Seed sample data
```

### 4. Access
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3001 (admin/admin)
- Jaeger: http://localhost:16686

## Manual Setup
If you prefer not to use Docker:

```bash
# Backend
poetry install
poetry run python -m apps.api.src.main

# Worker (separate terminal)
poetry run python -m apps.worker.src.main

# Frontend (separate terminal)
cd apps/frontend && npm install && npm run dev
```

## Next Steps
- Read the [Local Development Guide](local-development.md)
- Read the [Testing Guide](testing-guide.md)
- Explore the API at http://localhost:8000/docs
