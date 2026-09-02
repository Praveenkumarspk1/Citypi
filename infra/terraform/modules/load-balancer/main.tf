# Load Balancer Module
# Creates Global HTTP(S) Load Balancer with Cloud CDN

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "name" {
  description = "Load balancer name prefix"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "backend_services" {
  description = "Backend services configuration"
  type = list(object({
    name              = string
    backends = list(object({
      group           = string
      balancing_mode  = string
      capacity_scaler = number
    }))
    health_check = string
    cdn_enabled  = bool
    cache_key_policy = object({
      include_protocol = bool
      include_host     = bool
      include_query_string = bool
      query_string_whitelist = list(string)
      query_string_blacklist = list(string)
    })
    custom_request_headers = list(string)
    custom_response_headers = list(string)
  }))
  default = []
}

variable "ssl_certificates" {
  description = "SSL certificates for the load balancer"
  type = list(object({
    name    = string
    domains = list(string)
  }))
  default = []
}

variable "url_map_rules" {
  description = "URL map rules for routing"
  type = list(object({
    hosts = list(string)
    paths = list(string)
    service = string
  }))
  default = []
}

variable "enable_cdn" {
  description = "Enable Cloud CDN"
  type        = bool
  default     = true
}

variable "enable_quic" {
  description = "Enable QUIC protocol"
  type        = bool
  default     = true
}

variable "enable_http2" {
  description = "Enable HTTP/2"
  type        = bool
  default     = true
}

variable "waf_policy" {
  description = "WAF policy to attach"
  type        = string
  default     = ""
}

# Health Checks
resource "google_compute_health_check" "backend_health" {
  for_each = { for bs in var.backend_services : bs.name => bs }

  name        = "${var.name}-${each.key}-health"
  project     = var.project_id
  check_interval_sec  = 30
  timeout_sec         = 10
  healthy_threshold   = 2
  unhealthy_threshold = 3

  http_health_check {
    path        = "/health/ready"
    port        = 8080
    request_headers = ["Host", "health-check"]
  }
}

# Backend Services
resource "google_compute_backend_service" "backends" {
  for_each = { for bs in var.backend_services : bs.name => bs }

  name                  = "${var.name}-${each.key}"
  project               = var.project_id
  protocol              = "HTTP"
  timeout_sec           = 30
  enable_cdn            = each.value.cdn_enabled
  load_balancing_scheme = "EXTERNAL_MANAGED"

  health_checks = [google_compute_health_check.backend_health[each.key].id]

  backend {
    group           = each.value.backends[0].group
    balancing_mode  = each.value.backends[0].balancing_mode
    capacity_scaler = each.value.backends[0].capacity_scaler
  }

  cdn_policy {
    cache_key_policy {
      include_protocol          = each.value.cache_key_policy.include_protocol
      include_host              = each.value.cache_key_policy.include_host
      include_query_string      = each.value.cache_key_policy.include_query_string
      query_string_whitelist    = each.value.cache_key_policy.query_string_whitelist
      query_string_blacklist    = each.value.cache_key_policy.query_string_blacklist
    }
    signed_url_cache_max_age_sec = 3600
  }

  custom_request_headers  = each.value.custom_request_headers
  custom_response_headers = each.value.custom_response_headers

  security_policy = var.waf_policy != "" ? var.waf_policy : null

  log_config {
    enable = true
    sample_rate = 1.0
  }
}

# SSL Certificates
resource "google_compute_managed_ssl_certificate" "ssl_certs" {
  for_each = { for cert in var.ssl_certificates : cert.name => cert }

  name        = "${var.name}-${each.key}"
  project     = var.project_id
  managed {
    domains = each.value.domains
  }
}

# URL Map
resource "google_compute_url_map" "url_map" {
  name            = "${var.name}-url-map"
  project         = var.project_id
  default_service = var.backend_services[0].name != "" ? google_compute_backend_service.backends[var.backend_services[0].name].id : null

  host_rule = [
    for rule in var.url_map_rules : {
      hosts = rule.hosts
      path_matcher = "${var.name}-${rule.service}-matcher"
    }
  ]

  path_matcher = [
    for rule in var.url_map_rules : {
      name = "${var.name}-${rule.service}-matcher"
      default_service = google_compute_backend_service.backends[rule.service].id
      path_rule = [
        for path in rule.paths : {
          paths   = [path]
          service = google_compute_backend_service.backends[rule.service].id
        }
      ]
    }
  ]
}

# Target HTTP Proxy
resource "google_compute_target_http_proxy" "http_proxy" {
  name        = "${var.name}-http-proxy"
  project     = var.project_id
  url_map     = google_compute_url_map.url_map.id
}

# Target HTTPS Proxy
resource "google_compute_target_https_proxy" "https_proxy" {
  name             = "${var.name}-https-proxy"
  project          = var.project_id
  url_map          = google_compute_url_map.url_map.id
  ssl_certificates = [for cert in google_compute_managed_ssl_certificate.ssl_certs : cert.id]
  quic_override    = var.enable_quic ? "ENABLE" : "DISABLE"
  http2_enabled    = var.enable_http2
}

# Global Forwarding Rules
resource "google_compute_global_forwarding_rule" "http" {
  name        = "${var.name}-http"
  project     = var.project_id
  target      = google_compute_target_http_proxy.http_proxy.id
  port_range  = "80"
  ip_protocol = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  network_tier = "PREMIUM"
}

resource "google_compute_global_forwarding_rule" "https" {
  name        = "${var.name}-https"
  project     = var.project_id
  target      = google_compute_target_https_proxy.https_proxy.id
  port_range  = "443"
  ip_protocol = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  network_tier = "PREMIUM"
}

# Global External IP Address
resource "google_compute_global_address" "ipv4" {
  name        = "${var.name}-ipv4"
  project     = var.project_id
  ip_version  = "IPV4"
  network_tier = "PREMIUM"
}

resource "google_compute_global_address" "ipv6" {
  name        = "${var.name}-ipv6"
  project     = var.project_id
  ip_version  = "IPV6"
  network_tier = "PREMIUM"
}

output "http_proxy_id" {
  value = google_compute_target_http_proxy.http_proxy.id
}

output "https_proxy_id" {
  value = google_compute_target_https_proxy.https_proxy.id
}

output "url_map_id" {
  value = google_compute_url_map.url_map.id
}

output "ipv4_address" {
  value = google_compute_global_address.ipv4.address
}

output "ipv6_address" {
  value = google_compute_global_address.ipv6.address
}

output "backend_service_ids" {
  value = { for k, v in google_compute_backend_service.backends : k => v.id }
}