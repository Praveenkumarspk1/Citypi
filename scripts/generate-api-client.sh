#!/usr/bin/env bash
set -euo pipefail

echo "Generating TypeScript API client from OpenAPI spec..."

cd "$(dirname "$0")/.."

# Generate OpenAPI spec from running API
# openapi-typescript http://localhost:8000/openapi.json --output apps/frontend/src/types/api.ts

echo "API client generation placeholder - requires running API server."
echo "Run: poetry run python -m apps.api.src.main"
echo "Then: openapi-typescript http://localhost:8000/openapi.json --output apps/frontend/src/types/api.ts"
