# Cloud Run Deployment Guide

## Prerequisites
- GCP project with billing enabled
- Terraform >= 1.5.0
- gcloud CLI authenticated

## Deployment Steps

### 1. Initial Setup
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create Terraform state bucket
gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-tfstate
```

### 2. Provision Infrastructure
```bash
cd infra/terraform
terraform init
terraform workspace new prod
terraform apply -var-file=environments/prod/main.tfvars
```

### 3. Deploy Services
```bash
# Build and push images
gcloud builds submit --config cloudbuild.yaml

# Deploy API
gcloud run deploy concierge-api \
  --image gcr.io/PROJECT_ID/concierge-api:latest \
  --region us-central1 \
  --platform managed

# Deploy Frontend
gcloud run deploy concierge-frontend \
  --image gcr.io/PROJECT_ID/concierge-frontend:latest \
  --region us-central1 \
  --platform managed
```

### 4. Configure Secrets
```bash
echo -n "your-jwt-secret" | gcloud secrets create jwt-secret --data-file=-
echo -n "your-gemini-key" | gcloud secrets create gemini-api-key --data-file=-
```

## Scaling Configuration
- API: min 2, max 100 instances
- Worker: min 1, max 50 instances
- WebSocket: min 2, max 50 instances
- Frontend: min 1, max 20 instances
