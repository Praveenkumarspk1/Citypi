# Database Migration Guide

## Overview
We use Alembic for PostgreSQL migrations with async SQLAlchemy.

## Running Migrations

### Local Development
```bash
# Run all pending migrations
make db-migrate

# Or directly
poetry run alembic upgrade head
```

### Production (Cloud Run Job)
```bash
# Create migration job
gcloud run jobs create concierge-db-migrate \
  --image gcr.io/PROJECT_ID/concierge-api:latest \
  --args="alembic,upgrade,head" \
  --region us-central1

# Execute migration
gcloud run jobs execute concierge-db-migrate --region us-central1
```

## Creating New Migrations
```bash
# Auto-generate from model changes
poetry run alembic revision --autogenerate -m "add new table"

# Manual migration
poetry run alembic revision -m "description"
```

## Migration Files
Located at: `apps/api/alembic/versions/`

## Rollback
```bash
# Rollback one revision
poetry run alembic downgrade -1

# Rollback to specific revision
poetry run alembic downgrade <revision_id>
```

## Best Practices
- Always test migrations locally before production
- Use `--autogenerate` for simple changes, manual for complex
- Never modify existing migration files
- Include both `upgrade()` and `downgrade()` functions
