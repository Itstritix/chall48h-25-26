# Parkshare — Étude de marché par la donnée

Challenge 48h · Mars 2026

Outil d'analyse géographique pour identifier les zones à fort potentiel
commercial pour Parkshare — plateforme de partage de places de stationnement
en copropriété.

---

## Structure du repo

```
/
├── data/              # Partie Data — collecte, nettoyage, KPIs
├── app/               # Partie Dev  — base de données + dashboard
├── infra/             # Partie Infra — Docker, reverse proxy, déploiement
├── .env.example       # Variables d'environnement nécessaires (sans valeurs)
├── .gitignore
└── README.md
```

---

## Équipe

| Profil | Responsabilité |
|---|---|
| **Data** | Collecte sources, nettoyage, calcul des KPIs, scoring |
| **Dev** | Base DuckDB, API FastAPI, dashboard interactif |
| **Infra** | Containerisation Docker, déploiement VPS, reverse proxy |

---

## Lancement rapide

### 1. Cloner le repo
```bash
git clone <url-du-repo>
cd parkshare
```

### 2. Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec les vraies valeurs
```

### 3. Lancer avec Docker (recommandé)
```bash
cd infra
docker-compose up --build
```

### 4. Ou lancer le dashboard seul (développement)
```bash
cd app
pip install -r requirements.txt
python main.py
```

Accès : `http://localhost:8000`

---

## Documentation détaillée

- [`/data/README.md`](data/README.md) — sources de données, pipeline, KPIs
- [`/app/README.md`](app/README.md) — schéma BDD, routes API, utilisation dashboard
- [`/infra/README.md`](infra/README.md) — déploiement, variables d'environnement, accès distant

---

## Sources de données

| Source | Contenu | URL |
|---|---|---|
| Registre national des copropriétés | Nb lots, syndic, stationnement | data.gouv.fr |
| RPLS — Bailleurs sociaux | OPH/ESH par commune | data.gouv.fr |
| INSEE — Recensement Population | Motorisation, logements collectifs | insee.fr |
| IGN — Géographie communes | Contours GeoJSON | geoservices.ign.fr |

---

## Stack technique

| Couche | Technologie |
|---|---|
| Données | Python, Pandas, DuckDB |
| API | FastAPI, Uvicorn |
| Frontend | HTML / CSS / JS, Leaflet.js, Chart.js |
| Infra | Docker, Docker Compose, Nginx |