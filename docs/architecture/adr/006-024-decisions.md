# ADR 006-024: Additional Architecture Decisions

## ADR 006: PostgreSQL + PostGIS
Use PostgreSQL with PostGIS extension for relational data and geospatial queries. Mature ecosystem, full SQL support, and native geography types.

## ADR 007: Redis 7 (Streams + Cache)
Redis serves as cache (L2), message queue (Streams), session store, and pub/sub. Sub-millisecond latency, built-in data structures.

## ADR 008: Gemini 1.5 Flash (Google AI Studio)
Free tier LLM with 15 RPM and 1M tokens/day. Best cost-quality ratio for chat completions. No credit card required.

## ADR 009: BAAI/bge-m3 Embeddings
1024-dimensional multilingual embeddings. SOTA quality, supports 8K context length. Runs locally without API costs.

## ADR 010: faster-whisper small (Local)
CTranslate2-optimized Whisper model. CPU-friendly, best quality speech-to-text. ~488MB model size.

## ADR 011: CLIP ViT-B/32 (Local)
OpenAI's CLIP model for zero-shot image classification and image embeddings. 512-dim output, ~150MB.

## ADR 012: bge-reranker-base (Local)
Cross-encoder reranker for improving retrieval precision. Re-ranks top-k results from vector search.

## ADR 013: LightFM (Local)
Hybrid collaborative + content-based recommendation. Handles cold start, works with implicit feedback.

## ADR 014: GTFS + GTFS-RT
Open standard for transit data. Static schedules (GTFS) and real-time updates (GTFS-RT). Global coverage.

## ADR 015: Open-Meteo Weather
Free weather API, no API key required. Global coverage, high resolution, current/forecast/historical.

## ADR 016: Overpass + Nominatim
OpenStreetMap ecosystem for POI data and geocoding. Free, global, community-maintained.

## ADR 017: OpenChargeMap
Free API key for EV charging station data. Global coverage, community-maintained.

## ADR 018: Socrata Open Data
Government open data portal API. City-specific datasets for events, permits, statistics.

## ADR 019: GitHub Actions + Docker
Free CI/CD for public repos. Docker Buildx for multi-arch builds. GitHub Pages for frontend hosting.

## ADR 020: OpenTelemetry + Jaeger
Vendor-neutral observability. Distributed tracing with Jaeger for local development.

## ADR 021: Prometheus + Grafana + Loki
Full observability stack. Metrics (Prometheus), dashboards (Grafana), log aggregation (Loki).

## ADR 022: Poetry (Python) / npm (Node)
Modern dependency management. Poetry for Python with lock file, npm for Node.js.

## ADR 023: Ruff + Pyright
Fast Python linting (Ruff) and type checking (Pyright). Replaces flake8, black, mypy.

## ADR 024: pytest + Vitest + Playwright
Testing stack: pytest (backend unit/integration), Vitest (frontend unit), Playwright (E2E).
