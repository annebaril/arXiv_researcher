import os
import streamlit as st
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_chroma import Chroma
from langchain import hub

from arxivsearcher.load_chroma import download_directory_from_gcs
from arxivsearcher.retrieval import search_articles
from arxivsearcher.llm_agent import create_agent

# Chargement des variables d'environnement
load_dotenv()

# Configuration initiale
BUCKET_NAME = os.getenv("BUCKET_NAME")
GCS_PERSIST_PATH = os.getenv("GCS_PERSIST_PATH")
LOCAL_PERSIST_PATH = os.getenv("LOCAL_PERSIST_PATH")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
LLM_MODEL = os.getenv("LLM_MODEL")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
AGENT_PROMPT = os.getenv("AGENT_PROMPT")

# Initialisation de l'application Streamlit
st.set_page_config(
    page_title="arXiv Researcher",
    page_icon="📚",
    layout="wide"
)

st.title("📚 arXiv Researcher")

# Initialisation des composants
@st.cache_resource
def initialize_components():
    # Téléchargement de la base de données Chroma
    download_directory_from_gcs(GCS_PERSIST_PATH, LOCAL_PERSIST_PATH, BUCKET_NAME)
    
    # Initialisation des embeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = Chroma(persist_directory=LOCAL_PERSIST_PATH, embedding_function=embeddings)
    
    # Initialisation du LLM
    llm = HuggingFaceEndpoint(
        repo_id=LLM_MODEL,
        temperature=0.5,
        huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
        task="text-generation"
    )
    
    # Initialisation de l'agent
    tools = [search_articles]
    prompt = hub.pull(AGENT_PROMPT)
    agent_executor = create_agent(llm, tools, prompt)
    
    return vectorstore, agent_executor

# Initialisation des composants
vectorstore, agent_executor = initialize_components()

# Création des onglets
tab1, tab2 = st.tabs(["🔍 Recherche d'articles", "💬 Chat avec arXiv Researcher"])

with tab1:
    st.header("Recherche d'articles")
    search_query = st.text_input("Entrez votre requête de recherche:")
    if search_query:
        with st.spinner("Recherche en cours..."):
            results = search_articles(vectorstore, search_query)
            for result in results:
                st.write(f"**Titre:** {result['title']}")
                st.write(f"**Auteurs:** {result['authors']}")
                st.write(f"**Résumé:** {result['abstract']}")
                st.write("---")

with tab2:
    st.header("Chat avec l'agent")
    
    # Initialisation de l'historique de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Affichage de l'historique des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Zone de saisie pour le message de l'utilisateur
    if prompt := st.chat_input("Posez votre question..."):
        # Ajout du message de l'utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Génération de la réponse
        with st.chat_message("assistant"):
            with st.spinner("L'agent réfléchit..."):
                response = agent_executor.invoke({"input": prompt})
                st.markdown(response["output"])
                st.session_state.messages.append({"role": "assistant", "content": response["output"]}) 