# Production Environment Configuration

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
  default     = "concierge-prod"
}

variable "project_name" {
  description = "GCP Project Name"
  type        = string
  default     = "AI Smart City Concierge Production"
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
  default     = "prod"
}

# Locals
locals {
  name_prefix = "concierge"
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
  tier = "db-custom-4-15360"
  storage_size_gb = 100
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
  memory_size_gb = 8
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
      rotation_period = "7776000s"  # 90 days
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
    "encryption-key" = {
      description = "Data encryption key"
    }
  }
}

# IAM
module "iam" {
  source = "../../modules/iam"
  
  project_id = var.project_id
  
  service_accounts = {
    "cloud-run-prod" = {
      display_name = "Cloud Run Production Services"
      description  = "Service account for Cloud Run services in production"
      roles = [
        "roles/cloudsql.client",
        "roles/redis.editor",
        "roles/secretmanager.secretAccessor",
        "roles/logging.logWriter",
        "roles/monitoring.metricWriter",
        "roles/artifactregistry.reader",
      ]
    },
    "ci-cd" = {
      display_name = "CI/CD Service Account"
      description  = "Service account for CI/CD pipelines"
      roles = [
        "roles/run.admin",
        "roles/artifactregistry.writer",
        "roles/cloudbuild.builds.editor",
        "roles/iam.serviceAccountUser",
        "roles/secretmanager.secretAccessor",
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
  service_account_email = module.iam.service_account_emails["cloud-run-prod"]
  vpc_connector = null
  min_instances = 2
  max_instances = 200
  cpu = "2000m"
  memory = "2Gi"
  env_vars = {
    ENVIRONMENT = "production"
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
    { secret_name = "encryption-key", env_var = "ENCRYPTION_KEY", version = "latest" },
  ]
  allow_unauthenticated = true
}

module "worker" {
  source = "../../modules/cloud-run"
  
  project_id = var.project_id
  region     = var.region
  service_name = "${local.name_prefix}-worker"
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${local.name_prefix}-docker/worker:latest"
  service_account_email = module.iam.service_account_emails["cloud-run-prod"]
  min_instances = 2
  max_instances = 20
  cpu = "2000m"
  memory = "4Gi"
  env_vars = {
    ENVIRONMENT = "production"
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
  service_account_email = module.iam.service_account_emails["cloud-run-prod"]
  min_instances = 2
  max_instances = 100
  cpu = "2000m"
  memory = "1Gi"
  env_vars = {
    ENVIRONMENT = "production"
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
  service_account_email = module.iam.service_account_emails["cloud-run-prod"]
  min_instances = 2
  max_instances = 20
  cpu = "2000m"
  memory = "1Gi"
  env_vars = {
    ENVIRONMENT = "production"
    VITE_API_URL = "https://${local.name_prefix}-api-${var.region}.run.app"
    VITE_WS_URL = "wss://${local.name_prefix}-websocket-${var.region}.run.app"
  }
  allow_unauthenticated = true
}

# Load Balancer (Production)
module "load_balancer" {
  source = "../../modules/load-balancer"
  
  project_id = var.project_id
  region     = var.region
  name = "${local.name_prefix}-lb"
  
  ssl_certificates = [
    {
      name    = "prod-cert"
      domains = ["api.concierge.example.com", "app.concierge.example.com", "ws.concierge.example.com"]
    }
  ]
  
  backend_services = [
    {
      name = "api"
      backends = [
        {
          group = module.api.service_name
          balancing_mode = "RATE"
          capacity_scaler = 1.0
        }
      ]
      health_check = module.api.service_name
      cdn_enabled = true
    },
    {
      name = "websocket"
      backends = [
        {
          group = module.websocket.service_name
          balancing_mode = "UTILIZATION"
          capacity_scaler = 1.0
        }
      ]
      health_check = module.websocket.service_name
      cdn_enabled = false
    }
  ]
  
  url_map_rules = [
    {
      hosts = ["api.concierge.example.com"]
      paths = ["/*"]
      service = "api"
    },
    {
      hosts = ["ws.concierge.example.com"]
      paths = ["/*"]
      service = "websocket"
    }
  ]
  
  enable_cdn = true
  enable_quic = true
  enable_http2 = true
}

# CDN
module "cdn" {
  source = "../../modules/cdn"
  
  project_id = var.project_id
  backend_service_name = module.load_balancer.backend_service_ids["api"]
  
  cache_key_policy = {
    include_protocol = true
    include_host = true
    include_query_string = true
    query_string_whitelist = ["v", "format"]
    query_string_blacklist = ["token", "key", "secret"]
  }
  
  cache_mode = "USE_ORIGIN_HEADERS"
  default_ttl_sec = 3600
  max_ttl_sec = 86400
  negative_caching = true
  serve_stale_on_error = true
}

# DNS
module "dns" {
  source = "../../modules/dns"
  
  project_id = var.project_id
  zone_name = "concierge-prod"
  dns_name = "concierge.example.com."
  visibility = "public"
  
  records = [
    {
      name = "api.concierge.example.com."
      type = "A"
      ttl = 300
      rrdatas = [module.load_balancer.ipv4_address]
    },
    {
      name = "api.concierge.example.com."
      type = "AAAA"
      ttl = 300
      rrdatas = [module.load_balancer.ipv6_address]
    },
    {
      name = "ws.concierge.example.com."
      type = "A"
      ttl = 300
      rrdatas = [module.load_balancer.ipv4_address]
    },
    {
      name = "ws.concierge.example.com."
      type = "AAAA"
      ttl = 300
      rrdatas = [module.load_balancer.ipv6_address]
    },
    {
      name = "app.concierge.example.com."
      type = "A"
      ttl = 300
      rrdatas = [module.load_balancer.ipv4_address]
    },
    {
      name = "app.concierge.example.com."
      type = "AAAA"
      ttl = 300
      rrdatas = [module.load_balancer.ipv6_address]
    }
  ]
}

# Monitoring
module "monitoring" {
  source = "../../modules/monitoring"
  
  project_id = var.project_id
  region     = var.region
  
  notification_channels = [
    {
      type        = "email"
      display_name = "Production Alerts"
      labels = {
        email_address = "prod-alerts@example.com"
      }
      enabled = true
    },
    {
      type        = "pagerduty"
      display_name = "Production PagerDuty"
      labels = {
        service_key = "your-pagerduty-key"
      }
      enabled = true
    },
    {
      type        = "slack"
      display_name = "Production Slack"
      labels = {
        channel_name = "#prod-alerts"
      }
      enabled = true
    }
  ]
  
  alert_policies = [
    {
      display_name = "High Error Rate"
      conditions = [
        {
          display_name = "Error rate > 0.1%"
          condition_threshold = {
            filter = "metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class=\"5xx\""
            comparison = "COMPARISON_GT"
            threshold_value = 0.001
            duration = "60s"
          }
        }
      ]
      notification_channels = ["Production Alerts", "Production PagerDuty", "Production Slack"]
      enabled = true
    },
    {
      display_name = "High Latency"
      conditions = [
        {
          display_name = "P99 latency > 1s"
          condition_threshold = {
            filter = "metric.type=\"run.googleapis.com/request_latencies\""
            comparison = "COMPARISON_GT"
            threshold_value = 1.0
            duration = "300s"
          }
        }
      ]
      notification_channels = ["Production Alerts", "Production Slack"]
      enabled = true
    },
    {
      display_name = "Service Down"
      conditions = [
        {
          display_name = "No healthy instances"
          condition_threshold = {
            filter = "metric.type=\"run.googleapis.com/container/billable_container_instance_count\""
            comparison = "COMPARISON_LT"
            threshold_value = 1
            duration = "60s"
          }
        }
      ]
      notification_channels = ["Production Alerts", "Production PagerDuty"]
      enabled = true
    }
  ]
  
  uptime_checks = [
    {
      display_name = "API Health Check"
      hostname = "api.concierge.example.com"
      path = "/health/ready"
      port = 443
      check_interval = 60
      timeout = 10
      content_matchers = ["ready"]
      regions = ["USA", "EUROPE", "ASIA_PACIFIC"]
    },
    {
      display_name = "WebSocket Health Check"
      hostname = "ws.concierge.example.com"
      path = "/health/ready"
      port = 443
      check_interval = 60
      timeout = 10
      content_matchers = ["ready"]
      regions = ["USA", "EUROPE", "ASIA_PACIFIC"]
    },
    {
      display_name = "Frontend Health Check"
      hostname = "app.concierge.example.com"
      path = "/"
      port = 443
      check_interval = 60
      timeout = 10
      content_matchers = ["Smart City Concierge"]
      regions = ["USA", "EUROPE", "ASIA_PACIFIC"]
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

output "load_balancer_ipv4" {
  value = module.load_balancer.ipv4_address
}

output "load_balancer_ipv6" {
  value = module.load_balancer.ipv6_address
}