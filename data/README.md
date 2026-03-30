# Partie Data — Parkshare Challenge 48h

## Objectif

Collecter, nettoyer et analyser des données ouvertes pour produire des KPIs
identifiant les zones à fort potentiel commercial pour Parkshare.

La mission est de fournir à l'équipe commerciale de Parkshare un scoring
géographique par commune, permettant de prioriser les actions de prospection
auprès des syndics et bailleurs.

---

## Structure des fichiers

```
data/
├── raw/
│   ├── registre_coproprietes.csv      # RNIC T4 2025 — 437 Mo
│   ├── rnic_dictionnaire_donnees.csv  # Documentation colonnes RNIC
│   ├── insee_logement.zip             # Base INSEE logement 2020
│   └── communes_geometries.geojson    # Contours communes IGN 2024
├── processed/
│   ├── communes_scored.csv            # Données scorées (import BDD Dev)
│   ├── communes_scored.geojson        # Données géolocalisées (carte Dev)
│   ├── kpis_graphiques.png            # Graphiques KPI 1, 2, 3
│   └── kpi4_hlm.png                   # Graphique KPI 4
├── notebooks/
│   └── pipeline.ipynb                 # Pipeline complet reproductible
├── requirements.txt
└── README.md
```

---

## Sources de données

| Source | Description | URL |
|--------|-------------|-----|
| Registre National des Copropriétés (RNIC) | Syndic, nb lots, adresse — 626 702 copropriétés | https://www.data.gouv.fr/datasets/registre-national-dimmatriculation-des-coproprietes |
| INSEE — Base logement 2020 | Motorisation, logements collectifs, HLM par IRIS | https://www.insee.fr/fr/statistiques/7704078 |
| Contours administratifs IGN 2024 | Géométries des communes françaises | https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2024/geojson/communes-100m.geojson |

---

## Reproduire le pipeline

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Vérifier les fichiers bruts
Les fichiers doivent être présents dans `raw/` avant de lancer le notebook.
La cellule 1 vérifie automatiquement leur présence.

### 3. Lancer le notebook
```bash
jupyter notebook notebooks/pipeline.ipynb
```
Exécuter toutes les cellules dans l'ordre (Cell > Run All).

---

## KPIs produits

### KPI 1 — Score de potentiel commercial (obligatoire)

Score de 0 à 100 par commune par normalisation Min-Max + moyenne pondérée.

| Variable | Colonne | Poids | Justification |
|----------|---------|-------|---------------|
| Taille moyenne des copropriétés | `taille_moy_copro` | 25% | Plus la copro est grande, plus le contrat génère de valeur |
| Taux de motorisation | `taux_motorisation` | 20% | Sans voiture, le produit n'a pas de valeur |
| Part logements collectifs | `part_appartements` | 20% | Les maisons individuelles sont hors cible |
| Indice de concentration syndic | `indice_concentration_syndic` | 20% | Effet multiplicateur — un syndic dominant = plusieurs copros |
| Part logements sociaux HLM | `part_hlm` | 15% | Bailleurs sociaux = déploiement sans vote en AG |

**Résultats :** 13 061 communes scorées — min 7.67 / moy 27.18 / max 59.30

### KPI 2 — Classement Top 20 zones prioritaires (obligatoire)

Classement des 20 communes avec le score le plus élevé.
Directement actionnable par une équipe commerciale.

### KPI 3 — Indice de concentration syndic (choix équipe)

Part des copropriétés d'une commune gérées par le même syndic dominant.
```
indice = nb_copros_syndic_dominant / nb_copros_total_commune
```
Un indice de 0.80 = un seul rendez-vous commercial peut couvrir 80% des copros.
Calculé sur les communes avec 5+ copropriétés.

### KPI 4 — Part de logements à déploiement sans friction (choix équipe)

Part des logements HLM dans la commune.
```
part_hlm = nb_logements_hlm / nb_residences_principales
```
Les bailleurs sociaux (OPH, ESH) décident seuls — pas de vote en AG nécessaire.
Ce KPI mesure la vitesse potentielle de déploiement.

---

## Limites et biais connus

**1. Couverture partielle du registre**
Le RNIC est rempli de façon déclarative. Couverture estimée à 2/3 des
copropriétés françaises. Les petites copropriétés avec syndic bénévole
sont sous-représentées.

**2. Données INSEE pondérées**
Les chiffres INSEE utilisent des coefficients de pondération statistique
(valeurs décimales). Impact négligeable sur les ratios calculés.

**3. Choix des pondérations**
Les poids reflètent une logique métier construite à partir de l'analyse
du modèle commercial de Parkshare. Une analyse de sensibilité pourrait
tester d'autres pondérations.

**4. Normalisation Min-Max**
La normalisation est sensible aux valeurs extrêmes. Paris avec 9 636
copropriétés tire l'échelle vers le haut. Les communes moyennes peuvent
être sous-estimées. Ce point est à mentionner à l'oral.

---

## Schéma du fichier de livraison

| Colonne | Type | Description |
|---------|------|-------------|
| `code_commune` | str | Code INSEE 5 caractères — clé de jointure |
| `nom_commune` | str | Nom de la commune |
| `departement` | str | Département |
| `region` | str | Région |
| `score_potentiel` | float | Score final 0-100 |
| `nb_coproprietes` | int | Nb copropriétés immatriculées |
| `taille_moy_copro` | float | Nb moyen de lots par copropriété |
| `taux_motorisation` | float | Part ménages avec voiture (0-1) |
| `part_appartements` | float | Part résidences en appartement (0-1) |
| `indice_concentration_syndic` | float | Part copros sous syndic dominant (0-1) |
| `part_hlm` | float | Part logements HLM (0-1) |
| `syndic_dominant` | str | Syndic le plus présent dans la commune |
| `nb_lots_stationnement` | float | Nb total lots de stationnement déclarés |

---

*Challenge 48h Parkshare — Usage pédagogique — Mars 2026*
