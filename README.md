# AI Smart City Concierge

Production-grade AI Smart City Concierge - 100% Free Tier

## Overview

A comprehensive AI-powered smart city concierge platform built with modern technologies:

- **Python 3.12** + **FastAPI** for the backend API
- **React + TypeScript + Vite** for the frontend
- **PostgreSQL + PostGIS** for geospatial data
- **Redis** for caching and session management
- **ChromaDB** for vector embeddings (dev) / **Qdrant** (production)
- **Docker Compose** for local development
- **Google Cloud Run** for production deployment
- **GitHub Actions** for CI/CD

## AI Models

- **LLM**: Gemini 1.5 Flash (Google AI Studio - Free tier)
- **Embeddings**: BAAI/bge-m3 (1024-dim, local via sentence-transformers)
- **STT**: faster-whisper small (CTranslate2, local)
- **Vision**: CLIP ViT-B/32 (local via transformers)
- **Reranker**: BAAI/bge-reranker-base (local)

## Quick Start

```bash
# 1. Clone and configure
git clone <repo>
cd ai-smart-city-concierge
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# 2. Start all services
docker-compose up -d

# 3. Run migrations
docker-compose exec api alembic upgrade head

# 4. Seed data
docker-compose exec api python scripts/seed.py

# 5. Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Grafana: http://localhost:3001 (admin/admin)
# Jaeger: http://localhost:16686
# MinIO: http://localhost:9001 (minioadmin/minioadmin)
```

## Architecture

See [AI_SMART_CITY_CONCIERGE_ARCHITECTURE.md](AI_SMART_CITY_CONCIERGE_ARCHITECTURE.md) for complete architecture documentation.

## Project Structure

```
ai-smart-city-concierge/
├── apps/
│   ├── api/              # FastAPI backend
│   ├── worker/           # Background workers
│   ├── websocket/        # WebSocket server
│   └── frontend/         # React + TypeScript frontend
├── packages/             # Shared packages
├── docker/               # Dockerfiles
├── infra/                # Terraform modules
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| API | 8000 | FastAPI REST API |
| WebSocket | 8001 | Real-time communication |
| Frontend | 3000 | React SPA (via Nginx) |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & sessions |
| ChromaDB | 8002 | Vector database |
| MinIO | 9000/9001 | Object storage |
| Prometheus | 9090 | Metrics |
| Grafana | 3001 | Dashboards |
| Loki | 3100 | Log aggregation |
| Jaeger | 16686 | Distributed tracing |

## Environment Variables

See `.env.example` for all required variables.

### Required
- `GEMINI_API_KEY` - Get from [Google AI Studio](https://aistudio.google.com/) (Free)

### Optional
- `OPENCHARGEMAP_API_KEY` - EV charging stations
- `SOCRATA_APP_TOKEN` - Open data portals

## Development

```bash
# Run tests
docker-compose exec api pytest

# Lint
docker-compose exec api ruff check .
docker-compose exec api ruff format .

# Type check
docker-compose exec api pyright

# Generate migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head
```

## License

MIT"# Citypi" 
