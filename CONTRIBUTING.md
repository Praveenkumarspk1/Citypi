# Contributing to AI Smart City Concierge

Thank you for your interest in contributing! This document outlines how to get started.

## Development Setup

1. **Prerequisites**: Python 3.12+, Node.js 20+, Poetry, Docker Desktop
2. **Clone**: `git clone <repo-url> && cd ai-smart-city-concierge`
3. **Install**: `poetry install` (backend) and `cd apps/frontend && npm install` (frontend)
4. **Start**: `make dev-up` (Docker Compose)

## Code Style

- **Python**: Ruff (lint + format), Pyright (type checking)
- **TypeScript**: ESLint, Prettier
- Run `make lint && make typecheck` before committing

## Testing

- Backend: `poetry run pytest apps/api/tests -v`
- Frontend: `cd apps/frontend && npm run test`
- All tests must pass before PR submission

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes with tests
4. Run linting and tests
5. Commit with clear messages
6. Push and create a PR against `main`

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

## Architecture

Follow Clean Architecture principles:
- Domain layer has no external dependencies
- Application layer orchestrates use cases
- Infrastructure layer implements interfaces
- Interface layer handles HTTP/WebSocket

## Questions?

Open an issue for discussion before large changes.
