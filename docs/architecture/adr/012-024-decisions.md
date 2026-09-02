# ADR 012-024: Additional Architecture Decisions

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
Testing stack: pytest (backend unit/integration), vitest (frontend unit), Playwright (E2E).
