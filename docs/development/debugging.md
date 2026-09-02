# Debugging Guide

## Backend Debugging

### API Issues
1. Check logs: `docker compose logs api`
2. Access Swagger UI: http://localhost:8000/docs
3. Check health: `curl http://localhost:8000/health`

### Database Issues
```bash
# Connect to database
docker compose exec postgres psql -U postgres -d concierge

# Check migrations
poetry run alembic current
poetry run alembic history
```

### Redis Issues
```bash
# Connect to Redis
docker compose exec redis redis-cli

# Check keys
KEYS *
```

## Frontend Debugging

### React DevTools
Install React DevTools browser extension for component inspection.

### Network Issues
1. Check browser DevTools Network tab
2. Verify API URL in `.env`: `VITE_API_URL=http://localhost:8000/api/v1`
3. Check CORS settings in API middleware

### State Issues
Use Zustand DevTools or React Query DevTools (built into providers).

## Observability

### Grafana Dashboards
- URL: http://localhost:3001
- Default login: admin/admin
- Pre-configured dashboards: API, Database, Cache, Business

### Jaeger Tracing
- URL: http://localhost:16686
- Search traces by service name

### Logs (Loki)
```bash
# Query logs
docker compose logs -f api
docker compose logs -f worker
```

## Common Issues

### Port Conflicts
```bash
# Check port usage
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

### Docker Issues
```bash
# Reset everything
docker compose down -v
docker compose up -d --build
```

### Migration Issues
```bash
# Reset migrations
poetry run alembic downgrade base
poetry run alembic upgrade head
```
