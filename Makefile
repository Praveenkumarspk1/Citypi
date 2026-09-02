.PHONY: help dev-up dev-down test lint typecheck build clean db-migrate db-seed

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
dev-up: ## Start all services with Docker Compose
	docker compose -f docker/docker-compose.yml up -d

dev-down: ## Stop all services
	docker compose -f docker/docker-compose.yml down

dev-build: ## Build and start all services
	docker compose -f docker/docker-compose.yml up -d --build

# Backend
run-api: ## Run API service locally
	poetry run python -m apps.api.src.main

run-worker: ## Run worker service locally
	poetry run python -m apps.worker.src.main

# Testing
test: ## Run all tests
	poetry run pytest apps/api/tests -v && cd apps/frontend && npm run test

test-backend: ## Run backend tests
	poetry run pytest apps/api/tests -v

test-frontend: ## Run frontend tests
	cd apps/frontend && npm run test

# Code Quality
lint: ## Run all linters
	poetry run ruff check apps/api/src
	poetry run ruff format --check apps/api/src
	cd apps/frontend && npm run lint

typecheck: ## Run type checkers
	poetry run pyright apps/api/src
	cd apps/frontend && npm run typecheck

# Database
db-migrate: ## Run database migrations
	poetry run alembic upgrade head

db-seed: ## Seed database with sample data
	./scripts/db-seed.sh

# Build
build: ## Build all Docker images
	docker compose -f docker/docker-compose.yml build

# Clean
clean: ## Remove build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache 2>/dev/null || true
