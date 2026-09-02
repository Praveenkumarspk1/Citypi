#!/usr/bin/env bash
set -euo pipefail

echo "Deploying application..."

cd "$(dirname "$0")/.."

ENVIRONMENT="${1:-staging}"

case "$ENVIRONMENT" in
    staging)
        echo "Deploying to staging..."
        docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml pull
        docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d
        ;;
    production)
        echo "Deploying to production..."
        docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml pull
        docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT"
        echo "Usage: $0 [staging|production]"
        exit 1
        ;;
esac

echo "Deployment complete."
