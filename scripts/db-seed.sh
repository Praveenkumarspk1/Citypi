#!/usr/bin/env bash
set -euo pipefail

echo "Seeding database with sample data..."

cd "$(dirname "$0")/.."

poetry run python -m apps.api.src.infrastructure.seeding.seed

echo "Seeding complete."
