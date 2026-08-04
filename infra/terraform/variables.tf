variable "project_id" {
  description = "GCP projekt (blokujúca závislosť - nie je k dispozícii v tomto sedení, docs/risks.md)."
  type        = string
}

variable "region" {
  description = "Primárny GCP región."
  type        = string
  default     = "europe-west3" # Frankfurt - najbližší k SR z bežne ponúkaných regiónov
}

variable "environment" {
  description = "Prostredie (dev/staging/prod)."
  type        = string
  default     = "dev"
}

variable "db_tier" {
  description = "Cloud SQL tier pre PostgreSQL."
  type        = string
  default     = "db-custom-2-8192"
}
