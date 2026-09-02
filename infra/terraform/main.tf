# Terraform Root Configuration
# Entry point for all infrastructure provisioning

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "ai-smart-city-concierge-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# VPC Module
module "vpc" {
  source     = "./modules/vpc"
  project_id = var.project_id
  region     = var.region
}

# GCP Project Setup
module "gcp_project" {
  source     = "./modules/gcp-project"
  project_id = var.project_id
}

# Cloud SQL
module "cloud_sql" {
  source     = "./modules/cloud-sql"
  project_id = var.project_id
  region     = var.region
}

# Redis
module "redis" {
  source     = "./modules/redis"
  project_id = var.project_id
  region     = var.region
}

# Cloud Run Services
module "cloud_run" {
  source     = "./modules/cloud-run"
  project_id = var.project_id
  region     = var.region
}

# Qdrant
module "qdrant" {
  source     = "./modules/qdrant"
  project_id = var.project_id
  region     = var.region
}

# Cloud Storage
module "cloud_storage" {
  source     = "./modules/cloud-storage"
  project_id = var.project_id
  region     = var.region
}

# Pub/Sub
module "pubsub" {
  source     = "./modules/pubsub"
  project_id = var.project_id
  region     = var.region
}

# Secrets
module "secrets" {
  source     = "./modules/secret-manager"
  project_id = var.project_id
}

# IAM
module "iam" {
  source     = "./modules/iam"
  project_id = var.project_id
}

# Monitoring
module "monitoring" {
  source     = "./modules/monitoring"
  project_id = var.project_id
  region     = var.region
}

# Logging
module "logging" {
  source     = "./modules/logging"
  project_id = var.project_id
  region     = var.region
}

# Service Mesh
module "service_mesh" {
  source     = "./modules/service-mesh"
  project_id = var.project_id
  region     = var.region
}

# CDN
module "cdn" {
  source     = "./modules/cdn"
  project_id = var.project_id
}

# DNS
module "dns" {
  source     = "./modules/dns"
  project_id = var.project_id
}

# Artifact Registry
module "artifact_registry" {
  source     = "./modules/artifact-registry"
  project_id = var.project_id
  region     = var.region
}

# Load Balancer
module "load_balancer" {
  source     = "./modules/load-balancer"
  project_id = var.project_id
  region     = var.region
}

output "api_url" {
  value = module.cloud_run.api_url
}

output "frontend_url" {
  value = module.cloud_run.frontend_url
}
