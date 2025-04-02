import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_chroma import Chroma
from langchain import hub

load_dotenv()

from arxivsearcher.load_chroma import download_directory_from_gcs
from arxivsearcher.retrieval import search_articles
from arxivsearcher.llm_agent import create_agent


BUCKET_NAME = os.getenv("BUCKET_NAME")
GCS_PERSIST_PATH = os.getenv("GCS_PERSIST_PATH")
LOCAL_PERSIST_PATH = os.getenv("LOCAL_PERSIST_PATH")

# load chromadb to local from gcs
download_directory_from_gcs(GCS_PERSIST_PATH, LOCAL_PERSIST_PATH, BUCKET_NAME)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectorstore = Chroma(persist_directory=LOCAL_PERSIST_PATH, embedding_function=embeddings)

LLM_MODEL = os.getenv("LLM_MODEL")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
llm = HuggingFaceEndpoint(
    repo_id=LLM_MODEL,
    temperature=0.5,
    huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
    task="text-generation"
)
tools = [search_articles]
AGENT_PROMPT = os.getenv("AGENT_PROMPT")
prompt = hub.pull(AGENT_PROMPT)

agent_executor = create_agent(llm, tools, prompt)

def main():
    print("Welcome to arXiv AI searcher.")
    query = input("What do you want to know: ")
    response = agent_executor.invoke({"input": query})
    print("Bot:", response["output"])

if __name__ == "__main__":
    main()
