# Secrets Management

## Overview
Secrets are managed via Google Cloud Secret Manager for production and `.env` files for local development.

## Required Secrets

| Secret | Description | How to Obtain |
|--------|-------------|---------------|
| `jwt-secret` | JWT signing key | `openssl rand -hex 32` |
| `gemini-api-key` | Google AI Studio API key | Google AI Studio (free) |
| `database-password` | PostgreSQL password | Generate securely |
| `redis-password` | Redis password | Generate securely |
| `firebase-service-account` | Firebase Admin SDK | Firebase Console |

## Local Development
```bash
# Copy example env
cp .env.example .env

# Edit with your values
# GEMINI_API_KEY=your-key-here
# JWT_SECRET_KEY=generated-secret
```

## Production (Secret Manager)
```bash
# Create secrets
echo -n "value" | gcloud secrets create SECRET_NAME --data-file=-

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:cloud-run@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Secret Rotation
- JWT secret: Every 180 days
- API keys: Every 30-90 days
- Database passwords: Every 90 days

## Architecture
- Secrets are injected at runtime via environment variables
- No secrets are committed to git
- `.env.example` documents required variables without values
