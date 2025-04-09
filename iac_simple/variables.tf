# Variables
variable "project_id" {
  description = "GCP Project ID"
}

variable "region" {
  description = "GCP Region"
}

variable "zone" {
  description = "GCP Zone"
}

variable "instance_name" {
  description = "Name of the Compute Engine instance"
  default     = "chroma-instance"
}

variable "dataproc_name" {
  description = "Name of the Cluster Dataproc"
  default     = "cluster-3f4e"
}

variable "machine_type" {
  description = "Compute Engine machine type"
  default     = "e2-small"
}

variable "chroma_version" {
  description = "Chroma version to install"
  default     = "0.6.3"
}

variable "chroma_server_auth_credentials" {
  description = "Chroma authentication credentials"
  default     = ""
}

variable "chroma_server_auth_provider" {
  description = "Chroma authentication provider"
  default     = ""
}

variable "chroma_auth_token_transport_header" {
  description = "Chroma authentication custom token header"
  default     = ""
}

variable "chroma_otel_collection_endpoint" {
  description = "Chroma OTEL endpoint"
  default     = ""
}

variable "chroma_otel_service_name" {
  description = "Chroma OTEL service name"
  default     = ""
}

variable "chroma_otel_collection_headers" {
  description = "Chroma OTEL headers"
  default     = "{}"
}

variable "chroma_otel_granularity" {
  description = "Chroma OTEL granularity"
  default     = ""
}

variable "chromadb_port" {
  description = "Chroma open port"
  default = 8000
}
