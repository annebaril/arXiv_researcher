import os
import streamlit as st
import torch
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
from langchain.chat_models import init_chat_model
from langchain import hub

from arxivsearcher.llm_agent import create_agent
from arxivsearcher.api_request import search_arxiv

# debuging streamlit: https://github.com/VikParuchuri/marker/issues/442
torch.classes.__path__ = []

# Chargement des variables d'environnement
load_dotenv()

# Configuration initiale
CHROMADB_HOST = os.getenv("CHROMADB_HOST")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
LLM_MODEL = os.getenv("LLM_MODEL")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER")
AGENT_PROMPT = os.getenv("AGENT_PROMPT")

# Initialisation de l'application Streamlit 
st.set_page_config(
    page_title="arXiv Searcher",
    page_icon="📚",
    layout="wide"
)

st.title("📚 arXiv Searcher")

# Initialisation des composants
@st.cache_resource # introduit dans la version 1.18.0 de Streamlit
def initialize_components(): 
    # Initialisation des embeddings
    chroma_client = chromadb.HttpClient(host=CHROMADB_HOST, port=8000)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = Chroma(embedding_function=embeddings, client=chroma_client)

    # Initialisation du LLM
    llm = init_chat_model(model=LLM_MODEL, model_provider=MODEL_PROVIDER)
    
    # Initialisation de l'agent
    prompt = hub.pull(AGENT_PROMPT)
    agent_executor = create_agent(vectorstore, llm, prompt)
    
    return vectorstore, agent_executor

# Initialisation des composants
vectorstore, agent_executor = initialize_components()
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

print(vectorstore)


# Création des onglets
tab1, tab2 = st.tabs(["🔍 Articles Search in API", "💬 Chat with arXiv Searcher"])

with tab1:
    st.header("Articles Search in API") # TO DO : API SEARCH + cite API
    search_query = st.text_input("Search for articles!")
    if search_query:
        with st.spinner("Processing..."):
            results = search_arxiv(search_query)
            for result in results:
                st.write(f"**Title:** {result['title']}")
                st.write(f"**Authors:** {result['authors']}")
                st.write(f"**Year:** {result['year']}")               
                st.write(f"**Abstract:** {result['summary']}")
                st.write(f"**Link: {result['url']}**")
                st.write("---")

with tab2:
    st.header("Chat with arXiv Bot!")
    
    # Initialisation de l'historique de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! I'm your arXiv research assistant. I can help you find and understand research papers. What would you like to know?"
        })
    
    # Conteneur pour les messages
    chat_container = st.container()
    
    # Zone de saisie fixe en bas
    with st.container():
        st.markdown("---")
        if prompt := st.chat_input("Ask a question...", key="chat_input"):
            # Ajout du message de l'utilisateur à l'historique
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Génération de la réponse
            with st.spinner("The agent is thinking..."):
                response = agent_executor.invoke({"input": prompt})
                st.session_state.messages.append({"role": "assistant", "content": response["output"]})
            
            # Rafraîchir l'affichage des messages
            st.rerun()
    
    # Affichage des messages dans le conteneur dédié
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"]) 

