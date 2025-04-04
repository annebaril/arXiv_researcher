import os
import getpass
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain import hub
import chromadb

from arxivsearcher.llm_agent import create_agent


load_dotenv() 


if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")
else:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CHROMADB_HOST = os.getenv("CHROMADB_HOST")
chroma_client = chromadb.HttpClient(host=CHROMADB_HOST, port=8000)
chroma_client.heartbeat()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectorstore = Chroma(embedding_function=embeddings, client=chroma_client)

LLM_MODEL = os.getenv("LLM_MODEL")
llm = ChatGroq(
    model=LLM_MODEL,
    temperature=0,
    max_tokens=None,
    timeout=10,
    max_retries=2
)

AGENT_PROMPT = os.getenv("AGENT_PROMPT")
prompt = hub.pull(AGENT_PROMPT)

agent_executor = create_agent(vectorstore, llm, prompt)

def main():
    print("Welcome to arXiv AI searcher.")
    query = input("What do you want to know: ")
    response = agent_executor.invoke({"input": query})
    print("Bot: ", response["output"])

if __name__ == "__main__":
    main()
    #show me some articles on machine learning
