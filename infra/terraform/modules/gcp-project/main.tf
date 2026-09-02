# GCP Project Module
# Creates and configures a GCP project with required APIs

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_name" {
  description = "The GCP project name"
  type        = string
}

variable "billing_account" {
  description = "The billing account ID"
  type        = string
}

variable "organization_id" {
  description = "The organization ID"
  type        = string
  default     = null
}

variable "folder_id" {
  description = "The folder ID"
  type        = string
  default     = null
}

variable "apis" {
  description = "List of APIs to enable"
  type        = list(string)
  default = [
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "cloudprofiler.googleapis.com",
    "clouddebugger.googleapis.com",
    "compute.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "dns.googleapis.com",
    "certificatemanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
  ]
}

variable "labels" {
  description = "Labels to apply to the project"
  type        = map(string)
  default     = {}
}

# Create the project
resource "google_project" "project" {
  name            = var.project_name
  project_id      = var.project_id
  billing_account = var.billing_account
  org_id          = var.organization_id
  folder_id       = var.folder_id
  labels          = var.labels
}

# Enable APIs
resource "google_project_service" "apis" {
  for_each = toset(var.apis)
  project  = var.project_id
  service  = each.key

  disable_on_destroy = false
}

# Create service account for Cloud Run services
resource "google_service_account" "cloud_run" {
  account_id   = "cloud-run-services"
  display_name = "Cloud Run Services"
  project      = var.project_id
}

# Grant necessary roles to Cloud Run service account
resource "google_project_iam_member" "cloud_run_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/redis.editor",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/artifactregistry.reader",
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

output "project_id" {
  value = google_project.project.project_id
}

output "project_number" {
  value = google_project.project.number
}

output "cloud_run_service_account_email" {
  value = google_service_account.cloud_run.email
}