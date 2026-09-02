# Terraform Cloud Storage Module
# Creates GCS buckets for media and backups

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "media_bucket_name" {
  description = "Name of the media storage bucket"
  type        = string
  default     = "concierge-media"
}

variable "backup_bucket_name" {
  description = "Name of the backup storage bucket"
  type        = string
  default     = "concierge-backups"
}

# Media storage bucket
resource "google_storage_bucket" "media" {
  name          = "${var.project_id}-${var.media_bucket_name}"
  location      = var.region
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

# Backup storage bucket
resource "google_storage_bucket" "backups" {
  name          = "${var.project_id}-${var.backup_bucket_name}"
  location      = var.region
  storage_class = "NEARLINE"

  versioning {
    enabled = true
  }
}

# IAM for media bucket
resource "google_storage_bucket_iam_member" "media_reader" {
  bucket = google_storage_bucket.media.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:cloud-run@${var.project_id}.iam.gserviceaccount.com"
}

output "media_bucket_url" {
  value = google_storage_bucket.media.url
}

output "backup_bucket_url" {
  value = google_storage_bucket.backups.url
}
