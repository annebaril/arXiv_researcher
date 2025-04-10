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
from arxivsearcher.trend_analysis import trend_analysis

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
    llm = init_chat_model(model=LLM_MODEL, model_provider=MODEL_PROVIDER, temperature=0)
    
    # Initialisation de l'agent
    prompt = hub.pull(AGENT_PROMPT)
    agent_executor = create_agent(vectorstore, llm, prompt)
    
    return vectorstore, agent_executor

# Initialisation des composants
vectorstore, agent_executor = initialize_components()
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# Création des onglets
tab1, tab2, tab3 = st.tabs(["🔍 Articles Search in API", "💬 Chat with arXiv Searcher", "📈 Trend Analysis"])

# Onglet 1 - Articles Search
with tab1:
    st.header("Articles Search in arXiv API")

    # Zone de recherche 
    search_query = st.text_input("Search for articles!")

    # Ajout d'un état pour stocker les résultats
    st.session_state.search_results = []  

    # Conteneur pour les résultats
    results_container = st.empty()

    # Afficher uniquement le spinner pendant le chargement
    if search_query:
        with st.spinner("Processing..."):
            results = search_arxiv(search_query)
            st.session_state.search_results = results  # Stockage des résultats dans la session

        # Affichage des résultats uniquement s'ils ont été chargés
        if st.session_state.search_results:
            with results_container.container():
                l = len(st.session_state.search_results)
                for i, result in enumerate(st.session_state.search_results):
                    st.write(f"**Title: {result['title']}**")
                    st.write(f"**Authors:** {result['authors'][0]}")
                    st.write(f"**Year:** {result['year']}")               
                    st.write(f"**Abstract:** {result['summary']}")
                    st.write(f"**Link: {result['url']}**")
                    if i != l - 1:
                        st.write('---')
    
        else:
            st.warning("No results found. Please try a different query.")

# Onglet 2 - Chat
with tab2:
    # Sticky input style
    st.markdown("""
        <style>
        .stChatInput {
            position: fixed;
            bottom: 30px;
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

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hello! I'm your arXiv research assistant. I can help you find and understand research papers. What would you like to know?"
        }]
    
    # Afficher l'historique
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Ajouter nouvelle question
    user_input = st.chat_input("Ask a question")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.spinner("The agent is thinking..."):
            response = agent_executor.invoke({"input": user_input})
            with st.chat_message("assistant"):
                formatted_response = response["output"]
                formatted_response = formatted_response.replace("Title:", "**Title:**")
                formatted_response = formatted_response.replace("Abstract:", "**Abstract:**")
                st.markdown(formatted_response)
            st.session_state.messages.append({"role": "assistant", "content": formatted_response})


# Onglet 3 - Trend Analysis
with tab3:
    st.header("📈 Trend Analysis")
    
    # Création d'une colonne centrale
    col_center = st.columns([1, 2, 1])[1]  # [1, 2, 1] crée 3 colonnes, la colonne du milieu est 2 fois plus large
    
    with col_center:
        # Champ de recherche pour le topic
        topic = st.text_input("Enter a topic to analyze trends")
        
        # Sélecteurs de dates
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.slider("Start Year", 1991, 2025, 2010)
        with col2:
            end_year = st.slider("End Year", 1991, 2025, 2023)
        
        # Vérification que end_year >= start_year
        if end_year <= start_year:
            st.error("End year must be greater than or equal to start year")
        else:
            if topic:
                with st.spinner("Analyzing trends..."):
                    fig = trend_analysis(vectorstore, topic, start_year, end_year)
                    st.pyplot(fig)


# --- Footer affiché partout ---
#st.markdown("""---""")
st.markdown("""
    <style>
    footer {
        visibility: hidden;
    }
    .footer-fix {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        text-align: center;
        padding: 10px;
        font-size: 0.9rem;
        background: #f9f9f9;
        border-top: 1px solid #eaeaea;
    }
    </style>
    <div class="footer-fix">
        🔗 Powered by <a href="https://arxiv.org/help/api" target="_blank">arXiv API</a> and <a href="https://www.trychroma.com/" target="_blank">ChromaDB</a>
    </div>
""", unsafe_allow_html=True)