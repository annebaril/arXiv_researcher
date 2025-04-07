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

import matplotlib.pyplot as plt

# Debugging Streamlit: https://github.com/VikParuchuri/marker/issues/442
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
@st.cache_resource  # introduit dans la version 1.18.0 de Streamlit
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

# Stocker l'onglet actif
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Chat"

# Création des onglets
tab1, tab2 = st.tabs(["🔍 Articles Search in API", "💬 Chat with arXiv Searcher"])

# Onglet 1 - Articles Search
with tab1:
    if st.session_state.active_tab != "🔍 Articles Search in API":
        st.session_state.active_tab = "🔍 Articles Search in API"

    tab_container = st.container()
    with tab_container:
        st.header("Articles Search in API")

        # Initialisation de l'état de recherche
        if "search_initialized" not in st.session_state:
            st.session_state.search_initialized = False
            st.session_state.last_query = None
            st.session_state.search_results = []  # Ajout d'un état pour stocker les résultats
        
        # Zone de recherche 
        search_query = st.text_input("Search for articles!")

        # Conteneur pour les résultats
        results_container = st.empty()

        # Vérification si la requête a changé et si les résultats doivent être recalculés
        if search_query and search_query != st.session_state.last_query:
            st.session_state.last_query = search_query
            st.session_state.search_results = []  # Réinitialisation des résultats

            # Afficher uniquement le spinner pendant le chargement
            with st.spinner("Processing..."):
                results = search_arxiv(search_query)
                st.session_state.search_results = results  # Stockage des résultats dans la session

        # Affichage des résultats uniquement s'ils ont été chargés
        if st.session_state.search_results:
            with results_container.container():
                for result in st.session_state.search_results:
                    st.write(f"**Title:** {result['title']}")
                    st.write(f"**Authors:** {result['authors']}")
                    st.write(f"**Year:** {result['year']}")               
                    st.write(f"**Abstract:** {result['summary']}")
                    st.write(f"**Link: {result['url']}**")
                    st.write("---")

    # Footer avec mention de l'API
    st.markdown("---")
    st.markdown("Powered by [arXiv API](https://arxiv.org/help/api) and [ChromaDB](https://www.trychroma.com/)")

# Onglet 2 - Chat
with tab2:
    st.header("Chat with arXiv Bot!")
    st.session_state.active_tab = "Chat"
    
    # Initialisation de l'historique de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! I'm your arXiv research assistant. I can help you find and understand research papers. What would you like to know?"
        })
    
    st.markdown("""
        <style>
        .stChatInput {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 1rem;
            background-color: white;
            z-index: 9999;
            box-shadow: 0 -2px 8px rgba(0,0,0,0.05);
            box-sizing: border-box;
        }
        </style>
    """, unsafe_allow_html=True)

    # Affichage des messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Zone de saisie sticky
    if prompt := st.chat_input("Ask a question...", key="chat_input"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("The agent is thinking..."):
            response = agent_executor.invoke({"input": prompt})

            # Vérifie si le résultat contient une figure à afficher
            if isinstance(response.get("output"), plt.Figure):
                print("Displaying figure...")
                st.pyplot(response["output"])
            else:
                print("Displaying text...")
                st.write(response["output"])  # Afficher la réponse normale de l'agent
                st.session_state.messages.append({"role": "assistant", "content": response["output"]})

        # Garder l'onglet actif
        st.session_state.active_tab = "Chat"

        # Utilisation de `st.experimental_rerun()` pour éviter de perdre l'état
        st.rerun()
