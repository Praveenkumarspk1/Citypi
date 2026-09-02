# IAM Module
# Manages IAM roles, service accounts, and permissions

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "service_accounts" {
  description = "Service accounts to create"
  type = map(object({
    display_name = string
    description  = string
    roles        = list(string)
    labels       = map(string)
  }))
  default = {}
}

variable "custom_roles" {
  description = "Custom roles to create"
  type = map(object({
    title       = string
    description = string
    permissions = list(string)
    stage       = string
  }))
  default = {}
}

variable "project_iam_members" {
  description = "Project-level IAM bindings"
  type = list(object({
    role   = string
    member = string
  }))
  default = []
}

variable "folder_iam_members" {
  description = "Folder-level IAM bindings"
  type = list(object({
    role   = string
    member = string
    folder = string
  }))
  default = []
}

variable "organization_iam_members" {
  description = "Organization-level IAM bindings"
  type = list(object({
    role   = string
    member = string
    org    = string
  }))
  default = []
}

# Service Accounts
resource "google_service_account" "accounts" {
  for_each = var.service_accounts

  account_id   = each.key
  display_name = each.value.display_name
  description  = each.value.description
  labels       = each.value.labels
  project      = var.project_id
}

# Grant roles to service accounts
resource "google_project_iam_member" "sa_roles" {
  for_each = { for k, v in var.service_accounts : k => v }

  project = var.project_id
  role    = v
  member  = "serviceAccount:${google_service_account.accounts[each.key].email}"
  
  for r in v.roles : {
    role = r
  }
}

# Custom Roles
resource "google_project_iam_custom_role" "custom_roles" {
  for_each = var.custom_roles

  role_id     = each.key
  title       = each.value.title
  description = each.value.description
  permissions = each.value.permissions
  stage       = each.value.stage
  project     = var.project_id
}

# Project IAM Members
resource "google_project_iam_member" "project_members" {
  for_each = { for i, m in var.project_iam_members : i => m }

  project = var.project_id
  role    = each.value.role
  member  = each.value.member
}

# Folder IAM Members
resource "google_folder_iam_member" "folder_members" {
  for_each = { for i, m in var.folder_iam_members : i => m }

  folder = each.value.folder
  role   = each.value.role
  member = each.value.member
}

# Organization IAM Members
resource "google_organization_iam_member" "org_members" {
  for_each = { for i, m in var.organization_iam_members : i => m }

  org_id = each.value.org
  role   = each.value.role
  member = each.value.member
}

# Workload Identity Pool for GKE/GitHub Actions
resource "google_iam_workload_identity_pool" "pool" {
  workload_identity_pool_id = "github-actions"
  display_name              = "GitHub Actions Pool"
  description               = "Workload identity pool for GitHub Actions"
  project                   = var.project_id
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub Provider"
  description                        = "GitHub OIDC provider"
  attribute_mapping = {
    "google.subject" = "assertion.sub"
    "attribute.actor" = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  attribute_condition = "assertion.repository_owner == 'your-org'"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
  project = var.project_id
}

output "service_account_emails" {
  value = { for k, v in google_service_account.accounts : k => v.email }
}

output "custom_role_ids" {
  value = [for k, v in google_project_iam_custom_role.custom_roles : v.role_id]
}

output "workload_identity_pool" {
  value = google_iam_workload_identity_pool.pool.name
}

output "workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}