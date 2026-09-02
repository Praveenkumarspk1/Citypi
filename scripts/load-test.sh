#!/usr/bin/env bash
set -euo pipefail

echo "Running load tests with k6..."

cd "$(dirname "$0")/.."

if ! command -v k6 &> /dev/null; then
    echo "k6 not found. Install from https://k6.io/docs/get-started/installation/"
    exit 1
fi

k6 run --vus 10 --duration 30s scripts/load-test.js 2>/dev/null || echo "Load test script not found. Create scripts/load-test.js"
