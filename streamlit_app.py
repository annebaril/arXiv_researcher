import os
import streamlit as st
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_chroma import Chroma
import chromadb
from langchain import hub

from arxivsearcher.llm_agent import create_agent

# Chargement des variables d'environnement
load_dotenv()

# Configuration initiale
CHROMADB_HOST = os.getenv("CHROMADB_HOST")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
LLM_MODEL = os.getenv("LLM_MODEL")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
AGENT_PROMPT = os.getenv("AGENT_PROMPT")

# Initialisation de l'application Streamlit
st.set_page_config(
    page_title="arXiv Searcher",
    page_icon="📚",
    layout="wide"
)

st.title("📚 arXiv Searcher")

# Initialisation des composants
@st.cache_resource
def initialize_components(): 
    # Initialisation des embeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    chroma_client = chromadb.HttpClient(host=CHROMADB_HOST, port=8000)
    vectorstore = Chroma(embedding_function=embeddings, client=chroma_client)
    
    # Initialisation du LLM
    llm = HuggingFaceEndpoint(
        repo_id=LLM_MODEL,
        temperature=0.5,
        huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
        task="text-generation"
    )
    
    # Initialisation de l'agent
    prompt = hub.pull(AGENT_PROMPT)
    agent_executor = create_agent(vectorstore, llm, prompt)
    
    return vectorstore, agent_executor

# Initialisation des composants
vectorstore, agent_executor = initialize_components()
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# Création des onglets
tab1, tab2 = st.tabs(["🔍 Articles Search", "💬 Chat with arXiv Searcher"])

with tab1:
    st.header("Articles Search - API Powered") # TO DO : API SEARCH + cite API
    search_query = st.text_input("Search for articles!")
    if search_query:
        with st.spinner("Processing..."):
            results = retriever.invoke(search_query)
            for result in results:
                st.write(f"**Title:** {result.metadata['title']}")
                st.write(f"**Authors:** {result.metadata['authors']}")
                st.write(f"**Year:** {result.metadata['year']}")               
                st.write(f"**Abstract:** {result.page_content}")
                st.write(f"**Link: https://arxiv.org/abs/{result.id}**")
                st.write("---")

with tab2:
    st.header("Chat with the agent")
    
    # Initialisation de l'historique de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Affichage de l'historique des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Zone de saisie pour le message de l'utilisateur
    if prompt := st.chat_input("Ask your question..."):
        # Ajout du message de l'utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Génération de la réponse
        with st.chat_message("assistant"):
            with st.spinner("The agent is thinking..."):
                response = agent_executor.invoke({"input": prompt})
                st.markdown(response["output"])
                st.session_state.messages.append({"role": "assistant", "content": response["output"]}) 