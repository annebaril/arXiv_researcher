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

# resource "google_compute_address" "static-ip-address" {
#   name = "chroma-static-ip-address"
# }

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
    	access_config {
			# nat_ip = "${google_compute_address.static-ip-address.address}"
		}
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
	mkdir -p /index_data
	curl -o /home/$USER/docker-compose.yml https://s3.amazonaws.com/public.trychroma.com/cloudformation/assets/docker-compose.yml
	sed -i "s/CHROMA_VERSION/${var.chroma_version}/g" /home/$USER/docker-compose.yml

	# Create .env file
	echo "CHROMA_OPEN_TELEMETRY__ENDPOINT=${var.chroma_otel_collection_endpoint}" >> /home/$USER/.env
	echo "CHROMA_OPEN_TELEMETRY__SERVICE_NAME=${var.chroma_otel_service_name}" >> /home/$USER/.env
	echo "OTEL_EXPORTER_OTLP_HEADERS=${var.chroma_otel_collection_headers}" >> /home/$USER/.env
	echo "PERSIST_DIRECTORY=/index_data" >> /home/$USER/.env

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

resource "google_dataproc_cluster" "mycluster" {
	name     = var.dataproc_name
	region   = var.region_dataproc
	graceful_decommission_timeout = "86400s"
	labels = {
		foo = "bar"
	}

	cluster_config {
    	gce_cluster_config {
      		zone = var.zone_dataproc
    	}
    	master_config {
      		num_instances = 1
      		machine_type  = var.dataproc_machine_type
      		disk_config {
        		boot_disk_type    = var.dataproc_disk_type
        		boot_disk_size_gb = var.dataproc_master_disk_size_gb
      		}
    	}

		worker_config {
		num_instances    = 3
		machine_type     = var.dataproc_machine_type
			disk_config {
				boot_disk_type    = var.dataproc_disk_type
				boot_disk_size_gb = var.dataproc_worker_disk_size_gb
			}
		}

		preemptible_worker_config {
			num_instances = 0
		}

    	# Override or set some custom properties
		software_config {
      		image_version = "2.2-debian12"
      		override_properties = {
        		"dataproc:dataproc.allow.zero.workers" = "true"
				"spark-env:CHROMADB_HOST" = google_compute_instance.chroma_instance.network_interface[0].access_config[0].nat_ip
				"spark-env:DATA_START_JSON_NAME" = var.json_name_data_start
				"spark-env:DATA_START_JSON_GCP" = var.gcp_data_start
				"spark-env:CHROMADB_PORT" = var.chromadb_port
				"spark-env:ENV_DB" = var.env_db
				"spark-env:EMBEDDING_MODEL" = "sentence-transformers/all-mpnet-base-v2"
      		}
		}

		# You can define multiple initialization_action blocks
		initialization_action {
			script      = var.gcp_script_init_cluster_dataproc
			timeout_sec = 500
		}
	}
}

# Submit an example pyspark job to a dataproc cluster
resource "google_dataproc_job" "pyspark" {
  region       = google_dataproc_cluster.mycluster.region
  force_delete = true
  placement {
    cluster_name = google_dataproc_cluster.mycluster.name
  }

  pyspark_config {
    main_python_file_uri = var.gcp_script_job_dataproc
    properties = {
      "spark.logConf" = "true"
    }
  }
}

resource "google_cloud_run_service" "default" {
  name     = "cloudrun-service"
  location = var.region_cloud_run

  template {
	spec {
		containers {
			image = var.cloud_run_image_docker
			env {
				name = "CHROMADB_HOST"
				value = google_compute_instance.chroma_instance.network_interface[0].access_config[0].nat_ip
			}
			env {
				name = "ENV_DB"
				value = var.env_db
			}
			env {
				name = "CHROMADB_PORT"
				value = var.chromadb_port
			}
			resources {
			  limits = {
				"cpu" = "4"
				"memory" = "10Gi"
			  }
			}
		}
	}
  }
}

resource "google_cloud_run_service_iam_policy" "pub1-access" {
	service = google_cloud_run_service.default.name
	location = google_cloud_run_service.default.location
	policy_data = data.google_iam_policy.pub-1.policy_data
}

data "google_iam_policy" "pub-1" {
	binding {
	  role = "roles/run.invoker"
	  members =  ["allUsers"]
	}
}
# Output
output "chroma_instance_ip" {
    description = "Public IP address of the Chroma server"
	value       = google_compute_instance.chroma_instance.network_interface[0].access_config[0].nat_ip
}
