# Artifact Registry Module
# Creates Artifact Registry repositories for Docker images

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "repository_id" {
  description = "The repository ID"
  type        = string
  default     = "concierge"
}

variable "repository_name" {
  description = "The repository name"
  type        = string
  default     = "concierge-docker"
}

variable "format" {
  description = "Repository format (DOCKER, MAVEN, NPM, PYTHON)"
  type        = string
  default     = "DOCKER"
}

variable "description" {
  description = "Repository description"
  type        = string
  default     = "AI Smart City Concierge Docker images"
}

variable "labels" {
  description = "Labels for the repository"
  type        = map(string)
  default     = {}
}

variable "cleanup_policies" {
  description = "Cleanup policies for old images"
  type = list(object({
    action = string
    most_recent_versions = number
    tag_state = string
    older_than_days = number
    keep_count = number
  }))
  default = [
    {
      action = "DELETE"
      most_recent_versions = 10
      tag_state = "ANY"
      older_than_days = 30
      keep_count = 0
    },
    {
      action = "DELETE"
      most_recent_versions = 5
      tag_state = "UNTAGGED"
      older_than_days = 7
      keep_count = 0
    }
  ]
}

variable "vulnerability_scanning" {
  description = "Enable vulnerability scanning"
  type        = bool
  default     = true
}

variable "immutable_tags" {
  description = "Make tags immutable"
  type        = bool
  default     = true
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "main" {
  location      = var.region
  project       = var.project_id
  repository_id = var.repository_id
  format        = var.format
  description   = var.description
  labels        = var.labels

  cleanup_policies = var.cleanup_policies

  vulnerability_scanning_config {
    enable = var.vulnerability_scanning
  }

  immutable_tags = var.immutable_tags
}

# IAM for Cloud Build to push images
resource "google_artifact_registry_repository_iam_member" "cloud_build_writer" {
  project      = var.project_id
  location     = var.region
  repository   = google_artifact_registry_repository.main.name
  role         = "roles/artifactregistry.writer"
  member       = "serviceAccount:$(gcloud projects describe ${var.project_id} --format='value(projectNumber)')@cloudbuild.gserviceaccount.com"
}

# IAM for Cloud Run to pull images
resource "google_artifact_registry_repository_iam_member" "cloud_run_reader" {
  project      = var.project_id
  location     = var.region
  repository   = google_artifact_registry_repository.main.name
  role         = "roles/artifactregistry.reader"
  member       = "serviceAccount:$(gcloud projects describe ${var.project_id} --format='value(projectNumber)')-compute@developer.gserviceaccount.com"
}

output "repository_name" {
  value = google_artifact_registry_repository.main.name
}

output "repository_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_id}"
}