import os
from google.cloud import storage

from flask import Flask, request, render_template, jsonify
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
#from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEndpoint



app = Flask(__name__)

MODEL_NAME = 'sentence-transformers/all-mpnet-base-v2'
BUCKET_NAME = "arxiv-researcher-bucket"
GCS_PERSIST_PATH = "chroma_db/"
LOCAL_PERSIST_PATH = "./local_chromadb/"

REPO_ID = "mistralai/Mistral-7B-Instruct-v0.2"
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN") # TO FIX 

# Embedding model 
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

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

db = get_vectorstore()
retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
llm = HuggingFaceEndpoint(
    repo_id=REPO_ID,
    max_length=128,
    temperature=0.5,
    huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
    task="text-generation"
)
qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)


@app.route("/")
def home():
    return render_template("index_llm.html")


@app.route("/search", methods=["POST"])
def search_similar_items():
    try:
        data = request.form
        query = data.get("query")

        if not query:
            return render_template("index_llm.html", error="Query is required")

        # similarity search 
        docs = retriever.get_relevant_documents(query)

        # Recherche de similarité avec ChromaDB
        return render_template("results.html", results=docs)
    
    except Exception as e:
        return render_template("index_llm.html", error=str(e))


@app.route("/chat", methods=["POST"])
def ask_question_to_chatbot():
    try:
        data = request.form
        user_input = data.get("message")

        if not user_input:
            return jsonify({"response": "Je n'ai pas compris votre question."})

        # Similarity search 
        answer = qa_chain.invoke(user_input)
        return jsonify({"response": answer["result"]})
    
    except Exception as e:
        return render_template("index_llm.html", error=str(e))


if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
