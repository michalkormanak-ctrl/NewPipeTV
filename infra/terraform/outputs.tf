output "cloud_run_url" {
  value       = google_cloud_run_v2_service.api.uri
  description = "URL nasadeného API (po terraform apply)."
}

output "db_connection_name" {
  value       = google_sql_database_instance.legis_db.connection_name
  description = "Cloud SQL connection name pre Cloud SQL Auth Proxy."
}

output "source_documents_bucket" {
  value = google_storage_bucket.source_documents.name
}
