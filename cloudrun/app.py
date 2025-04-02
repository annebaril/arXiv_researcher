import os
from google.cloud import storage

from flask import Flask, request, render_template
#from langchain.vectorstores.chroma import Chroma
from langchain_community.vectorstores import Chroma
#from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings


app = Flask(__name__)

# Embedding model 
embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')

BUCKET_NAME = "arxiv-researcher-bucket"
GCS_PERSIST_PATH = "chroma_db/"
LOCAL_PERSIST_PATH = "./local_chromadb/"

def get_vectorstore(gcs_directory=GCS_PERSIST_PATH, local_directory=LOCAL_PERSIST_PATH, bucket_name=BUCKET_NAME):
    # Initialize GCS client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=gcs_directory)

    # Download Chroma persisted data from GCS to local directory
    for blob in blobs:
        if not blob.name.endswith("/"):  # Avoid directory blobs
            relative_path = os.path.relpath(blob.name, gcs_directory)
            local_file_path = os.path.join(local_directory, relative_path)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            blob.download_to_filename(local_file_path)

    # Load the stored vector database
    vectorstore = Chroma(persist_directory=LOCAL_PERSIST_PATH, embedding_function=embeddings)

    # Retrieve all stored documents
    return vectorstore

# cache ? / redit storage 
vectorstore = get_vectorstore()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search_similar_items():
    try:
        data = request.form
        query = data.get("query")
        top_k = int(data.get("top_k", 5))

        if not query:
            return render_template("index.html", error="Query is required")

        # similarity search 
        docs = vectorstore.similarity_search(query)

        # Recherche de similarité avec ChromaDB
        results = docs[0].page_content

        return render_template("results.html", results=results)
    
    except Exception as e:
        return render_template("index.html", error=str(e))


if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
