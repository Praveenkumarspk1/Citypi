# CDN Module
# Creates Cloud CDN configuration with custom cache keys and signed URLs

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "backend_service_name" {
  description = "The backend service to enable CDN on"
  type        = string
}

variable "cache_key_policy" {
  description = "Cache key policy configuration"
  type = object({
    include_protocol          = bool
    include_host              = bool
    include_query_string      = bool
    query_string_whitelist    = list(string)
    query_string_blacklist    = list(string)
  })
  default = {
    include_protocol          = true
    include_host              = true
    include_query_string      = true
    query_string_whitelist    = []
    query_string_blacklist    = []
  }
}

variable "signed_url_cache_max_age_sec" {
  description = "Maximum age for signed URLs in seconds"
  type        = number
  default     = 3600
}

variable "cache_mode" {
  description = "Cache mode (CACHE_ALL_STATIC, USE_ORIGIN_HEADERS, FORCE_CACHE_ALL)"
  type        = string
  default     = "USE_ORIGIN_HEADERS"
}

variable "client_ttl_sec" {
  description = "Client TTL in seconds"
  type        = number
  default     = 3600
}

variable "default_ttl_sec" {
  description = "Default TTL in seconds"
  type        = number
  default     = 3600
}

variable "max_ttl_sec" {
  description = "Maximum TTL in seconds"
  type        = number
  default     = 86400
}

variable "negative_caching" {
  description = "Enable negative caching"
  type        = bool
  default     = true
}

variable "negative_caching_policy" {
  description = "Negative caching policy"
  type = list(object({
    code = number
    ttl  = number
  }))
  default = [
    { code = 301, ttl = 300 },
    { code = 302, ttl = 300 },
    { code = 404, ttl = 60 },
    { code = 410, ttl = 60 },
    { code = 500, ttl = 30 },
  ]
}

variable "serve_stale_on_error" {
  description = "Serve stale content on error"
  type        = bool
  default     = true
}

variable "compress" {
  description = "Enable compression"
  type        = bool
  default     = true
}

# CDN Policy on Backend Service
resource "google_compute_backend_service" "cdn_backend" {
  name        = var.backend_service_name
  project     = var.project_id
  enable_cdn  = true

  cdn_policy {
    cache_key_policy {
      include_protocol          = var.cache_key_policy.include_protocol
      include_host              = var.cache_key_policy.include_host
      include_query_string      = var.cache_key_policy.include_query_string
      query_string_whitelist    = var.cache_key_policy.query_string_whitelist
      query_string_blacklist    = var.cache_key_policy.query_string_blacklist
    }
    signed_url_cache_max_age_sec = var.signed_url_cache_max_age_sec
    cache_mode                   = var.cache_mode
    client_ttl_sec               = var.client_ttl_sec
    default_ttl_sec              = var.default_ttl_sec
    max_ttl_sec                  = var.max_ttl_sec
    negative_caching             = var.negative_caching
    negative_caching_policy = [
      for policy in var.negative_caching_policy : {
        code = policy.code
        ttl  = policy.ttl
      }
    ]
    serve_stale_on_error = var.serve_stale_on_error
    compress = var.compress
  }
}

# Signed URL Keys
resource "google_compute_backend_service_signed_url_key" "signed_url_keys" {
  count = 2
  name = "${var.backend_service_name}-signed-url-key-${count.index}"
  project = var.project_id
  backend_service = var.backend_service_name
  key_value = base64encode(random_bytes.key[count.index].bytes)
}

resource "random_bytes" "key" {
  count  = 2
  length = 16
}

output "signed_url_key_names" {
  value = [for k in google_compute_backend_service_signed_url_key.signed_url_keys : k.name]
}