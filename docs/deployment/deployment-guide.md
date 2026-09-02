# Deployment Guide

## Local Development (Docker Compose)

### Prerequisites
- Docker Desktop 24+
- Docker Compose v2+
- 8GB RAM available

### Quick Start
```bash
# Clone repository
git clone <repo-url>
cd ai-smart-city-concierge

# Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Start all services
make dev-up

# Run migrations
make db-migrate

# Access services
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Grafana: http://localhost:3001
```

## Production Deployment

### Infrastructure (Terraform)
```bash
cd infra/terraform
terraform init
terraform workspace new prod
terraform apply -var-file=environments/prod/main.tfvars
```

### CI/CD (GitHub Actions)
- Push to `develop` → auto-deploy to staging
- Push to `main` → auto-deploy to production
- Security scans run on every PR

### Database Migrations
```bash
# Run migrations
docker compose exec api alembic upgrade head

# Create new migration
docker compose exec api alembic revision --autogenerate -m "description"
```

### Secrets Management
Required secrets (GitHub Actions):
- `GEMINI_API_KEY` — Google AI Studio API key
- `JWT_SECRET_KEY` — JWT signing key
- `POSTGRES_PASSWORD` — Database password
- `REDIS_PASSWORD` — Redis password
