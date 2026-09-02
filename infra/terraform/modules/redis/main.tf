# Redis Module
# Creates a Redis instance (Memorystore)

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "instance_name" {
  description = "The Redis instance name"
  type        = string
  default     = "concierge-redis"
}

variable "redis_version" {
  description = "Redis version"
  type        = string
  default     = "REDIS_7_0"
}

variable "tier" {
  description = "Redis tier (BASIC, STANDARD_HA)"
  type        = string
  default     = "STANDARD_HA"
}

variable "memory_size_gb" {
  description = "Memory size in GB"
  type        = number
  default     = 4
}

variable "authorized_network" {
  description = "VPC network for the Redis instance"
  type        = string
}

variable "redis_configs" {
  description = "Redis configuration parameters"
  type        = map(string)
  default = {
    "maxmemory-policy" = "allkeys-lru"
    "timeout"          = "0"
    "tcp-keepalive"    = "60"
  }
}

variable "maintenance_window" {
  description = "Maintenance window"
  type = object({
    day  = number
    hour = number
  })
  default = {
    day  = 1
    hour = 4
  }
}

variable "labels" {
  description = "Labels for the instance"
  type        = map(string)
  default     = {}
}

variable "transit_encryption_mode" {
  description = "Transit encryption mode (SERVER_AUTHENTICATION, DISABLED)"
  type        = string
  default     = "SERVER_AUTHENTICATION"
}

variable "auth_enabled" {
  description = "Enable authentication"
  type        = bool
  default     = true
}

variable "persistence_enabled" {
  description = "Enable RDB persistence"
  type        = bool
  default     = false
}

variable "persistence_rdb_snapshot_period" {
  description = "RDB snapshot period (ONE_HOUR, SIX_HOURS, TWELVE_HOURS, TWENTY_FOUR_HOURS)"
  type        = string
  default     = "SIX_HOURS"
}

# Redis Instance
resource "google_redis_instance" "main" {
  name                = var.instance_name
  project             = var.project_id
  location_id         = var.region
  redis_version       = var.redis_version
  tier                = var.tier
  memory_size_gb      = var.memory_size_gb
  authorized_network  = var.authorized_network
  redis_configs       = var.redis_configs
  transit_encryption_mode = var.transit_encryption_mode
  auth_enabled        = var.auth_enabled
  persistence_enabled = var.persistence_enabled

  dynamic "persistence_config" {
    for_each = var.persistence_enabled ? [1] : []
    content {
      rdb_snapshot_period = var.persistence_rdb_snapshot_period
    }
  }

  maintenance_policy {
    window {
      day   = var.maintenance_window.day
      hour  = var.maintenance_window.hour
    }
  }

  labels = var.labels
}

# Store auth string in Secret Manager (if auth enabled)
resource "google_secret_manager_secret" "redis_auth" {
  count       = var.auth_enabled ? 1 : 0
  secret_id   = "${var.instance_name}-auth-string"
  project     = var.project_id
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "redis_auth" {
  count       = var.auth_enabled ? 1 : 0
  secret      = google_secret_manager_secret.redis_auth[0].id
  secret_data = google_redis_instance.main.auth_string
}

output "instance_name" {
  value = google_redis_instance.main.name
}

output "host" {
  value = google_redis_instance.main.host
}

output "port" {
  value = google_redis_instance.main.port
}

output "auth_string_secret" {
  value = var.auth_enabled ? google_secret_manager_secret.redis_auth[0].secret_id : ""
}