import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_chroma import Chroma
from langchain import hub
import chromadb

load_dotenv()

from arxivsearcher.llm_agent import create_agent

CHROMADB_HOST = os.getenv("CHROMADB_HOST")
chroma_client = chromadb.HttpClient(host=CHROMADB_HOST, port=8000)
chroma_client.heartbeat()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectorstore = Chroma(embedding_function=embeddings, client=chroma_client)

LLM_MODEL = os.getenv("LLM_MODEL")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
llm = HuggingFaceEndpoint(
    repo_id=LLM_MODEL,
    temperature=0.5,
    huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
    task="text-generation"
)

AGENT_PROMPT = os.getenv("AGENT_PROMPT")
prompt = hub.pull(AGENT_PROMPT)

agent_executor = create_agent(vectorstore, llm, prompt)

def main():
    print("Welcome to arXiv AI searcher.")
    query = input("What do you want to know: ")
    response = agent_executor.invoke({"input": query})
    print("Bot:", response["output"])

if __name__ == "__main__":
    main()
    #show me some articles on machine learning
