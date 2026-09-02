# Monitoring Module
# Sets up Cloud Monitoring with dashboards, alerts, and uptime checks

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "notification_channels" {
  description = "Notification channels for alerts"
  type = list(object({
    type        = string
    display_name = string
    labels      = map(string)
    enabled     = bool
  }))
  default = []
}

variable "alert_policies" {
  description = "Alert policies to create"
  type = list(object({
    display_name = string
    conditions   = list(object({
      display_name = string
      condition_threshold = object({
        filter          = string
        comparison      = string
        threshold_value = number
        duration        = string
        aggregations = list(object({
          alignment_period   = string
          per_series_aligner = string
          cross_series_reducer = string
          group_by_fields = list(string)
        }))
      })
    }))
    notification_channels = list(string)
    enabled = bool
  }))
  default = []
}

variable "uptime_checks" {
  description = "Uptime checks to create"
  type = list(object({
    display_name = string
    hostname     = string
    path         = string
    port         = number
    check_interval = number
    timeout      = number
    content_matchers = list(string)
    regions = list(string)
  }))
  default = []
}

variable "dashboard_configs" {
  description = "Custom dashboard configurations"
  type = list(object({
    display_name = string
    mosaic_layout = list(object({
      x_pos = number
      y_pos = number
      width = number
      height = number
      widget = object({
        title = string
        xy_chart = object({
          data_sets = list(object({
            time_series_query = object({
              time_series_filter = object({
                filter = string
                aggregation = object({
                  alignment_period = string
                  per_series_aligner = string
                  cross_series_reducer = string
                  group_by_fields = list(string)
                })
              })
            })
            plot_type = string
          }))
          timeshift_duration = string
          y_axis = object({
            label = string
            scale = string
          })
        })
      })
    }))
  }))
  default = []
}

# Notification Channels
resource "google_monitoring_notification_channel" "channels" {
  for_each = { for i, ch in var.notification_channels : i => ch }
  
  project         = var.project_id
  type            = each.value.type
  display_name    = each.value.display_name
  labels          = each.value.labels
  enabled         = each.value.enabled
}

# Alert Policies
resource "google_monitoring_alert_policy" "policies" {
  for_each = { for i, p in var.alert_policies : i => p }

  project     = var.project_id
  display_name = each.value.display_name
  combiner    = "OR"
  enabled     = each.value.enabled

  dynamic "conditions" {
    for_each = each.value.conditions
    content {
      display_name = conditions.value.display_name
      condition_threshold {
        filter          = conditions.value.condition_threshold.filter
        comparison      = conditions.value.condition_threshold.comparison
        threshold_value = conditions.value.condition_threshold.threshold_value
        duration        = conditions.value.condition_threshold.duration
        aggregations = [
          for agg in conditions.value.condition_threshold.aggregations : {
            alignment_period   = agg.alignment_period
            per_series_aligner = agg.per_series_aligner
            cross_series_reducer = agg.cross_series_reducer
            group_by_fields    = agg.group_by_fields
          }
        ]
      }
    }
  }

  notification_channels = [
    for ch in each.value.notification_channels : 
    google_monitoring_notification_channel.channels[ch].name
  ]
}

# Uptime Checks
resource "google_monitoring_uptime_check_config" "uptime_checks" {
  for_each = { for i, u in var.uptime_checks : i => u }

  project         = var.project_id
  display_name    = each.value.display_name
  hostname        = each.value.hostname
  path            = each.value.path
  port            = each.value.port
  check_interval  = "${each.value.check_interval}s"
  timeout         = "${each.value.timeout}s"
  content_matchers = each.value.content_matchers
  selected_regions = each.value.regions

  http_check {
    path = each.value.path
    port = each.value.port
    use_ssl = true
  }
}

# Custom Dashboards
resource "google_monitoring_dashboard" "dashboards" {
  for_each = { for i, d in var.dashboard_configs : i => d }

  project     = var.project_id
  display_name = each.value.display_name
  mosaic_layout {
    tiles = [
      for tile in each.value.mosaic_layout : {
        x_pos = tile.x_pos
        y_pos = tile.y_pos
        width = tile.width
        height = tile.height
        widget {
          title = tile.widget.title
          xy_chart {
            data_sets = [
              for ds in tile.widget.xy_chart.data_sets : {
                time_series_query {
                  time_series_filter {
                    filter = ds.time_series_query.time_series_filter.filter
                    aggregation {
                      alignment_period = ds.time_series_query.time_series_filter.aggregation.alignment_period
                      per_series_aligner = ds.time_series_query.time_series_filter.aggregation.per_series_aligner
                      cross_series_reducer = ds.time_series_query.time_series_filter.aggregation.cross_series_reducer
                      group_by_fields = ds.time_series_query.time_series_filter.aggregation.group_by_fields
                    }
                  }
                }
                plot_type = ds.plot_type
              }
            ]
            timeshift_duration = tile.widget.xy_chart.timeshift_duration
            y_axis {
              label = tile.widget.xy_chart.y_axis.label
              scale = tile.widget.xy_chart.y_axis.scale
            }
          }
        }
      }
    ]
  }
}

output "notification_channel_names" {
  value = [for k, v in google_monitoring_notification_channel.channels : v.name]
}

output "alert_policy_names" {
  value = [for k, v in google_monitoring_alert_policy.policies : v.name]
}

output "uptime_check_names" {
  value = [for k, v in google_monitoring_uptime_check_config.uptime_checks : v.name]
}

output "dashboard_names" {
  value = [for k, v in google_monitoring_dashboard.dashboards : v.name]
}