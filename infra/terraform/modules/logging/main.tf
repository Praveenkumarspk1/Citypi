# Terraform Logging Module
# Configures Cloud Logging sinks and metrics

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "log_sink_name" {
  description = "Name of the log sink"
  type        = string
  default     = "concierge-log-sink"
}

variable "log_bucket_name" {
  description = "Cloud Storage bucket for log exports"
  type        = string
  default     = "concierge-logs"
}

# Log export bucket
resource "google_storage_bucket" "logs" {
  name          = "${var.project_id}-${var.log_bucket_name}"
  location      = var.region
  storage_class = "NEARLINE"

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
}

# Log sink to Cloud Storage
resource "google_logging_project_sink" "log_sink" {
  name        = var.log_sink_name
  destination = "storage.googleapis.com/${google_storage_bucket.logs.name}"

  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"concierge-api\""

  unique_writer_identity = true
}

# Log-based metrics
resource "google_logging_metric" "error_count" {
  name   = "concierge-error-count"
  filter = "resource.type=\"cloud_run_revision\" AND severity>=ERROR"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"

    labels {
      key         = "service"
      value_type  = "STRING"
      description = "Service name"
    }
  }

  label_extractors = {
    "service" = "EXTRACT(resource.labels.service_name)"
  }
}

resource "google_logging_metric" "request_latency" {
  name   = "concierge-request-latency"
  filter = "resource.type=\"cloud_run_revision\" AND httpRequest.status!=0"

  metric_descriptor {
    metric_kind = "DISTRIBUTION"
    value_type  = "DISTRIBUTION"

    buckets_options {
      exponential_buckets {
        num_finite_buckets = 64
        growth_factor      = 2
        scale              = 0.001
      }
    }

    unit = "s"
  }
}

output "log_bucket_name" {
  value = google_storage_bucket.logs.name
}

output "log_sink_name" {
  value = google_logging_project_sink.log_sink.name
}
