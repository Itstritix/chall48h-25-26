"""
graphiques.py — Parkshare
Module logique graphiques : agrégats + données pour Chart.js
"""

from database import get_connection


def get_stats_par_region() -> list:
    """
    Agrégats par région pour le graphique barres horizontales.
    Utilisé par la route GET /api/stats
    """
    con = get_connection()
    df = con.execute("""
        SELECT
            region,
            ROUND(AVG(score_potentiel), 2)              AS score_moyen,
            COUNT(*)                                     AS nb_communes,
            SUM(nb_coproprietes)                        AS nb_coproprietes_total,
            ROUND(AVG(part_hlm) * 100, 1)               AS part_hlm_moyenne_pct,
            ROUND(AVG(indice_concentration_syndic)*100, 1) AS indice_syndic_moyen_pct
        FROM communes
        WHERE region IS NOT NULL AND region != 'non connu'
        GROUP BY region
        ORDER BY score_moyen DESC
    """).df()
    con.close()
    return df.to_dict(orient="records")


def get_scatter_hlm_score() -> list:
    """
    Données pour le scatter plot Part HLM vs Score potentiel.
    Échantillonné pour la performance (max 300 points).
    Utilisé par la route GET /api/graphiques/scatter
    """
    con = get_connection()
    df = con.execute("""
        SELECT
            nom_commune,
            region,
            ROUND(part_hlm * 100, 1)        AS part_hlm_pct,
            ROUND(score_potentiel, 2)        AS score_potentiel,
            score_category,
            nb_coproprietes
        FROM communes
        WHERE part_hlm IS NOT NULL
          AND score_potentiel IS NOT NULL
        USING SAMPLE 300
    """).df()
    con.close()
    return df.to_dict(orient="records")


def get_concentration_syndic_top15() -> list:
    """
    Top 15 communes par indice de concentration syndic.
    Utilisé par la route GET /api/graphiques/syndic
    """
    con = get_connection()
    df = con.execute("""
        SELECT
            nom_commune,
            region,
            syndic_dominant,
            ROUND(indice_concentration_syndic * 100, 1) AS concentration_pct,
            ROUND(score_potentiel, 2)                   AS score_potentiel
        FROM communes
        WHERE indice_concentration_syndic IS NOT NULL
          AND syndic_dominant IS NOT NULL
        ORDER BY indice_concentration_syndic DESC
        LIMIT 15
    """).df()
    con.close()
    return df.to_dict(orient="records")


def get_distribution_scores() -> list:
    """
    Distribution des scores par tranche de 10 points.
    Utilisé pour l'histogramme de distribution.
    Utilisé par la route GET /api/graphiques/distribution
    """
    con = get_connection()
    df = con.execute("""
        SELECT
            FLOOR(score_potentiel / 10) * 10   AS tranche_min,
            FLOOR(score_potentiel / 10) * 10 + 10 AS tranche_max,
            COUNT(*)                            AS nb_communes
        FROM communes
        WHERE score_potentiel IS NOT NULL
        GROUP BY FLOOR(score_potentiel / 10)
        ORDER BY tranche_min
    """).df()
    con.close()
    return df.to_dict(orient="records")