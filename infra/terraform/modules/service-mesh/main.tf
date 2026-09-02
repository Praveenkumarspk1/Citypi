# Terraform Service Mesh Module
# Configures Istio/Anthos Service Mesh for Cloud Run

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "mesh_name" {
  description = "Service Mesh name"
  type        = string
  default     = "concierge-mesh"
}

# Enable required APIs
resource "google_project_service" "trafficdirector" {
  project = var.project_id
  service = "trafficdirector.googleapis.com"
}

resource "google_project_service" "networkservices" {
  project = var.project_id
  service = "networkservices.googleapis.com"
}

# VPC for service mesh
resource "google_compute_network" "mesh_vpc" {
  name                    = "${var.mesh_name}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "mesh_subnet" {
  name          = "${var.mesh_name}-subnet"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.mesh_vpc.id
}

# Firewall rule for mesh traffic
resource "google_compute_firewall" "mesh_allow_internal" {
  name    = "${var.mesh_name}-allow-internal"
  network = google_compute_network.mesh_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["8000", "8001", "8080", "9090"]
  }

  source_ranges = ["10.0.0.0/20"]
}

output "vpc_name" {
  value = google_compute_network.mesh_vpc.name
}

output "subnet_name" {
  value = google_compute_subnetwork.mesh_subnet.name
}
