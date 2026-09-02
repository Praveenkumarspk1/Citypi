# AI Smart City Concierge - Project Context & Implementation Tracker

**Last Updated:** 2026-07-25  
**Architecture Version:** 1.0 (Free Tier - Docker Compose)  
**Status:** Architecture Complete | Implementation In Progress

---

## 📋 Executive Summary

Building a production-grade AI Smart City Concierge platform running 100% free on local Docker Compose (8GB RAM). Multi-modal AI with Gemini 1.5 Flash API, BAAI/bge-m3 embeddings, faster-whisper STT, CLIP vision, ChromaDB vector search, and full observability stack.

---

## ✅ COMPLETED: Architecture Design (100%)

### 1. High-Level Architecture
- [x] Docker Compose stack diagram with all services
- [x] Service port mapping (8000 API, 8001 WS, 5432 PG, 6379 Redis, 8002 ChromaDB, 9000 MinIO, 9090 Prometheus, 3001 Grafana, 3100 Loki, 16686 Jaeger)
- [x] Model selection: Gemini 1.5 Flash, BAAI/bge-m3 (1024-dim), faster-whisper small, CLIP ViT-B/32, bge-reranker-base
- [x] Free tier decisions documented (no credit card required)

### 2. Folder Structure (Monorepo)
- [x] Nx/Turborepo structure defined
- [x] Apps: api, worker, websocket, frontend
- [x] Packages: shared-types, shared-config, api-client, ui-components
- [x] Infra: Terraform modules, K8s manifests, Helm charts
- [x] Docs: Architecture, API, Deployment, Development

### 3. Module Breakdown (Clean Architecture)
- [x] **Domain Layer**: Entities, Value Objects, Aggregates, Domain Events, Repository Interfaces, Domain Services, Specifications, Exceptions
- [x] **Application Layer**: Commands (CQRS Write), Queries (CQRS Read), Handlers, DTOs, Ports, Application Services, Event Handlers
- [x] **Infrastructure Layer**: SQLAlchemy persistence, Redis cache, Vector stores (ChromaDB/Qdrant), External API adapters, Messaging, Storage, Auth, Config, Observability
- [x] **Interface Layer**: REST API (FastAPI), WebSocket, GraphQL (optional)
- [x] **Shared Kernel**: CQRS base classes, Mediator, Utils, Exceptions

### 4. API Design
- [x] REST endpoints (Conversations, Messages, Itineraries, POIs, Transit, Weather, Media, Users)
- [x] Streaming (SSE) and WebSocket protocols
- [x] GraphQL schema (optional)
- [x] Request/Response examples with JSON

### 5. Database Schema (PostgreSQL + PostGIS)
- [x] Core tables: users, user_preferences, conversations, messages, pois, transit_stops, transit_routes, weather_data, itineraries, itinerary_items, media, feedback, analytics_events, recommendations, search_history, favorite_places
- [x] Indexes, constraints, triggers for updated_at
- [x] PostGIS geography types for geospatial queries

### 6. Vector DB Schema
- [x] ChromaDB collections: poi_embeddings, conversation_embeddings, itinerary_embeddings, user_preference_embeddings
- [x] Metadata schemas with filtering support
- [x] HNSW index configuration

### 7. Request Flows
- [x] Chat flow (user message → intent → tools → LLM → stream response)
- [x] Transit routing flow (origin/dest → GTFS → router → routes)
- [x] POI search flow (query → embed → vector search → rerank → filter → response)
- [x] Voice flow (audio → Whisper → text → chat flow)
- [x] Image flow (image → CLIP → analysis → chat flow)

### 8. Deployment Architecture
- [x] Cloud Run services (API, Worker, WebSocket, Frontend)
- [x] Terraform modules (Cloud Run, Cloud SQL, Redis, Qdrant, GCS, Pub/Sub, Service Mesh, Secrets, IAM, Monitoring, Logging, VPC)
- [x] GitHub Actions CI/CD pipelines (CI, CD staging, CD production, security scan, dependency update, performance test)

### 9. Security Architecture
- [x] Defense in depth (network, application, data, identity)
- [x] AuthN/AuthZ (JWT, API keys, Firebase, RBAC)
- [x] Secrets management (Secret Manager, .env for local)
- [x] Compliance (GDPR, data retention, encryption)

### 10. Scalability Plan
- [x] Horizontal scaling (Cloud Run autoscaling, Redis Cluster, Qdrant clustering)
- [x] Capacity planning (RPS targets, memory/CPU budgets)
- [x] Disaster recovery (RPO/RTO, backup strategies, multi-region)

---

## 🏗️ IMPLEMENTATION STATUS

### Infrastructure & DevOps
| Component | Status | Notes |
|-----------|--------|-------|
| Docker Compose (local) | 🔄 **In Progress** | docker-compose.yml exists, needs validation |
| Dockerfiles (API, Worker, WS, Frontend) | ✅ **Done** | Multi-stage builds created |
| Nginx config (Frontend) | ✅ **Done** | SPA proxy + static files |
| GitHub Actions CI/CD | ❌ **Not Started** | Workflows directory empty |
| Terraform modules | ❌ **Not Started** | Directory structure only |
| Environment configs (.env.example) | ✅ **Done** | Root and app-level examples |
| **DI Container (dependencies.py)** | ✅ **Done** | Complete wiring of all ports to adapters |
### Backend - API Service (FastAPI)
| Layer | Component | Status | Files |
|-------|-----------|--------|-------|
| **Domain** | Entities (User, Conversation, POI, Itinerary, Transit, Weather, Media, Feedback, Analytics) | ✅ **Done** | 9 entity files |
| **Domain** | Value Objects (Coordinates, Address, TransitRoute, WeatherCondition, MediaContent) | ✅ **Done** | 5 VO files |
| **Domain** | Aggregates (Conversation, Itinerary, UserProfile) | ✅ **Done** | 3 aggregate files |
| **Domain** | Domain Events | ✅ **Done** | domain_events.py |
| **Domain** | Repository Interfaces | ✅ **Done** | 7 repository interfaces |
| **Domain** | Domain Services (ItineraryPlanner, TransitRouter, POIRanker, ConversationManager) | ✅ **Done** | 4 service files |
| **Domain** | Specifications | ✅ **Done** | 2 spec files |
| **Domain** | Exceptions | ✅ **Done** | 2 exception files |
| **Application** | Commands (CQRS Write) | ✅ **Done** | 8 command files |
| **Application** | Queries (CQRS Read) | ✅ **Done** | 4 query files |
| **Application** | Command/Query Handlers | 🔄 **Partial** | Handlers directory exists |
| **Application** | DTOs (Request/Response) | ✅ **Done** | request.py, response.py |
| **Application** | Ports (Interfaces) | ✅ **Done** | 11 port files |
| **Application** | Application Services | ✅ **Done** | 7 service files |
| **Application** | Event Handlers | ✅ **Done** | event_handlers.py |
| **Infrastructure** | SQLAlchemy Models | ✅ **Done** | 8 model files |
| **Infrastructure** | SQLAlchemy Repositories | 🔄 **Partial** | Repositories directory exists |
| **Infrastructure** | Database Config/Session | ✅ **Done** | database.py, session.py |
| **Infrastructure** | Redis Cache/Session | ✅ **Done** | cache_repository.py, session_store.py |
| **Infrastructure** | Vector Store Adapters (ChromaDB, Qdrant) | ✅ **Done** | 3 adapter files |
| **Infrastructure** | External API Clients (Gemini, bge-m3, Whisper, CLIP, Overpass, Nominatim, Open-Meteo, GTFS) | ✅ **Done** | 8 client files |
| **Infrastructure** | Messaging (Event Bus, Outbox) | ✅ **Done** | 3 messaging files |
| **Infrastructure** | Storage (GCS, Local) | ✅ **Done** | 2 storage files |
| **Infrastructure** | Auth (Firebase, JWT, API Key) | ✅ **Done** | 3 auth files |
| **Infrastructure** | Config (Settings, DB, Redis, Vector, External APIs) | ✅ **Done** | 5 config files |
| **Infrastructure** | Observability (Logging, Metrics, Tracing, Health) | ✅ **Done** | 4 observability files |
| **Interface** | REST Routes (v1) | ✅ **Done** | 9 route files |
| **Interface** | Middleware (Auth, Rate Limit, Logging, Tracing, Error Handling) | ✅ **Done** | 5 middleware files |
| **Interface** | Dependencies (DI Container) | ✅ **Done** | dependencies.py |
| **Interface** | Schemas (Request/Response) | ✅ **Done** | schemas directory |
| **Interface** | WebSocket Handlers | ✅ **Done** | 3 handler files |
| **Interface** | GraphQL (Optional) | ❌ **Not Started** | Directory only |
| **Main** | Application Entry Point | ✅ **Done** | main.py |
### Backend - API Service (FastAPI)
| Layer | Component | Status | Files |
|-------|-----------|--------|-------|
| **Domain** | Entities (User, Conversation, POI, Itinerary, Transit, Weather, Media, Feedback, Analytics) | ✅ **Done** | 9 entity files |
| **Domain** | Value Objects (Coordinates, Address, TransitRoute, WeatherCondition, MediaContent) | ✅ **Done** | 5 VO files |
| **Domain** | Aggregates (Conversation, Itinerary, UserProfile) | ✅ **Done** | 3 aggregate files |
| **Domain** | Domain Events | ✅ **Done** | domain_events.py |
| **Domain** | Repository Interfaces | ✅ **Done** | 7 repository interfaces |
| **Domain** | Domain Services (ItineraryPlanner, TransitRouter, POIRanker, ConversationManager) | ✅ **Done** | 4 service files |
| **Domain** | Specifications | ✅ **Done** | 2 spec files |
| **Domain** | Exceptions | ✅ **Done** | 2 exception files |
| **Application** | Commands (CQRS Write) | ✅ **Done** | 8 command files |
| **Application** | Queries (CQRS Read) | ✅ **Done** | 4 query files |
| **Application** | Command/Query Handlers | 🔄 **Partial** | Handlers directory exists |
| **Application** | DTOs (Request/Response) | ✅ **Done** | request.py, response.py |
| **Application** | Ports (Interfaces) | ✅ **Done** | 11 port files |
| **Application** | Application Services | ✅ **Done** | 7 service files |
| **Application** | Event Handlers | ✅ **Done** | event_handlers.py |
| **Infrastructure** | SQLAlchemy Models | ✅ **Done** | 8 model files |
| **Infrastructure** | SQLAlchemy Repositories | 🔄 **Partial** | Repositories directory exists |
| **Infrastructure** | Database Config/Session | ✅ **Done** | database.py, session.py |
| **Infrastructure** | Redis Cache/Session | ✅ **Done** | cache_repository.py, session_store.py |
| **Infrastructure** | Vector Store Adapters (ChromaDB, Qdrant) | ✅ **Done** | 3 adapter files |
| **Infrastructure** | External API Clients (Gemini, bge-m3, Whisper, CLIP, Overpass, Nominatim, Open-Meteo, GTFS) | ✅ **Done** | 8 client files |
| **Infrastructure** | Messaging (Event Bus, Outbox) | ✅ **Done** | 3 messaging files |
| **Infrastructure** | Storage (GCS, Local) | ✅ **Done** | 2 storage files |
| **Infrastructure** | Auth (Firebase, JWT, API Key) | ✅ **Done** | 3 auth files |
| **Infrastructure** | Config (Settings, DB, Redis, Vector, External APIs) | ✅ **Done** | 5 config files |
| **Infrastructure** | Observability (Logging, Metrics, Tracing, Health) | ✅ **Done** | 4 observability files |
| **Interface** | REST Routes (v1) | ✅ **Done** | 9 route files |
| **Interface** | Middleware (Auth, Rate Limit, Logging, Tracing, Error Handling) | ✅ **Done** | 5 middleware files |
| **Interface** | Dependencies (DI Container) | ✅ **Done** | dependencies.py |
| **Interface** | Schemas (Request/Response) | ✅ **Done** | schemas directory |
| **Interface** | WebSocket Handlers | ✅ **Done** | 3 handler files |
| **Interface** | GraphQL (Optional) | ❌ **Not Started** | Directory only |
| **Main** | Application Entry Point | ✅ **Done** | main.py |
| **Routes** | Conversations (DI Wired) | ✅ **Done** | conversations.py updated |

### Backend - API Service (FastAPI)
| Layer | Component | Status | Files |
|-------|-----------|--------|-------|
| **Domain** | Entities (User, Conversation, POI, Itinerary, Transit, Weather, Media, Feedback, Analytics) | ✅ **Done** | 9 entity files |
| **Domain** | Value Objects (Coordinates, Address, TransitRoute, WeatherCondition, MediaContent) | ✅ **Done** | 5 VO files |
| **Domain** | Aggregates (Conversation, Itinerary, UserProfile) | ✅ **Done** | 3 aggregate files |
| **Domain** | Domain Events | ✅ **Done** | domain_events.py |
| **Domain** | Repository Interfaces | ✅ **Done** | 7 repository interfaces |
| **Domain** | Domain Services (ItineraryPlanner, TransitRouter, POIRanker, ConversationManager) | ✅ **Done** | 4 service files |
| **Domain** | Specifications | ✅ **Done** | 2 spec files |
| **Domain** | Exceptions | ✅ **Done** | 2 exception files |
| **Application** | Commands (CQRS Write) | ✅ **Done** | 8 command files |
| **Application** | Queries (CQRS Read) | ✅ **Done** | 4 query files |
| **Application** | Command/Query Handlers | 🔄 **Partial** | Handlers directory exists |
| **Application** | DTOs (Request/Response) | ✅ **Done** | request.py, response.py |
| **Application** | Ports (Interfaces) | ✅ **Done** | 11 port files |
| **Application** | Application Services | ✅ **Done** | 7 service files |
| **Application** | Event Handlers | ✅ **Done** | event_handlers.py |
| **Infrastructure** | SQLAlchemy Models | ✅ **Done** | 8 model files |
| **Infrastructure** | SQLAlchemy Repositories | 🔄 **Partial** | Repositories directory exists |
| **Infrastructure** | Database Config/Session | ✅ **Done** | database.py, session.py |
| **Infrastructure** | Redis Cache/Session | ✅ **Done** | cache_repository.py, session_store.py |
| **Infrastructure** | Vector Store Adapters (ChromaDB, Qdrant) | ✅ **Done** | 3 adapter files |
| **Infrastructure** | External API Clients (Gemini, bge-m3, Whisper, CLIP, Overpass, Nominatim, Open-Meteo, GTFS) | ✅ **Done** | 8 client files |
| **Infrastructure** | Messaging (Event Bus, Outbox) | ✅ **Done** | 3 messaging files |
| **Infrastructure** | Storage (GCS, Local) | ✅ **Done** | 2 storage files |
| **Infrastructure** | Auth (Firebase, JWT, API Key) | ✅ **Done** | 3 auth files |
| **Infrastructure** | Config (Settings, DB, Redis, Vector, External APIs) | ✅ **Done** | 5 config files |
| **Infrastructure** | Observability (Logging, Metrics, Tracing, Health) | ✅ **Done** | 4 observability files |
| **Interface** | REST Routes (v1) | ✅ **Done** | 9 route files |
| **Interface** | Middleware (Auth, Rate Limit, Logging, Tracing, Error Handling) | ✅ **Done** | 5 middleware files |
| **Interface** | Dependencies (DI Container) | ✅ **Done** | dependencies.py |
| **Interface** | Schemas (Request/Response) | ✅ **Done** | schemas directory |
| **Interface** | WebSocket Handlers | ✅ **Done** | 3 handler files |
| **Interface** | GraphQL (Optional) | ❌ **Not Started** | Directory only |
| **Main** | Application Entry Point | ✅ **Done** | main.py |

### Backend - Worker Service
| Component | Status | Notes |
|-----------|--------|-------|
| Tasks (Embedding, POI Enrichment, Transit Sync, Weather Sync, Itinerary Gen, Media Processing, Conversation Analysis) | 🔄 **Partial** | Task files exist |
| Consumers (Event Consumers, Dead Letter Handler) | 🔄 **Partial** | Consumer files exist |
| Scheduler (Cron Jobs, Scheduler) | 🔄 **Partial** | Scheduler files exist |
| Main Entry Point | ✅ **Done** | main.py |

### Backend - WebSocket Service
| Component | Status | Notes |
|-----------|--------|-------|
| Connection Manager | ✅ **Done** | connection_manager.py |
| Message Router | ✅ **Done** | message_router.py |
| Presence Manager | ✅ **Done** | presence_manager.py |
| Room Manager | ✅ **Done** | room_manager.py |
| Main Entry Point | ✅ **Done** | main.py |

### Frontend (React + TypeScript + Vite)
| Feature | Status | Notes |
|---------|--------|-------|
| Project Setup (package.json, tsconfig, vite.config, tailwind) | ✅ **Done** | Config files exist |
| App Structure (App.tsx, routes, providers, layout) | ✅ **Done** | App-level components |
| Chat Feature (Window, Messages, Streaming, Voice, Image, Typing) | ✅ **Done** | 5 components + hooks + API + store |
| Map Feature (View, POI Markers, Routes, Transit, Weather) | ✅ **Done** | 5 components + hooks + store |
| Transit Feature (Planner, Options, Real-time, Details) | ✅ **Done** | 4 components + hooks + API |
| Weather Feature (Dashboard, Forecast, Alerts) | ✅ **Done** | 3 components + hooks + API |
| Itinerary Feature (Builder, Day Planner, POI Card, Share) | ✅ **Done** | 4 components + hooks + API |
| User Feature (Profile, Preferences, Auth) | ✅ **Done** | 3 components + hooks + API |
| Shared UI Components (shadcn/ui base) | ✅ **Done** | UI component directory |
| Shared Hooks (useApi, useWebSocket, useLocalStorage) | ✅ **Done** | 3 hook files |
| Shared Utils (API, Date, Coordinates, Validation) | ✅ **Done** | 4 util files |
| Types (API, Domain, UI) | ✅ **Done** | 3 type files |
| Constants | ✅ **Done** | 3 constant files |
| Styles (Globals, Variables, Tailwind) | ✅ **Done** | 3 CSS files |
| Main Entry (main.tsx) | ✅ **Done** | main.tsx |
| Tests (Unit, Integration, E2E, Visual) | ❌ **Not Started** | Directory structure only |

### Shared Packages
| Package | Status | Notes |
|---------|--------|-------|
| shared-types (Python + TypeScript) | 🔄 **Structure Only** | pyproject.toml, package.json only |
| shared-config (Python + TypeScript) | 🔄 **Structure Only** | Config directories only |
| api-client (Python + TypeScript) | 🔄 **Structure Only** | Package.json/pyproject.toml only |
| ui-components | 🔄 **Structure Only** | package.json only |

---

## 📦 REMAINING WORK (Priority Order)

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] **Validate Docker Compose** - Run `docker-compose up` and fix any issues
- [ ] **Database Migrations** - Create Alembic migrations from SQLAlchemy models
- [ ] **Seed Data Script** - Populate POIs, transit agencies, sample data
- [ ] **Health Checks** - Verify all services respond to health endpoints
- [ ] **Local Development Script** - `dev-setup.sh` for one-command startup

### Phase 2: Backend Integration (Week 2-3)
- [ ] **Wire DI Container** - Connect all ports to adapters in `dependencies.py`
- [ ] **Implement Repository Methods** - Complete SQLAlchemy repository implementations
- [ ] **Implement Command/Query Handlers** - Connect handlers to services
- [ ] **Integrate External APIs** - Test Gemini, bge-m3, Whisper, CLIP clients
- [ ] **Vector Store Integration** - Embedding generation pipeline (Worker)
- [ ] **Event Bus Wiring** - Connect domain events to handlers
- [ ] **Authentication Flow** - JWT issuance, validation, refresh
- [ ] **Rate Limiting** - Redis-based rate limiter implementation

### Phase 3: Feature Completion (Week 3-4)
- [ ] **Chat Streaming** - SSE/WebSocket token streaming implementation
- [ ] **Transit Routing** - GTFS parsing, route calculation, real-time departures
- [ ] **POI Search** - Hybrid search (vector + keyword + geospatial), reranking
- [ ] **Itinerary Generation** - LLM-powered planning with constraints
- [ ] **Voice Input** - WebM audio → Whisper → text → chat flow
- [ ] **Image Analysis** - Upload → CLIP → description → chat flow
- [ ] **Weather Integration** - Current, forecast, alerts from Open-Meteo
- [ ] **Recommendation Engine** - LightFM collaborative filtering

### Phase 4: Frontend Polish (Week 4-5)
- [ ] **API Client Generation** - OpenAPI → TypeScript client
- [ ] **State Management** - Connect TanStack Query + Zustand stores
- [ ] **Real-time Updates** - WebSocket integration for chat, presence, typing
- [ ] **Map Integration** - MapLibre GL JS with POI markers, route layers
- [ ] **Responsive Design** - Mobile-first, accessibility (WCAG AA)
- [ ] **Error Boundaries** - Graceful error handling UI
- [ ] **Loading States** - Skeletons, spinners, progressive loading

### Phase 5: Testing & Quality (Week 5-6)
- [ ] **Unit Tests** - Domain, Application, Infrastructure layers (target 80%+)
- [ ] **Integration Tests** - API endpoints, database, external APIs
- [ ] **Contract Tests** - API schema validation
- [ ] **E2E Tests** - Playwright critical user journeys
- [ ] **Performance Tests** - k6 load testing (target: 100 RPS)
- [ ] **Security Scan** - SAST, dependency audit, container scan

### Phase 6: CI/CD & Deployment (Week 6-7)
- [ ] **GitHub Actions CI** - Lint, type-check, test, build
- [ ] **GitHub Actions CD Staging** - Deploy to Cloud Run staging
- [ ] **GitHub Actions CD Production** - Blue-green deploy to prod
- [ ] **Security Scan Workflow** - Trivy, Snyk, CodeQL
- [ ] **Dependency Update** - Dependabot configuration
- [ ] **Performance Test Workflow** - Scheduled k6 runs
- [ ] **Terraform Apply** - Infrastructure provisioning

### Phase 7: Observability & Hardening (Week 7-8)
- [ ] **Prometheus Metrics** - Custom business metrics, RED metrics
- [ ] **Grafana Dashboards** - API, Database, Cache, Queue, Business
- [ ] **Loki Log Aggregation** - Structured logging, log queries
- [ ] **Jaeger Tracing** - Distributed traces across services
- [ ] **Alerting Rules** - PagerDuty/Slack notifications
- [ ] **Sentry Integration** - Error tracking, performance monitoring
- [ ] **Health Check Endpoints** - Liveness, readiness, startup probes
- [ ] **Circuit Breakers** - Resilience patterns for external APIs

---

## 🎯 KEY TECHNICAL DECISIONS (ADRs)

| ADR | Decision | Status |
|-----|----------|--------|
| 001 | Clean Architecture (Domain/Application/Infrastructure/Interface) | ✅ Implemented |
| 002 | CQRS + Event Sourcing for Conversations/Itineraries | ✅ Implemented |
| 003 | Vector DB: ChromaDB (dev) / Qdrant (prod) | ✅ Implemented |
| 004 | Deployment: Cloud Run + Terraform | 📋 Planned |
| 005 | Event-Driven: Redis Streams (local) / PubSub (prod) | ✅ Implemented |
| 006 | Auth: JWT + Firebase (optional) | ✅ Implemented |
| 007 | LLM: Gemini 1.5 Flash API (free tier) | ✅ Configured |
| 008 | Embeddings: BAAI/bge-m3 local (1024-dim) | ✅ Configured |
| 009 | STT: faster-whisper small (CTranslate2) | ✅ Configured |
| 010 | Vision: CLIP ViT-B/32 (transformers) | ✅ Configured |

---

## 📊 METRICS & TARGETS

| Metric | Target | Current |
|--------|--------|---------|
| **API Latency (p95)** | < 500ms | - |
| **Streaming First Token** | < 1s | - |
| **Vector Search (p95)** | < 100ms | - |
| **Transit Route Calc** | < 2s | - |
| **Uptime** | 99.9% | - |
| **Test Coverage** | > 80% | 0% |
| **Docker Image Size (API)** | < 500MB | - |
| **Memory Usage (Total)** | < 6GB / 8GB | - |
| **Cold Start (Cloud Run)** | < 3s | - |

---

## 🔑 ENVIRONMENT VARIABLES NEEDED

### Required (No Defaults)
```bash
# Google AI Studio (FREE - no CC)
GEMINI_API_KEY=

# Optional: OpenChargeMap (FREE key)
OPENCHARGEMAP_API_KEY=

# Optional: Socrata (FREE)
SOCRATA_APP_TOKEN=
```

### Generated/Configured
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/concierge
POSTGRES_PASSWORD=postgres

# Redis
REDIS_URL=redis://redis:6379/0

# Vector DB
CHROMADB_HOST=chromadb
CHROMADB_PORT=8002

# Object Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=concierge-media

# Auth
JWT_SECRET_KEY=<generate: openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# External APIs (all free, no keys needed)
NOMINATIM_USER_AGENT=concierge/1.0
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1
```

---

## 🚀 QUICK START (Once Phase 1 Complete)

```bash
# 1. Clone and setup
git clone <repo>
cd ai-smart-city-concierge

# 2. Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# 3. Start all services
docker-compose up -d

# 4. Run migrations
docker-compose exec api alembic upgrade head

# 5. Seed data
docker-compose exec api python scripts/seed.py

# 6. Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Grafana: http://localhost:3001 (admin/admin)
# Jaeger: http://localhost:16686
# MinIO: http://localhost:9001 (minioadmin/minioadmin)
```

---

## 📝 NOTES FOR NEXT SESSION

1. **Start with Docker Compose validation** - Run `docker-compose up` and fix any startup issues
2. **Database migrations are critical** - Alembic needs to be set up with the SQLAlchemy models
3. **DI Container wiring** - The `dependencies.py` has `NotImplementedError` placeholders that need real implementations
4. **Worker service** - Background tasks need to be connected to Redis Streams event bus
5. **Frontend API client** - Generate from OpenAPI spec once API is stable

---

## 📁 KEY FILES TO REVIEW

| File | Purpose |
|------|---------|
| `AI_SMART_CITY_CONCIERGE_ARCHITECTURE.md` | Complete architecture reference |
| `docker/docker-compose.yml` | Local development stack |
| `apps/api/src/main.py` | API entry point |
| `apps/api/src/interfaces/api/v1/dependencies.py` | DI container (needs wiring) |
| `apps/api/src/infrastructure/config/settings.py` | Configuration management |
| `apps/frontend/package.json` | Frontend dependencies |
| `.env.example` | Environment template |

---

*This context file should be updated at the end of each development session to track progress.*