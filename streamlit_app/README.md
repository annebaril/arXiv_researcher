# arXiv Researcher - Application Streamlit

Cette application Streamlit permet de rechercher et d'interagir avec une base de données d'articles arXiv.

## Fonctionnalités

1. 🔍 **Recherche d'articles**
   - Recherche sémantique dans la base d'articles
   - Affichage des résultats pertinents
   - Possibilité de sauvegarder les articles intéressants

2. 💬 **Chatbot**
   - Posez des questions sur les articles
   - Obtenez des réponses contextuelles
   - Historique des conversations

3. 📊 **Comparaison d'articles**
   - Comparez deux articles
   - Analyse des similarités et différences
   - Visualisation des résultats

## Installation

1. Créez un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurez les variables d'environnement :
```bash
export HUGGINGFACEHUB_API_TOKEN="votre_token"
export GOOGLE_APPLICATION_CREDENTIALS="chemin/vers/credentials.json"
```

## Utilisation

1. Lancez l'application :
```bash
streamlit run app.py
```

2. Ouvrez votre navigateur à l'adresse : http://localhost:8501

## Structure des données

L'application utilise une base de données vectorielle Chroma pour stocker et rechercher les articles. Les données sont stockées dans Google Cloud Storage et sont synchronisées localement lors du lancement de l'application.

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request. 