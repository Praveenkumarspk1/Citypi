# Cloud SQL Module
# Creates a PostgreSQL instance with PostGIS

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "instance_name" {
  description = "The Cloud SQL instance name"
  type        = string
  default     = "concierge-db"
}

variable "database_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "POSTGRES_16"
}

variable "tier" {
  description = "Machine tier (e.g., db-custom-2-7680, db-f1-micro)"
  type        = string
  default     = "db-custom-2-7680"
}

variable "storage_type" {
  description = "Storage type (SSD or HDD)"
  type        = string
  default     = "PD_SSD"
}

variable "storage_size_gb" {
  description = "Storage size in GB"
  type        = number
  default     = 50
}

variable "storage_auto_increase" {
  description = "Enable storage auto-increase"
  type        = bool
  default     = true
}

variable "storage_auto_increase_limit_gb" {
  description = "Maximum storage size in GB"
  type        = number
  default     = 500
}

variable "availability_type" {
  description = "Availability type (REGIONAL or ZONAL)"
  type        = string
  default     = "REGIONAL"
}

variable "authorized_networks" {
  description = "List of authorized networks"
  type        = list(string)
  default     = []
}

variable "ipv4_enabled" {
  description = "Enable public IP"
  type        = bool
  default     = false
}

variable "private_network" {
  description = "VPC network for private IP"
  type        = string
}

variable "backup_enabled" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_start_time" {
  description = "Backup window start time (HH:MM)"
  type        = string
  default     = "03:00"
}

variable "backup_location" {
  description = "Backup location"
  type        = string
  default     = "us"
}

variable "point_in_time_recovery" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = true
}

variable "maintenance_window_day" {
  description = "Maintenance window day (1-7, Monday=1)"
  type        = number
  default     = 1
}

variable "maintenance_window_hour" {
  description = "Maintenance window hour (0-23)"
  type        = number
  default     = 4
}

variable "maintenance_update_track" {
  description = "Maintenance update track (canary, stable)"
  type        = string
  default     = "stable"
}

variable "database_flags" {
  description = "Database flags"
  type        = map(string)
  default = {
    "cloudsql.enable_postgis" = "on"
    "max_connections"         = "200"
    "shared_buffers"          = "256MB"
    "work_mem"                = "4MB"
    "maintenance_work_mem"    = "64MB"
    "effective_cache_size"    = "1GB"
    "random_page_cost"        = "1.1"
    "log_statement"           = "ddl"
    "log_min_duration_statement" = "1000"
  }
}

variable "labels" {
  description = "Labels for the instance"
  type        = map(string)
  default     = {}
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "insights_config" {
  description = "Query insights configuration"
  type = object({
    enabled             = bool
    record_client_address = bool
    record_application_name = bool
  })
  default = {
    enabled               = true
    record_client_address = true
    record_application_name = true
  }
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = var.instance_name
  project          = var.project_id
  region           = var.region
  database_version = var.database_version

  settings {
    tier                    = var.tier
    availability_type       = var.availability_type
    storage_type            = var.storage_type
    storage_auto_increase   = var.storage_auto_increase
    storage_auto_increase_limit = var.storage_auto_increase_limit_gb
    deletion_protection     = var.deletion_protection

    ip_configuration {
      ipv4_enabled     = var.ipv4_enabled
      private_network  = var.private_network
      authorized_networks = [
        for network in var.authorized_networks : {
          value = network
        }
      ]
      require_ssl = true
    }

    backup_configuration {
      enabled            = var.backup_enabled
      start_time         = var.backup_start_time
      location           = var.backup_location
      point_in_time_recovery_enabled = var.point_in_time_recovery
      transaction_log_retention_days = 7
    }

    maintenance_window {
      day  = var.maintenance_window_day
      hour = var.maintenance_window_hour
      update_track = var.maintenance_update_track
    }

    database_flags = [
      for key, value in var.database_flags : {
        name  = key
        value = value
      }
    ]

    insights_config {
      query_insights_enabled           = var.insights_config.enabled
      record_client_address_enabled    = var.insights_config.record_client_address
      record_application_name_enabled  = var.insights_config.record_application_name
    }

    user_labels = var.labels
  }

  deletion_protection = var.deletion_protection
}

# Default Database
resource "google_sql_database" "default" {
  name     = "concierge"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
  charset  = "UTF8"
  collation = "en_US.UTF8"
}

# Database Users
resource "google_sql_user" "postgres" {
  name     = "postgres"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
  password = random_password.postgres_password.result
}

resource "google_sql_user" "app_user" {
  name     = "concierge"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
  password = random_password.app_password.result
}

# SSL Certs
resource "google_sql_ssl_cert" "client_cert" {
  instance = google_sql_database_instance.main.name
  project  = var.project_id
  common_name = "concierge-client"
}

# Random passwords
resource "random_password" "postgres_password" {
  length  = 32
  special = true
}

resource "random_password" "app_password" {
  length  = 32
  special = true
}

# Store passwords in Secret Manager
resource "google_secret_manager_secret" "postgres_password" {
  secret_id = "${var.instance_name}-postgres-password"
  project   = var.project_id
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "postgres_password" {
  secret = google_secret_manager_secret.postgres_password.id
  secret_data = random_password.postgres_password.result
}

resource "google_secret_manager_secret" "app_password" {
  secret_id = "${var.instance_name}-app-password"
  project   = var.project_id
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "app_password" {
  secret = google_secret_manager_secret.app_password.id
  secret_data = random_password.app_password.result
}

resource "google_secret_manager_secret" "client_cert" {
  secret_id = "${var.instance_name}-client-cert"
  project   = var.project_id
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "client_cert" {
  secret = google_secret_manager_secret.client_cert.id
  secret_data = google_sql_ssl_cert.client_cert.cert
}

resource "google_secret_manager_secret" "client_key" {
  secret_id = "${var.instance_name}-client-key"
  project   = var.project_id
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "client_key" {
  secret = google_secret_manager_secret.client_key.id
  secret_data = google_sql_ssl_cert.client_cert.private_key
}

resource "google_secret_manager_secret" "ca_cert" {
  secret_id = "${var.instance_name}-ca-cert"
  project   = var.project_id
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "ca_cert" {
  secret = google_secret_manager_secret.ca_cert.id
  secret_data = google_sql_database_instance.main.server_ca_cert[0].cert
}

output "instance_name" {
  value = google_sql_database_instance.main.name
}

output "instance_connection_name" {
  value = google_sql_database_instance.main.connection_name
}

output "instance_ip" {
  value = google_sql_database_instance.main.private_ip_address
}

output "database_name" {
  value = google_sql_database.default.name
}

output "postgres_user" {
  value = google_sql_user.postgres.name
}

output "app_user" {
  value = google_sql_user.app_user.name
}

output "postgres_password_secret" {
  value = google_secret_manager_secret.postgres_password.secret_id
}

output "app_password_secret" {
  value = google_secret_manager_secret.app_password.secret_id
}