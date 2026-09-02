# ADR 005: Docker Compose for All Services

## Status
Accepted

## Context
The system has multiple services (API, Worker, WebSocket, Frontend) and data stores (PostgreSQL, Redis, ChromaDB, MinIO). We need a simple way to run everything locally without cloud dependencies.

## Decision
Use Docker Compose for local development and deployment:
- Single `docker-compose.yml` for all services
- Dev and prod override files for environment-specific config
- Health checks and service dependencies
- Volume mounts for hot reload in development

## Consequences
- **Pros**: One-command startup, local parity with prod, no cloud lock-in
- **Cons**: Not suitable for large-scale production (use K8s for that)
