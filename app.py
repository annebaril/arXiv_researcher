import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chat_models import init_chat_model
from langchain_chroma import Chroma
from langchain import hub
import chromadb

load_dotenv() 

from arxivsearcher.llm_agent import create_agent

print("hello")
CHROMADB_HOST = os.getenv("CHROMADB_HOST")
print("CHROMADB_HOST =", CHROMADB_HOST)
chroma_client = chromadb.HttpClient(host=CHROMADB_HOST, port=8000)
print(chroma_client.heartbeat())
print("done")


# create embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectorstore = Chroma(embedding_function=embeddings, client=chroma_client)

# create LLM
LLM_MODEL = os.getenv("LLM_MODEL")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER")
llm = init_chat_model(model=LLM_MODEL, model_provider=MODEL_PROVIDER)

# create agent 
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
