# Terraform Pub/Sub Module
# Creates topics and subscriptions for async messaging

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

# Topics
resource "google_pubsub_topic" "events" {
  name = "concierge-events"

  message_retention_duration = "604800s"
}

resource "google_pubsub_topic" "notifications" {
  name = "concierge-notifications"

  message_retention_duration = "86400s"
}

resource "google_pubsub_topic" "tasks" {
  name = "concierge-tasks"

  message_retention_duration = "259200s"
}

# Subscriptions
resource "google_pubsub_subscription" "events_worker" {
  name  = "concierge-events-worker"
  topic = google_pubsub_topic.events.name

  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"

  expiration_policy {
    ttl = ""
  }
}

resource "google_pubsub_subscription" "notifications_worker" {
  name  = "concierge-notifications-worker"
  topic = google_pubsub_topic.notifications.name

  ack_deadline_seconds       = 30
  message_retention_duration = "86400s"
}

resource "google_pubsub_subscription" "tasks_worker" {
  name  = "concierge-tasks-worker"
  topic = google_pubsub_topic.tasks.name

  ack_deadline_seconds       = 120
  message_retention_duration = "259200s"
}

output "events_topic" {
  value = google_pubsub_topic.events.id
}

output "notifications_topic" {
  value = google_pubsub_topic.notifications.id
}

output "tasks_topic" {
  value = google_pubsub_topic.tasks.id
}
