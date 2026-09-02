#!/usr/bin/env bash
set -euo pipefail

echo "Running database migrations..."

cd "$(dirname "$0")/.."

poetry run alembic upgrade head

echo "Migrations complete."
