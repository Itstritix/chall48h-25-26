"""
carte.py — Parkshare
Module logique carte : filtrage GeoJSON + formatage pour Leaflet
"""

import json
import os
from database import get_connection

GEOJSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "communes_scored.geojson")


def get_geojson_complet() -> dict:
    """
    Charge et retourne le GeoJSON complet depuis le fichier.
    Utilisé par la route GET /api/geojson
    """
    if not os.path.exists(GEOJSON_PATH):
        raise FileNotFoundError(f"GeoJSON introuvable : {GEOJSON_PATH}")

    with open(GEOJSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    return data


def get_geojson_filtre(
    region: str   = None,
    score_min: float = 0,
    score_max: float = 100,
    syndic: str   = None
) -> dict:
    """
    Retourne le GeoJSON filtré selon les paramètres du dashboard.
    Les filtres sont appliqués sur les properties de chaque feature.
    Utilisé par la route GET /api/geojson/filtre
    """
    data = get_geojson_complet()

    features_filtrees = []
    for feature in data["features"]:
        props = feature.get("properties", {})
        score = props.get("score_potentiel", 0) or 0

        # Filtre score
        if not (score_min <= score <= score_max):
            continue

        # Filtre région
        if region and region != "Toutes":
            if props.get("region") != region:
                continue

        # Filtre syndic
        if syndic and syndic != "Tous":
            if props.get("syndic_dominant") != syndic:
                continue

        features_filtrees.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features_filtrees
    }


def get_couleur_score(score: float) -> str:
    """
    Retourne la couleur hex selon le score.
    Utilisé côté Python pour pré-calculer les couleurs si besoin.
    """
    if score >= 66:
        return "#10b981"   # vert — zone prioritaire
    elif score >= 33:
        return "#f59e0b"   # orange — zone moyenne
    else:
        return "#ef4444"   # rouge — zone faible


def get_stats_carte() -> dict:
    """
    Retourne les statistiques globales pour la légende de la carte.
    Utilisé par la route GET /api/carte/stats
    """
    con = get_connection()
    stats = con.execute("""
        SELECT
            COUNT(*)                            AS total_communes,
            ROUND(AVG(score_potentiel), 2)      AS score_moyen,
            ROUND(MIN(score_potentiel), 2)      AS score_min,
            ROUND(MAX(score_potentiel), 2)      AS score_max,
            COUNT(*) FILTER (WHERE score_potentiel >= 66) AS zones_elevees,
            COUNT(*) FILTER (WHERE score_potentiel >= 33
                             AND score_potentiel < 66)    AS zones_moyennes,
            COUNT(*) FILTER (WHERE score_potentiel < 33)  AS zones_faibles
        FROM communes
    """).df()
    con.close()
    return stats.to_dict(orient="records")[0]