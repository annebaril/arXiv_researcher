# Firewall Rule
resource "google_compute_firewall" "default" {
  name    = "chroma-allow-ssh-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "8000"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# Compute Engine Instance
resource "google_compute_instance" "chroma_instance" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 24
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata_startup_script = <<-EOT
  #!/bin/bash
  USER=chroma
  useradd -m -s /bin/bash $USER
  apt-get update
  apt-get install -y docker.io
  usermod -aG docker $USER
  curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
  ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
  systemctl enable docker
  systemctl start docker

  mkdir -p /home/$USER/config
  curl -o /home/$USER/docker-compose.yml https://s3.amazonaws.com/public.trychroma.com/cloudformation/assets/docker-compose.yml
  sed -i "s/CHROMA_VERSION/${var.chroma_version}/g" /home/$USER/docker-compose.yml

  # Create .env file
  echo "CHROMA_OPEN_TELEMETRY__ENDPOINT=${var.chroma_otel_collection_endpoint}" >> /home/$USER/.env
  echo "CHROMA_OPEN_TELEMETRY__SERVICE_NAME=${var.chroma_otel_service_name}" >> /home/$USER/.env
  echo "OTEL_EXPORTER_OTLP_HEADERS=${var.chroma_otel_collection_headers}" >> /home/$USER/.env

  chown $USER:$USER /home/$USER/.env /home/$USER/docker-compose.yml
  cd /home/$USER
  sudo -u $USER docker-compose up -d
EOT


  # Tags for firewall rules
  tags = ["chroma-server"]

  # Service account with necessary scopes
  service_account {
    scopes = ["cloud-platform"]
  }
}

# Output
output "chroma_instance_ip" {
  description = "Public IP address of the Chroma server"
  value       = google_compute_instance.chroma_instance.network_interface[0].access_config[0].nat_ip
}
