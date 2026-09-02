# Testing Guide

## Testing Pyramid
```
┌─────────────────────┐
│   E2E Tests (10%)   │  Playwright
│   ────────────────  │
│ Integration (20%)   │  Testcontainers, Real APIs
│   ────────────────  │
│   Contract (10%)    │  Schema validation
│   ────────────────  │
│   Unit (60%)        │  pytest, vitest
└─────────────────────┘
```

## Running Tests

### Backend
```bash
# All tests
poetry run pytest apps/api/tests -v

# Unit tests only
poetry run pytest apps/api/tests/unit -v

# Integration tests
poetry run pytest apps/api/tests/integration -v

# With coverage
poetry run pytest --cov=apps/api/src --cov-report=html
```

### Frontend
```bash
# Unit tests
cd apps/frontend && npm run test

# E2E tests
npm run test:e2e

# With coverage
npm run test -- --coverage
```

## Writing Tests

### Python (pytest)
```python
import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_example(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
```

### TypeScript (vitest)
```typescript
import { test, expect } from 'vitest';

test('example', () => {
  expect(1 + 1).toBe(2);
});
```

## Test Fixtures
Shared fixtures are in `apps/api/tests/conftest.py`:
- `client` - Async HTTP client
- `db_session` - Database session
- `auth_headers` - Authentication headers

## Coverage Target
- Overall: > 80%
- Domain layer: > 90%
- Application layer: > 80%
