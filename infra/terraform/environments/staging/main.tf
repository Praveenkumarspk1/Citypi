# Staging Environment Configuration

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "concierge-staging"
}

variable "project_name" {
  description = "GCP Project Name"
  type        = string
  default     = "AI Smart City Concierge Staging"
}

variable "billing_account" {
  description = "Billing Account ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

# Locals
locals {
  name_prefix = "concierge-${var.environment}"
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    project     = "concierge"
  }
}

# GCP Project
module "gcp_project" {
  source = "../../modules/gcp-project"
  
  project_id      = var.project_id
  project_name    = var.project_name
  billing_account = var.billing_account
  labels          = local.labels
}

# VPC
module "vpc" {
  source = "../../modules/vpc"
  
  project_id = var.project_id
  region     = var.region
  network_name = "${local.name_prefix}-vpc"
}

# Artifact Registry
module "artifact_registry" {
  source = "../../modules/artifact-registry"
  
  project_id = var.project_id
  region     = var.region
  repository_id = "${local.name_prefix}-docker"
}

# Cloud SQL
module "cloud_sql" {
  source = "../../modules/cloud-sql"
  
  project_id = var.project_id
  region     = var.region
  instance_name = "${local.name_prefix}-db"
  tier = "db-custom-2-7680"
  storage_size_gb = 50
  availability_type = "REGIONAL"
  private_network = module.vpc.network_name
  labels = local.labels
}

# Redis
module "redis" {
  source = "../../modules/redis"
  
  project_id = var.project_id
  region     = var.region
  instance_name = "${local.name_prefix}-redis"
  tier = "STANDARD_HA"
  memory_size_gb = 4
  authorized_network = module.vpc.network_name
  auth_enabled = true
  labels = local.labels
}

# Secret Manager
module "secrets" {
  source = "../../modules/secret-manager"
  
  project_id = var.project_id
  
  secrets = {
    "jwt-secret" = {
      description = "JWT signing secret"
    }
    "gemini-api-key" = {
      description = "Gemini API key"
    }
    "openweather-api-key" = {
      description = "OpenWeather API key"
    }
    "google-maps-api-key" = {
      description = "Google Maps API key"
    }
    "postgres-password" = {
      description = "PostgreSQL password"
    }
  }
}

# IAM
module "iam" {
  source = "../../modules/iam"
  
  project_id = var.project_id
  
  service_accounts = {
    "cloud-run-staging" = {
      display_name = "Cloud Run Staging Services"
      description  = "Service account for Cloud Run services in staging"
      roles = [
        "roles/cloudsql.client",
        "roles/redis.editor",
        "roles/secretmanager.secretAccessor",
        "roles/logging.logWriter",
        "roles/monitoring.metricWriter",
        "roles/artifactregistry.reader",
      ]
    }
  }
}

# Cloud Run Services
module "api" {
  source = "../../modules/cloud-run"
  
  project_id = var.project_id
  region     = var.region
  service_name = "${local.name_prefix}-api"
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${local.name_prefix}-docker/api:latest"
  service_account_email = module.iam.service_account_emails["cloud-run-staging"]
  vpc_connector = null
  min_instances = 1
  max_instances = 50
  cpu = "2000m"
  memory = "1Gi"
  env_vars = {
    ENVIRONMENT = "staging"
    DATABASE_URL = "postgresql+asyncpg://concierge:@${module.cloud_sql.instance_ip}:5432/concierge"
    REDIS_URL = "redis://:${module.redis.auth_string_secret}@${module.redis.host}:6379/0"
    CHROMADB_HOST = "localhost"
    CHROMADB_PORT = "8000"
  }
  secrets = [
    { secret_name = "jwt-secret", env_var = "JWT_SECRET_KEY", version = "latest" },
    { secret_name = "gemini-api-key", env_var = "GEMINI_API_KEY", version = "latest" },
    { secret_name = "openweather-api-key", env_var = "OPENWEATHER_API_KEY", version = "latest" },
    { secret_name = "google-maps-api-key", env_var = "GOOGLE_MAPS_API_KEY", version = "latest" },
  ]
  allow_unauthenticated = true
}

module "worker" {
  source = "../../modules/cloud-run"
  
  project_id = var.project_id
  region     = var.region
  service_name = "${local.name_prefix}-worker"
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${local.name_prefix}-docker/worker:latest"
  service_account_email = module.iam.service_account_emails["cloud-run-staging"]
  min_instances = 1
  max_instances = 10
  cpu = "2000m"
  memory = "2Gi"
  env_vars = {
    ENVIRONMENT = "staging"
    DATABASE_URL = "postgresql+asyncpg://concierge:@${module.cloud_sql.instance_ip}:5432/concierge"
    REDIS_URL = "redis://:${module.redis.auth_string_secret}@${module.redis.host}:6379/0"
    CHROMADB_HOST = "localhost"
    CHROMADB_PORT = "8000"
  }
  allow_unauthenticated = false
}

module "websocket" {
  source = "../../modules/cloud-run"
  
  project_id = var.project_id
  region     = var.region
  service_name = "${local.name_prefix}-websocket"
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${local.name_prefix}-docker/websocket:latest"
  service_account_email = module.iam.service_account_emails["cloud-run-staging"]
  min_instances = 1
  max_instances = 20
  cpu = "1000m"
  memory = "512Mi"
  env_vars = {
    ENVIRONMENT = "staging"
    REDIS_URL = "redis://:${module.redis.auth_string_secret}@${module.redis.host}:6379/0"
  }
  secrets = [
    { secret_name = "jwt-secret", env_var = "JWT_SECRET_KEY", version = "latest" },
  ]
  allow_unauthenticated = true
}

module "frontend" {
  source = "../../modules/cloud-run"
  
  project_id = var.project_id
  region     = var.region
  service_name = "${local.name_prefix}-frontend"
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${local.name_prefix}-docker/frontend:latest"
  service_account_email = module.iam.service_account_emails["cloud-run-staging"]
  min_instances = 1
  max_instances = 10
  cpu = "1000m"
  memory = "512Mi"
  env_vars = {
    ENVIRONMENT = "staging"
    VITE_API_URL = "https://${local.name_prefix}-api-${var.region}.run.app"
    VITE_WS_URL = "wss://${local.name_prefix}-websocket-${var.region}.run.app"
  }
  allow_unauthenticated = true
}

# Monitoring
module "monitoring" {
  source = "../../modules/monitoring"
  
  project_id = var.project_id
  region     = var.region
  
  notification_channels = [
    {
      type        = "email"
      display_name = "Staging Alerts"
      labels = {
        email_address = "staging-alerts@example.com"
      }
      enabled = true
    },
    {
      type        = "slack"
      display_name = "Staging Slack"
      labels = {
        channel_name = "#staging-alerts"
      }
      enabled = true
    }
  ]
  
  alert_policies = [
    {
      display_name = "High Error Rate"
      conditions = [
        {
          display_name = "Error rate > 1%"
          condition_threshold = {
            filter = "metric.type=\"run.googleapis.com/container/billable_container_instance_count\""
            comparison = "COMPARISON_GT"
            threshold_value = 1
            duration = "300s"
          }
        }
      ]
      notification_channels = ["Staging Alerts", "Staging Slack"]
      enabled = true
    },
    {
      display_name = "High Latency"
      conditions = [
        {
          display_name = "P95 latency > 500ms"
          condition_threshold = {
            filter = "metric.type=\"run.googleapis.com/request_latencies\""
            comparison = "COMPARISON_GT"
            threshold_value = 0.5
            duration = "300s"
          }
        }
      ]
      notification_channels = ["Staging Alerts"]
      enabled = true
    }
  ]
}

output "api_url" {
  value = module.api.service_url
}

output "websocket_url" {
  value = module.websocket.service_url
}

output "frontend_url" {
  value = module.frontend.service_url
}