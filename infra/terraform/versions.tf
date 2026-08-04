terraform {
  required_version = ">= 1.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Produkčný state musí byť v GCS backende (docs/backup-recovery.md), nie
  # lokálne. Backend blok je zámerne prázdny (vyžaduje konkrétny bucket
  # názov od gestora infraštruktúry) - `terraform init -backend-config=...`.
  backend "gcs" {}
}
