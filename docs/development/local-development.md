# Local Development Guide

## Environment Setup

### Python Environment
```bash
# Install Poetry if not present
pip install poetry

# Install dependencies
poetry install

# Activate shell
poetry shell
```

### Node.js Environment
```bash
cd apps/frontend
npm install
```

## Running Services

### Option 1: Docker Compose (Recommended)
```bash
make dev-up        # Start all services
make dev-down      # Stop all services
make dev-build     # Rebuild and start
```

### Option 2: Manual
```bash
# Terminal 1: Infrastructure
docker compose -f docker/docker-compose.yml up -d postgres redis chromadb minio

# Terminal 2: API
make run-api

# Terminal 3: Worker
make run-worker

# Terminal 4: Frontend
cd apps/frontend && npm run dev
```

## Code Quality
```bash
# Linting
make lint          # All linters
poetry run ruff check .  # Python only

# Type checking
make typecheck     # All type checkers
poetry run pyright # Python only

# Formatting
poetry run ruff format .
npx prettier --write apps/frontend/src
```

## Common Commands
```bash
make help          # Show all available commands
make test          # Run all tests
make db-migrate    # Run migrations
make db-seed       # Seed sample data
```

## IDE Setup
Recommended VS Code extensions:
- Ruff (astral-sh.ruff)
- Pyright
- ESLint
- Prettier
- Tailwind CSS IntelliSense
