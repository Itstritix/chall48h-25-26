"""
graphiques.py — Parkshare
Module logique graphiques : agrégats + données pour Chart.js
"""

import os
from database import get_connection

# Chemin vers le fichier KPI3 livré par Data
KPI3_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "kpi3_concentration_syndic.csv")
KPI3_MOCK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "kpi3_concentration_syndic_MOCK.csv")


def get_stats_par_region() -> list:
    """Score moyen par région pour le graphique barres horizontales."""
    con = get_connection()
    df = con.execute("""
        SELECT
            region,
            ROUND(AVG(score_potentiel), 2)                  AS score_moyen,
            COUNT(*)                                         AS nb_communes,
            SUM(nb_coproprietes)                            AS nb_coproprietes_total,
            ROUND(AVG(part_hlm) * 100, 1)                   AS part_hlm_moyenne_pct,
            ROUND(AVG(indice_concentration_syndic)*100, 1)  AS indice_syndic_moyen_pct
        FROM communes
        WHERE region IS NOT NULL AND region != 'non connu'
        GROUP BY region
        ORDER BY score_moyen DESC
    """).df()
    con.close()
    return df.to_dict(orient="records")


def get_scatter_hlm_score() -> list:
    """
    Scatter HLM vs Score — échantillon fixe sans USING SAMPLE
    (compatibilité toutes versions DuckDB)
    """
    con = get_connection()
    df = con.execute("""
        SELECT
            nom_commune,
            region,
            ROUND(part_hlm * 100, 1)     AS part_hlm_pct,
            ROUND(score_potentiel, 2)     AS score_potentiel,
            score_category,
            nb_coproprietes
        FROM communes
        WHERE part_hlm IS NOT NULL
          AND score_potentiel IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 300
    """).df()
    con.close()
    return df.to_dict(orient="records")


def get_concentration_syndic_top15() -> list:
    """
    KPI 3 — Concentration syndic par département.
    Utilise le fichier livré par Data : kpi3_concentration_syndic.csv
    Si le fichier n'existe pas encore, retourne les données de fallback
    depuis la table communes (score potentiel Top 15).
    """
    # Chemin du fichier Data
    path = KPI3_PATH if os.path.exists(KPI3_PATH) else (KPI3_MOCK_PATH if os.path.exists(KPI3_MOCK_PATH) else None)

    if path:
        # Fichier livré par Data — colonnes réelles :
        # code_departement, nom_departement, nb_copros_total,
        # syndic_dominant, nb_copros_syndic, concentration_pct
        con = get_connection()
        df = con.execute(f"""
            SELECT
                nom_departement                              AS nom_commune,
                ''                                           AS region,
                syndic_dominant,
                CAST(nb_copros_total AS INTEGER)             AS nb_coproprietes,
                ROUND(CAST(concentration_pct AS DOUBLE), 1)  AS concentration_pct,
                CAST(nb_copros_syndic AS INTEGER)            AS nb_copros_syndic
            FROM read_csv_auto('{path}', header=True)
            ORDER BY concentration_pct DESC
            LIMIT 15
        """).df()
        con.close()
        return df.to_dict(orient="records")

    else:
        # Fallback — Data n'a pas encore livré le fichier
        # On retourne le Top 15 communes par score avec syndic
        con = get_connection()
        df = con.execute("""
            SELECT
                nom_commune,
                region,
                syndic_dominant,
                nb_coproprietes,
                ROUND(score_potentiel, 2)    AS score_potentiel,
                ROUND(taille_moy_copro, 1)  AS taille_moy_copro
            FROM communes
            WHERE syndic_dominant IS NOT NULL
              AND nb_coproprietes >= 10
              AND score_potentiel IS NOT NULL
            ORDER BY score_potentiel DESC
            LIMIT 15
        """).df()
        con.close()
        return df.to_dict(orient="records")


def get_kpi3_mode() -> str:
    """
    Retourne le mode actuel du KPI 3 :
    'departement' si Data a livré le fichier, 'fallback' sinon.
    Utilisé par le dashboard pour adapter le titre et le tooltip.
    """
    if os.path.exists(KPI3_PATH):
        return "departement"
    elif os.path.exists(KPI3_MOCK_PATH):
        return "mock"
    return "fallback"


def get_distribution_scores() -> list:
    """Distribution des scores par tranche de 10 points."""
    con = get_connection()
    df = con.execute("""
        SELECT
            FLOOR(score_potentiel / 10) * 10      AS tranche_min,
            FLOOR(score_potentiel / 10) * 10 + 10 AS tranche_max,
            COUNT(*)                               AS nb_communes
        FROM communes
        WHERE score_potentiel IS NOT NULL
        GROUP BY FLOOR(score_potentiel / 10)
        ORDER BY tranche_min
    """).df()
    con.close()
    return df.to_dict(orient="records")


def get_correlation_matrix() -> dict:
    """
    Bonus 2 — Matrice de corrélation entre les 5 variables du scoring.
    Retourne les valeurs de corrélation pour la heatmap Chart.js.
    """
    con = get_connection()
    df = con.execute("""
        SELECT
            taille_moy_copro,
            taux_motorisation,
            part_appartements,
            indice_concentration_syndic,
            part_hlm,
            score_potentiel
        FROM communes
        WHERE taille_moy_copro IS NOT NULL
          AND taux_motorisation IS NOT NULL
          AND part_appartements IS NOT NULL
          AND indice_concentration_syndic IS NOT NULL
          AND part_hlm IS NOT NULL
          AND score_potentiel IS NOT NULL
    """).df()
    con.close()

    # Calcul de la matrice de corrélation avec pandas
    corr = df.corr(numeric_only=True).round(2)

    labels = [
        'Taille copros',
        'Motorisation',
        'Logements collectifs',
        'Concentration syndic',
        'Part HLM',
        'Score potentiel'
    ]

    # Construire la liste de points {x, y, v} pour Chart.js matrix
    data = []
    cols = corr.columns.tolist()
    for i, row in enumerate(cols):
        for j, col in enumerate(cols):
            data.append({
                'x': j,
                'y': i,
                'v': float(corr.loc[row, col])
            })

    return {
        'labels': labels,
        'data': data
    }