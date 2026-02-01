Fact-Checker Automatique pour Scripts Notion

Ce projet est une automatisation permettant de vérifier la véracité d'un script stocké dans une base de données Notion.
N'ayant pas accès à votre base, j'ai créé la mienne avec les colonnes suivantes :

Script (nom du fichier)
Contenu (texte à vérifier)
Fact-checking (status : To verify / Verified / Error)
Source (lien cliquable)
Explanation (explication du verdict)

Première étape : Récupérer les clés API
Toutes les clés API nécessaires sont stockées dans un fichier .env (qui est dans .gitignore pour éviter toute fuite).

Les clés utilisées :

Notion API : permet de récupérer les informations et de mettre à jour le statut d’une page.
Groq API : N'ayant pas les versions payantes de Claude ou GPT, j'ai dû trouver un moyen pour contourner ça. Groq me permet avec une seule clé API d'avoir accès à plusieurs modèles d'IA. J'ai utilisé :

MODEL1 = "llama-3.1-8b-instant"
MODEL2 = "openai/gpt-oss-120b"

Serper API : Petit souci que j'ai rencontré : la génération de lien pour les sources. J'ai donc utilisé Serper qui me permet en donnant des mots-clés de récupérer des liens.

Configuration du .env :
NOTION_API_KEY=secret_xxxxx
DATABASE_ID=xxxxx
GROQ_API_KEY=gsk_xxxxx
SERPER_API_KEY=xxxxx

Deuxième étape : notion.py
Ce fichier gère les interactions avec Notion. Il utilise la clé API et l’ID de la base de données pour récupérer et mettre à jour les pages.

Les fonctions :

get_page_to_verify() : récupère les pages dont le statut est To verify.
get_page_content() : récupère uniquement le contenu à fact-checker.
updates_page_status() : met à jour le statut, la source et l’explication d’une page.

Troisième étape : agents.py
Tout d'abord on choisit ses agents IA. Dans notre cas Llama et ChatGPT. On met la température à une valeur très faible pour éviter toute hallucination.

Les fonctions importantes :

_clean_json() : formate la réponse des IA en JSON.
check_ai() : crée le prompt et récupère les informations au format attendu. Voir la doc du prompting de chaque IA peut être très intéressant pour donner le meilleur prompt.
consensus() : compare les réponses des deux modèles et calcule la confiance ; si accord, confiance élevée, sinon uncertain.
search_web_for_source() : génère un lien web en fonction de mots-clés grâce à l’API Serper.

Quatrième étape : main.py
Ce fichier exécute le fact-checker. Une boucle infinie qui effectue un polling toutes les 30 secondes pour vérifier de nouvelles pages.

Le fonctionnement :

Récupère les pages avec statut "To verify"
Pour chaque page :

Récupère le contenu
Lance les 2 agents IA
Compare leurs résultats (consensus)
Cherche une source web
Met à jour Notion avec le verdict, la source et l'explication

Pour une version production, il serait préférable d’utiliser un webhook ou des outils comme n8n ou Zapier pour automatiser le processus.


INSTALLATION

# Clone le projet
git clone ton-repo

# Installe les dépendances
pip install -r requirements.txt

# Configure ton .env

# Lance le fact-checker
PYTHONPATH=. python -m app.main