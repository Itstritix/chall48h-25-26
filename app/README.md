# Parkshare — Dashboard `/app/`

Application web interactive connectée à la base DuckDB pour visualiser
les résultats de l'étude de marché Parkshare.

---

## Stack technique

| Composant | Technologie |
|---|---|
| Serveur API | FastAPI + Uvicorn |
| Base de données | DuckDB |
| Carte interactive | Leaflet.js |
| Graphiques | Chart.js |
| Frontend | HTML / CSS / JS vanilla |

---

## Structure des fichiers

```
/app/
├── main.py           # Serveur FastAPI — routes API + pages HTML
├── database.py       # DuckDB — création tables + requêtes
├── carte.py          # Logique carte : GeoJSON + filtres
├── classement.py     # Logique Top 20 + classement filtré
├── graphiques.py     # Logique agrégats + données graphiques
├── static/
│   ├── rapport.html  # Page storytelling (accueil)
│   ├── index.html    # Dashboard interactif
│   ├── style.css     # Styles partagés
│   └── app.js        # Logique JS (carte, graphiques, filtres)
├── requirements.txt
└── README.md
```

---

## Schéma de la base de données

### Table 1 — `raw_communes` (données brutes)
Données telles que reçues de l'équipe Data, sans transformation.

| Colonne | Type | Description |
|---|---|---|
| `code_commune` | TEXT (PK) | Code INSEE commune |
| `nom_commune` | TEXT | Nom de la commune |
| `departement` | TEXT | Département |
| `region` | TEXT | Région |
| `score_potentiel` | DOUBLE | Score 0–100 |
| `nb_coproprietes` | INTEGER | Nombre de copropriétés |
| `taille_moy_copro` | DOUBLE | Taille moyenne en lots |
| `taux_motorisation` | DOUBLE | Nb voitures / nb ménages |
| `part_appartements` | DOUBLE | Part logements collectifs (0–1) |
| `indice_concentration_syndic` | DOUBLE | Concentration syndic dominant (0–1) |
| `part_hlm` | DOUBLE | Part logements OPH/ESH (0–1) |
| `syndic_dominant` | TEXT | Nom du syndic majoritaire |
| `nb_lots_stationnement` | INTEGER | Nombre de lots de stationnement |

### Table 2 — `communes` (données transformées)
Données nettoyées + colonnes calculées. C'est sur cette table que les KPIs sont calculés.

Colonnes supplémentaires par rapport à `raw_communes` :

| Colonne | Type | Description |
|---|---|---|
| `score_category` | TEXT | `'Élevé'` / `'Moyen'` / `'Faible'` |
| `rang_national` | INTEGER | Classement par score décroissant |

### Table 3a — `kpi_top20` (KPI agrégé)
Top 20 zones prioritaires prêtes à l'affichage.

| Colonne | Type | Description |
|---|---|---|
| `rang` | INTEGER | Classement 1–20 |
| `code_commune` | TEXT | Code INSEE |
| `nom_commune` | TEXT | Nom |
| `region` | TEXT | Région |
| `score_potentiel` | DOUBLE | Score |
| `nb_coproprietes` | INTEGER | Nb copros |
| `syndic_dominant` | TEXT | Syndic |
| `part_hlm_pct` | DOUBLE | Part HLM en % |
| `concentration_syndic_pct` | DOUBLE | Concentration syndic en % |

### Table 3b — `kpi_par_region` (KPI agrégé)
Agrégats par région pour les graphiques du dashboard.

| Colonne | Type | Description |
|---|---|---|
| `region` | TEXT (PK) | Nom de la région |
| `score_moyen` | DOUBLE | Score moyen des communes |
| `nb_communes` | INTEGER | Nombre de communes |
| `nb_coproprietes_total` | INTEGER | Total copropriétés |
| `part_hlm_moyenne_pct` | DOUBLE | Part HLM moyenne en % |
| `indice_syndic_moyen_pct` | DOUBLE | Indice syndic moyen en % |

---

## Routes API

| Méthode | Route | Description |
|---|---|---|
| GET | `/` | Page storytelling `rapport.html` |
| GET | `/dashboard` | Dashboard interactif `index.html` |
| GET | `/api/communes` | Communes avec filtres dynamiques |
| GET | `/api/geojson` | GeoJSON complet pour la carte |
| GET | `/api/geojson/filtre` | GeoJSON filtré |
| GET | `/api/carte/stats` | Statistiques globales carte |
| GET | `/api/top20` | Top 20 zones prioritaires |
| GET | `/api/classement` | Classement filtré dynamiquement |
| GET | `/api/classement/resume` | Top 3 pour le storytelling |
| GET | `/api/stats` | Agrégats par région |
| GET | `/api/graphiques/scatter` | Données scatter HLM vs score |
| GET | `/api/graphiques/syndic` | Concentration syndic Top 15 |
| GET | `/api/graphiques/distribution` | Distribution des scores |
| GET | `/api/filtres` | Valeurs disponibles pour les dropdowns |

**Paramètres de filtre disponibles** sur `/api/communes` et `/api/classement` :

| Paramètre | Type | Défaut | Description |
|---|---|---|---|
| `region` | string | null | Filtrer par région |
| `score_min` | float | 0 | Score minimum |
| `score_max` | float | 100 | Score maximum |
| `syndic` | string | null | Filtrer par syndic dominant |

---

## Installation et lancement

### Prérequis
- Python 3.10+
- Les fichiers `communes_scored.csv` et `communes_scored.geojson` dans `../data/processed/`

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Lancement du serveur

```bash
cd app
python main.py
```

Le serveur démarre sur `http://localhost:8000`.

Au premier lancement, `database.py` initialise automatiquement la base DuckDB
en chargeant le CSV et en créant les 4 tables.

### Accès

| URL | Page |
|---|---|
| `http://localhost:8000/` | Rapport storytelling |
| `http://localhost:8000/dashboard` | Dashboard interactif |
| `http://localhost:8000/docs` | Documentation API automatique (FastAPI) |

---

## Fonctionnalités du dashboard

- **Carte choroplèthe** : communes colorées par score potentiel, tooltip au survol
- **Filtres dynamiques** : région, score min/max, syndic dominant — tout se met à jour en temps réel
- **Top 20 tableau** : classement avec badges colorés, scroll, filtrable
- **4 graphiques KPIs** :
  - Distribution des scores (histogramme)
  - Score moyen par région (barres horizontales)
  - Concentration syndic Top 15 (barres)
  - Part HLM vs Score potentiel (scatter plot)