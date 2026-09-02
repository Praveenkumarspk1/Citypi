# VPC Module
# Creates a VPC network with subnets, firewall rules, and NAT

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "network_name" {
  description = "The VPC network name"
  type        = string
  default     = "concierge-vpc"
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "subnet_cidr" {
  description = "CIDR range for the main subnet"
  type        = string
  default     = "10.0.0.0/20"
}

variable "secondary_ranges" {
  description = "Secondary IP ranges for the subnet"
  type = list(object({
    range_name    = string
    ip_cidr_range = string
  }))
  default = [
    {
      range_name    = "cloud-run"
      ip_cidr_range = "10.0.16.0/20"
    },
    {
      range_name    = "cloud-sql"
      ip_cidr_range = "10.0.32.0/20"
    },
    {
      range_name    = "redis"
      ip_cidr_range = "10.0.48.0/20"
    },
    {
      range_name    = "vpc-connector"
      ip_cidr_range = "10.0.64.0/28"
    },
  ]
}

variable "enable_private_google_access" {
  description = "Enable Private Google Access"
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = var.network_name
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode            = "GLOBAL"
  mtu                     = 1460

  delete_default_routes_on_create = false
}

# Main Subnet
resource "google_compute_subnetwork" "main" {
  name                     = "${var.network_name}-subnet"
  project                  = var.project_id
  network                  = google_compute_network.vpc.id
  region                   = var.region
  ip_cidr_range            = var.subnet_cidr
  private_ip_google_access = var.enable_private_google_access

  secondary_ip_range = var.secondary_ranges

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# VPC Connector Subnet (for Serverless VPC Access)
resource "google_compute_subnetwork" "vpc_connector" {
  name                     = "${var.network_name}-vpc-connector"
  project                  = var.project_id
  network                  = google_compute_network.vpc.id
  region                   = var.region
  ip_cidr_range            = "10.0.64.0/28"
  purpose                  = "PRIVATE_SERVICE_CONNECT"
  private_ip_google_access = true
}

# Firewall Rules
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.network_name}-allow-internal"
  project = var.project_id
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "icmp"
  }

  source_ranges = [var.subnet_cidr]
  priority      = 1000
  direction     = "INGRESS"
}

resource "google_compute_firewall" "allow_health_checks" {
  name    = "${var.network_name}-allow-health-checks"
  project = var.project_id
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8000", "8001", "8080", "8081", "9090"]
  }

  source_ranges = [
    "130.211.0.0/22",  # GCP health checks
    "35.191.0.0/16",   # GCP health checks
  ]
  priority  = 1000
  direction = "INGRESS"
  target_tags = ["allow-health-checks"]
}

resource "google_compute_firewall" "allow_cloud_run" {
  name    = "${var.network_name}-allow-cloud-run"
  project = var.project_id
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["8080", "8081", "8000", "8001"]
  }

  source_tags = ["cloud-run"]
  target_tags = ["cloud-sql", "redis"]
  priority    = 1000
  direction   = "INGRESS"
}

# Cloud NAT
resource "google_compute_router" "nat_router" {
  name       = "${var.network_name}-nat-router"
  project    = var.project_id
  network    = google_compute_network.vpc.name
  region     = var.region
  bgp {
    asn = 64514
  }
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.network_name}-nat"
  project                            = var.project_id
  router                             = google_compute_router.nat_router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Private Service Connection for Cloud SQL
resource "google_service_networking_connection" "private_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}

resource "google_compute_global_address" "private_ip_range" {
  name          = "${var.network_name}-private-ip-range"
  project       = var.project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

output "network_id" {
  value = google_compute_network.vpc.id
}

output "network_name" {
  value = google_compute_network.vpc.name
}

output "subnet_id" {
  value = google_compute_subnetwork.main.id
}

output "subnet_name" {
  value = google_compute_subnetwork.main.name
}

output "vpc_connector_subnet_id" {
  value = google_compute_subnetwork.vpc_connector.id
}

output "nat_router_name" {
  value = google_compute_router.nat_router.name
}