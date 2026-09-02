# Terraform Qdrant Module
# Deploys Qdrant vector database on GKE

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "ai-smart-city-concierge"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "concierge-cluster"
}

variable "qdrant_namespace" {
  description = "Kubernetes namespace for Qdrant"
  type        = string
  default     = "qdrant"
}

variable "qdrant_replicas" {
  description = "Number of Qdrant replicas"
  type        = number
  default     = 3
}

variable "qdrant_storage_gb" {
  description = "Storage per Qdrant node in GB"
  type        = number
  default     = 50
}

# GKE Node Pool for Qdrant
resource "google_container_node_pool" "qdrant" {
  name     = "qdrant-node-pool"
  location = var.region
  cluster  = var.cluster_name

  initial_node_count = var.qdrant_replicas

  node_config {
    machine_type = "e2-standard-4"
    disk_size_gb = var.qdrant_storage_gb + 50

    labels = {
      component = "qdrant"
    }

    tags = ["qdrant"]
  }

  autoscaling {
    min_node_count = 3
    max_node_count = 6
  }
}

# Cloud Storage backup bucket for Qdrant snapshots
resource "google_storage_bucket" "qdrant_backups" {
  name          = "${var.project_id}-qdrant-backups"
  location      = var.region
  storage_class = "STANDARD"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

output "node_pool_name" {
  value = google_container_node_pool.qdrant.name
}

output "backup_bucket" {
  value = google_storage_bucket.qdrant_backups.name
}
