#!/usr/bin/env bash
set -euo pipefail

echo "Running security scans..."

cd "$(dirname "$0")/.."

echo "=== Bandit (Python security) ==="
pip install bandit --quiet
bandit -r apps/api/src -f json -o bandit-results.json || true
echo "Bandit results: bandit-results.json"

echo "=== npm audit ==="
cd apps/frontend
npm audit --audit-level=high || true
cd ../..

echo "=== Trivy (container scan) ==="
if command -v trivy &> /dev/null; then
    trivy fs --format json --output trivy-results.json .
    echo "Trivy results: trivy-results.json"
else
    echo "Trivy not found. Install from https://trivy.dev/"
fi

echo "Security scan complete."
