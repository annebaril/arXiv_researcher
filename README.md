# arXiv Researcher

An intelligent literature search system that helps researchers find and analyze academic papers from [arXiv](https://arxiv.org/).

## Features

- 🔍 **Article Search**: Direct search in the arXiv API with formatted results
- 💬 **Chat Interface**: Interactive chat with an AI assistant that can help find and understand research papers
- 📈 **Trend Analysis**: Visualize research trends over time for specific topics

## Installation


### Option 1: Using Poetry (Local Installation)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/arXiv_researcher.git
cd arXiv_researcher
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Set up environment variables:
Create a `.env` file with the following variables:
```
CHROMADB_HOST=your_chromadb_host
AGENT_PROMPT=hwchase17/structured-chat-agent
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
LLM_MODEL=gemini-2.0-flash-lite
MODEL_PROVIDER=google_vertexai
VERBOSE=True
```

### Option 2: Using Docker

1. Pull the Docker image:
```bash
docker pull europe-west1-docker.pkg.dev/arxiv-researcher/arxiv-searcher/arxiv-app:latest 
```

2. Run the container:
```bash
docker run -p 8501:8501 
```
The application will be available at `http://localhost:8501`

## Installation Terraform
1. Créer une copie du fichier de variable terraform :
```bash
cd iac
cp chroma.tfvars.example chroma.tfvars
```

2. Modifier le fichier pour remplacer les données :
```bash
nano chroma.tfvars
```

3. Initialiser le terraform :
```bash
terraform init
```

4. Planifier pour vérifier les informations puis Déployer :
```bash
terraform plan -var-file chroma.tfvars
terraform apply -var-file chroma.tfvars
```

5. Récupérer l'ip du chroma fraichement créer :
```bash
terraform output -raw chroma_instance_ip
```

6. Remplacer l'ip du chroma avec celui récupérer

7. Modifier les variables dans le fichier `iac/script/add_from_json.py`

8. Lancer la commande : 
```bash
gcloud dataproc jobs submit pyspark script/add_from_json.py \
    --cluster=<NOM_CLUSTER> \
    --region=<REGION_CLUSTER>
```
Vous avez à la fin une VM avec un chroma d'installer et un cluster dataproc

## Usage

1. Start the Streamlit application:
```bash
poetry run streamlit run streamlit_app.py
```

2. Use the application through your web browser:
- Use the search tab to directly search arXiv
- Chat with the AI assistant to get help finding and understanding papers
- Analyze research trends for specific topics

## Technologies Used

- Streamlit for the web interface
- LangChain for AI agent functionality
- ChromaDB for vector storage
- arXiv API for paper search
- HuggingFace for embeddings
- Matplotlib for trend visualization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## Dataset
The dataset used to feed the LLM agent: https://www.kaggle.com/code/arthurchariyasathian/week7-projectexam-rag-option-1/notebook



