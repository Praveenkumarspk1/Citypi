# Cloud Run Module
# Deploys a Cloud Run service

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "service_name" {
  description = "The Cloud Run service name"
  type        = string
}

variable "image" {
  description = "Container image URL"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for the service"
  type        = string
}

variable "vpc_connector" {
  description = "VPC connector for private networking"
  type        = string
  default     = null
}

variable "vpc_egress" {
  description = "VPC egress setting (all-traffic, private-ranges-only)"
  type        = string
  default     = "private-ranges-only"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 100
}

variable "cpu" {
  description = "CPU limit (e.g., 1000m, 2000m)"
  type        = string
  default     = "1000m"
}

variable "memory" {
  description = "Memory limit (e.g., 512Mi, 1Gi, 2Gi)"
  type        = string
  default     = "512Mi"
}

variable "concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 80
}

variable "timeout" {
  description = "Request timeout in seconds"
  type        = number
  default     = 300
}

variable "env_vars" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secrets to mount as environment variables"
  type = list(object({
    secret_name = string
    env_var     = string
    version     = string
  }))
  default = []
}

variable "labels" {
  description = "Labels for the service"
  type        = map(string)
  default     = {}
}

variable "annotations" {
  description = "Annotations for the service"
  type        = map(string)
  default     = {}
}

variable "ingress" {
  description = "Ingress setting (all, internal, internal-and-cloud-load-balancing)"
  type        = string
  default     = "all"
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated invocations"
  type        = bool
  default     = true
}

variable "execution_environment" {
  description = "Execution environment (gen1, gen2)"
  type        = string
  default     = "gen2"
}

variable "health_check" {
  description = "Health check configuration"
  type = object({
    path                 = string
    interval_seconds     = number
    timeout_seconds      = number
    failure_threshold    = number
    startup_period_seconds = number
  })
  default = {
    path                 = "/health/live"
    interval_seconds     = 30
    timeout_seconds      = 10
    failure_threshold    = 3
    startup_period_seconds = 40
  }
}

variable "revision_suffix" {
  description = "Revision suffix for the service"
  type        = string
  default     = null
}

variable "depends_on" {
  description = "Resources to depend on"
  type        = list(any)
  default     = []
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "service" {
  name        = var.service_name
  project     = var.project_id
  location    = var.region
  deletion_protection = false

  template {
    service_account = var.service_account_email
    timeout         = "${var.timeout}s"
    concurrency     = var.concurrency
    max_instance_count = var.max_instances
    min_instance_count = var.min_instances
    execution_environment = var.execution_environment

    vpc_access {
      connector          = var.vpc_connector
      egress             = var.vpc_egress
    }

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.image
      cpu_limit   = var.cpu
      memory_limit = var.memory
      startup_cpu_boost = true

      env = [
        for key, value in var.env_vars : {
          name  = key
          value = value
        }
      ]

      env {
        name = "PORT"
        value = "8080"
      }

      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.value
          value_source {
            secret_key_ref {
              secret   = env.secret_name
              version  = env.version
            }
          }
        }
      }

      ports {
        container_port = 8080
      }

      health_check {
        http_get {
          path = var.health_check.path
          port = 8080
        }
        initial_delay_seconds = var.health_check.startup_period_seconds
        period_seconds = var.health_check.interval_seconds
        timeout_seconds = var.health_check.timeout_seconds
        failure_threshold = var.health_check.failure_threshold
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }
    }

    labels = var.labels
    annotations = var.annotations
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  ingress = var.ingress

  depends_on = var.depends_on
}

# IAM Binding for unauthenticated access
resource "google_cloud_run_v2_service_iam_member" "unauthenticated" {
  count = var.allow_unauthenticated ? 1 : 0
  project = var.project_id
  location = var.region
  service = google_cloud_run_v2_service.service.name
  role = "roles/run.invoker"
  member = "allUsers"
}

output "service_name" {
  value = google_cloud_run_v2_service.service.name
}

output "service_url" {
  value = google_cloud_run_v2_service.service.uri
}

output "service_id" {
  value = google_cloud_run_v2_service.service.id
}