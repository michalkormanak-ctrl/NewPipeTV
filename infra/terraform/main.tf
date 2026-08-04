# Kostra infraštruktúry (docs/architecture.md, sekcia 5). NEAPLIKOVANÉ v
# tomto sedení - chýba GCP projekt/oprávnenia (docs/risks.md, blokujúca
# neistota č. 2). Pred `terraform apply` je potrebné:
#   1. mať existujúci GCP projekt s povolenou fakturáciou,
#   2. povoliť potrebné API (cloudresourcemanager, sqladmin, run, pubsub,
#      cloudscheduler, secretmanager, storage),
#   3. nastaviť GCS backend pre state (versions.tf).

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "required" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "pubsub.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "aiplatform.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_sql_database_instance" "legis_db" {
  name             = "sk-legis-${var.environment}"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = var.db_tier
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
  }

  deletion_protection = var.environment == "prod"
  depends_on          = [google_project_service.required]
}

resource "google_sql_database" "legis" {
  name     = "legis"
  instance = google_sql_database_instance.legis_db.name
}

resource "google_storage_bucket" "source_documents" {
  name                        = "${var.project_id}-legis-source-documents-${var.environment}"
  location                    = var.region
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

resource "google_pubsub_topic" "ingestion_events" {
  name = "legis-ingestion-events-${var.environment}"
}

resource "google_cloud_run_v2_service" "api" {
  name     = "sk-legis-api-${var.environment}"
  location = var.region

  template {
    containers {
      # Image sa buildí a pushuje samostatne (CI/CD, mimo rozsahu tohto
      # Terraform modulu) - viď backend/Dockerfile.
      image = "gcr.io/${var.project_id}/sk-legis-api:latest"
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
    }
  }

  depends_on = [google_project_service.required]
}

resource "google_cloud_scheduler_job" "daily_ingest" {
  name      = "legis-daily-ingest-${var.environment}"
  schedule  = "0 3 * * *" # 03:00 denne - viď docs/update-procedure.md
  time_zone = "Europe/Bratislava"

  pubsub_target {
    topic_name = google_pubsub_topic.ingestion_events.id
    data       = base64encode("{\"trigger\":\"daily_ingest\"}")
  }

  depends_on = [google_project_service.required]
}
