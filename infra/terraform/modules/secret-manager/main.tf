# Secret Manager Module
# Manages secrets in Secret Manager

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "secrets" {
  description = "Map of secrets to create"
  type = map(object({
    description    = optional(string, "")
    labels         = optional(map(string), {})
    replication    = optional(string, "automatic")
    rotation_period = optional(string, null)
    next_rotation_time = optional(string, null)
  }))
  default = {}
}

variable "secret_versions" {
  description = "Map of secret versions to create"
  type = map(object({
    secret_id = string
    data      = string
  }))
  default = {}
}

# Create secrets
resource "google_secret_manager_secret" "secrets" {
  for_each = var.secrets

  secret_id   = each.key
  project     = var.project_id
  replication {
    automatic = true
  }
  labels      = each.value.labels

  dynamic "rotation" {
    for_each = each.value.rotation_period != null ? [1] : []
    content {
      next_rotation_time = each.value.next_rotation_time
      rotation_period    = each.value.rotation_period
    }
  }
}

# Create secret versions
resource "google_secret_manager_secret_version" "versions" {
  for_each = var.secret_versions

  secret      = google_secret_manager_secret.secrets[each.value.secret_id].id
  secret_data = each.value.data
}

output "secret_names" {
  value = { for k, v in google_secret_manager_secret.secrets : k => v.secret_id }
}

output "secret_versions" {
  value = { for k, v in google_secret_manager_secret_version.versions : k => v.secret }
}