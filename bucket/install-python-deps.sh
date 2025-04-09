#!/bin/bash

set -euxo pipefail

# Remplace ce chemin par celui où est stocké ton requirements.txt
#gs://<BUCKET_NAME>/<PATH_TO_FILE>
REQUIREMENTS_PATH="gs://bucket-terraform-arxiv-researcher/requirements.txt"
LOCAL_REQUIREMENTS="/tmp/requirements.txt"

# Copier depuis GCS vers le systÃ¨me de fichiers local
gsutil cp "$REQUIREMENTS_PATH" "$LOCAL_REQUIREMENTS"

# Installer les dÃ©pendances
pip install -r "$LOCAL_REQUIREMENTS"