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

## Installation Terraform
1. Créer une copie du fichier de variable terraform :
```bash
cd iac
cp chroma.tfvars.example chroma.tfvars
```

2. Modifier le fichier pour remplacer les données :
```bash
nano chroma.tfvars
```

3. Initialiser le terraform :
```bash
terraform init
```

4. Planifier pour vérifier les informations puis Déployer :
```bash
terraform plan -var-file chroma.tfvars
terraform apply -var-file chroma.tfvars
```

5. Récupérer l'ip du chroma fraichement créer :
```bash
terraform output -raw chroma_instance_ip
```

6. Remplacer l'ip du chroma avec celui récupérer

7. Modifier les variables dans le fichier `iac/script/add_from_json.py`

8. Lancer la commande : 
```bash
gcloud dataproc jobs submit pyspark script/add_from_json.py \
    --cluster=<NOM_CLUSTER> \
    --region=<REGION_CLUSTER>
```
Vous avez à la fin une VM avec un chroma d'installer et un cluster dataproc

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