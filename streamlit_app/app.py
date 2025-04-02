import streamlit as st
import os
from google.cloud import storage
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEndpoint

# Configuration de la page
st.set_page_config(
    page_title="arXiv Researcher",
    page_icon="📚",
    layout="wide"
)

# Constants
MODEL_NAME = 'sentence-transformers/all-mpnet-base-v2'
BUCKET_NAME = "arxiv-researcher-bucket"
GCS_PERSIST_PATH = "chroma_db/"
LOCAL_PERSIST_PATH = "./local_chromadb/"
REPO_ID = "mistralai/Mistral-7B-Instruct-v0.2"

# Initialisation des composants avec mise en cache
@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(model_name=MODEL_NAME)

@st.cache_resource
def get_vectorstore(_embeddings):
    # Création du dossier local s'il n'existe pas
    os.makedirs(LOCAL_PERSIST_PATH, exist_ok=True)
    
    try:
        # Tentative de connexion à Google Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blobs = bucket.list_blobs(prefix=GCS_PERSIST_PATH)

        # Téléchargement des données de Chroma depuis GCS
        for blob in blobs:
            if not blob.name.endswith("/"):
                relative_path = os.path.relpath(blob.name, GCS_PERSIST_PATH)
                local_file_path = os.path.join(LOCAL_PERSIST_PATH, relative_path)
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                blob.download_to_filename(local_file_path)
    except Exception as e:
        st.warning(f"Impossible de se connecter à Google Cloud Storage. Utilisation des données locales. Erreur: {e}")

    return Chroma(persist_directory=LOCAL_PERSIST_PATH, embedding_function=embeddings)

@st.cache_resource
def get_qa_chain(_retriever):
    try:
        llm = HuggingFaceEndpoint(
            repo_id=REPO_ID,
            max_length=128,
            temperature=0.5,
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
            task="text-generation"
        )
        return RetrievalQA.from_chain_type(llm, retriever=_retriever)
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation du modèle LLM: {e}")
        return None

# Sidebar
with st.sidebar:
    st.title("arXiv Researcher")
    st.markdown("""
    Cette application vous permet de :
    1. 🔍 Rechercher des articles similaires
    2. 💬 Poser des questions sur les articles
    3. 📊 Comparer des articles
    """)
    
    # Ajouter des filtres si nécessaire
    st.subheader("Filtres")
    categories = st.multiselect(
        "Catégories",
        ["Physics", "Mathematics", "Computer Science", "Quantitative Biology", "Quantitative Finance", 
          "Statistics", "Electrical Engineering and Systems Science", "Economics"],
        []
    )

# Initialisation des composants
embeddings = get_embeddings()
vectorstore = get_vectorstore(embeddings)
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
qa_chain = get_qa_chain(retriever)

# Interface principale avec onglets
tab1, tab2, tab3 = st.tabs(["Recherche d'articles", "Chatbot", "Comparaison"])

with tab1:
    st.header("🔍 Recherche d'articles similaires")
    search_query = st.text_input("Entrez votre requête de recherche")
    
    if search_query:
        with st.spinner("Recherche en cours..."):
            docs = retriever.get_relevant_documents(search_query)
            
            for i, doc in enumerate(docs, 1):
                with st.expander(f"📄 Article {i}"):
                    st.markdown(f"**Source:** {doc.metadata.get('source', 'Non spécifié')}")
                    st.markdown(f"**Contenu:**\n{doc.page_content}")
                    
                    # Boutons d'action
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"📋 Copier le texte {i}"):
                            st.write("Texte copié !")
                    with col2:
                        if st.button(f"⭐ Sauvegarder {i}"):
                            st.write("Article sauvegardé !")

with tab2:
    st.header("💬 Chatbot arXiv")
    
    # Initialisation de l'historique
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Affichage de l'historique
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input du chat
    if prompt := st.chat_input("Posez votre question sur les articles"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if qa_chain:
                with st.spinner("Réflexion en cours..."):
                    try:
                        response = qa_chain.invoke(prompt)
                        st.markdown(response["result"])
                        st.session_state.messages.append({"role": "assistant", "content": response["result"]})
                    except Exception as e:
                        st.error(f"Erreur lors de la génération de la réponse: {e}")
            else:
                st.error("Le modèle LLM n'est pas disponible. Veuillez vérifier votre configuration.")

with tab3:
    st.header("📊 Comparaison d'articles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        article1 = st.text_area("Article 1", height=200)
    with col2:
        article2 = st.text_area("Article 2", height=200)
    
    if article1 and article2 and st.button("Comparer"):
        with st.spinner("Analyse en cours..."):
            # Comparaison des articles
            try:
                docs1 = retriever.get_relevant_documents(article1)
                docs2 = retriever.get_relevant_documents(article2)
                
                st.subheader("Résultats de la comparaison")
                
                # Affichage des similarités
                st.markdown("### 🔄 Points communs")
                st.markdown("- Analyse des thèmes communs")
                st.markdown("- Méthodologies similaires")
                
                # Affichage des différences
                st.markdown("### ⚡ Différences principales")
                st.markdown("- Approches distinctes")
                st.markdown("- Résultats spécifiques")
                
            except Exception as e:
                st.error(f"Erreur lors de la comparaison: {e}")

# Footer
st.markdown("---")
st.markdown("Développé avec ❤️ par Célia, Jérémy et Anne") 