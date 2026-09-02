# DNS Module
# Creates Cloud DNS managed zones and records

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "zone_name" {
  description = "DNS zone name (without .)"
  type        = string
}

variable "dns_name" {
  description = "DNS name (with trailing .)"
  type        = string
}

variable "description" {
  description = "Zone description"
  type        = string
  default     = "Managed by Terraform"
}

variable "labels" {
  description = "Labels for the zone"
  type        = map(string)
  default     = {}
}

variable "records" {
  description = "DNS records to create"
  type = list(object({
    name    = string
    type    = string
    ttl     = number
    rrdatas = list(string)
  }))
  default = []
}

variable "managed_zone" {
  description = "Existing managed zone name (optional)"
  type        = string
  default     = ""
}

variable "visibility" {
  description = "Zone visibility (public, private)"
  type        = string
  default     = "public"
}

variable "private_networks" {
  description = "Networks for private zone"
  type = list(object({
    network_url = string
  }))
  default = []
}

# Managed Zone
resource "google_dns_managed_zone" "zone" {
  name        = var.managed_zone != "" ? var.managed_zone : var.zone_name
  project     = var.project_id
  dns_name    = var.dns_name
  description = var.description
  labels      = var.labels
  visibility  = var.visibility

  dynamic "private_visibility_config" {
    for_each = var.visibility == "private" ? [1] : []
    content {
      networks = var.private_networks
    }
  }
}

# DNS Records
resource "google_dns_record_set" "records" {
  for_each = { for i, r in var.records : "${r.name}-${r.type}-${i}" => r }

  name    = each.value.name
  type    = each.value.type
  ttl     = each.value.ttl
  rrdatas = each.value.rrdatas
  managed_zone = google_dns_managed_zone.zone.name
  project = var.project_id
}

output "zone_name" {
  value = google_dns_managed_zone.zone.name
}

output "zone_dns_name" {
  value = google_dns_managed_zone.zone.dns_name
}

output "name_servers" {
  value = google_dns_managed_zone.zone.name_servers
}

output "record_sets" {
  value = [for k, v in google_dns_record_set.records : {
    name = v.name
    type = v.type
    ttl  = v.ttl
    rrdatas = v.rrdatas
  }]
}