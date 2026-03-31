# Parkshare - Partie A : Développement API & Backend 🚀

Ce dossier `app` contient le code source de la **Partie A** (Développement de l'API et du Backend pour le dashboard Parkshare).

## 🏗️ Architecture Technique

Le projet repose sur la stack technique suivante :
* **FastAPI** : Framework Python ultra-rapide utilisé pour créer les routes API REST et servir les pages web (HTML/JS/CSS).
* **DuckDB** : Base de données analytique en mémoire / fichier local (`parkshare.duckdb`). Choisi pour sa performance sur les requêtes complexes de filtrage sans nécessiter de serveur lourd (Zero-Config).
* **Uvicorn** : Serveur ASGI pour exécuter l'application FastAPI.

## 📁 Structure du dossier `app`

* `main.py` : **Point d'entrée de l'application.** Il déclare l'API FastAPI, initialise la base de données au démarrage (`startup`) et expose l'ensemble des routes (endpoints) consommées par le frontend.
* `database.py` : Gère la connexion à DuckDB de manière dynamique et les requêtes de base (ex: filtres disponibles).
* `carte.py` : Logique métier pour générer les données géographiques (format GeoJSON) affichées sur la carte de l'interface. Intègre le filtrage en temps réel par région, score et syndic.
* `graphiques.py` : Exécute et met en forme les requêtes SQL permettant d'alimenter les graphiques (Scatter plots HLM vs Score, Distribution des scores, Tops syndics...).
* `classement.py` : Contient la logique pour la génération du classement détaillé (Top 20, Résumés) et la pagination des résultats du dashboard.
* `/static` & `/pages` : Fichiers statiques contenant le code Front-End (HTML, CSS, potentiellement le JS de cartographie/graphiques).
* `parkshare.duckdb` : Le fichier de base de données DuckDB consolidé.

## 🚀 Installation & Démarrage rapide

### 1. Prérequis
Assurez-vous d'avoir Python 3.9+ installé.
Placez votre terminal dans le répertoire `app/` ou le répertoire racine du projet et installez les dépendances :

```bash
pip install fastapi uvicorn duckdb
# ou via un fichier requirements.txt si présent à la racine :
# pip install -r requirements.txt
```

### 2. Lancer le serveur local

Depuis le dossier `app`, exécutez la commande suivante :

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

L'application démarre alors sur le port local : `http://localhost:8000/`.
Vous pourrez consulter le rapport narratif (racine) et le dashboard interactif sur `http://localhost:8000/dashboard`.

### 3. Documentation de l'API (Swagger UI)
Avantage majeur de FastAPI, la documentation de toutes les routes de l'API générées (`/api/communes`, `/api/geojson`, etc.) est générée automatiquement et accessible à l'adresse :
👉 `http://localhost:8000/docs`

## 🤝 Répartition / Historique Git

**Candidats de l'équipe :**
* Ashley
* Firas Bourguiba

*(Note pour l'oral, les fichiers `carte.py` et `graphiques.py` gèrent l'intelligence du filtrage et du formatage pour soulager le front et exploitent la puissance de DuckDB, assurant ainsi la fluidité du dashboard).*
