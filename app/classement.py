"""
classement.py — Parkshare
Module logique classement : Top 20 + requêtes filtrées
"""

from database import get_connection


def get_top20() -> list:
    """
    Retourne le Top 20 des zones prioritaires trié par score décroissant.
    Utilisé par la route GET /api/top20
    """
    con = get_connection()
    df = con.execute("""
        SELECT
            rang,
            code_commune,
            nom_commune,
            region,
            ROUND(score_potentiel, 2)               AS score_potentiel,
            nb_coproprietes,
            syndic_dominant,
            ROUND(part_hlm * 100, 1)                AS part_hlm_pct,
            ROUND(indice_concentration_syndic * 100, 1) AS concentration_syndic_pct
        FROM kpi_top20
        ORDER BY rang
    """).df()
    con.close()
    return df.to_dict(orient="records")


def get_classement_filtre(
    region: str    = None,
    score_min: float = 0,
    score_max: float = 100,
    syndic: str    = None,
    limit: int     = 20
) -> list:
    """
    Retourne un classement filtré dynamiquement.
    Utilisé par la route GET /api/classement avec paramètres
    """
    con = get_connection()

    query = """
        SELECT
            ROW_NUMBER() OVER (ORDER BY score_potentiel DESC) AS rang,
            code_commune,
            nom_commune,
            region,
            ROUND(score_potentiel, 2)                   AS score_potentiel,
            nb_coproprietes,
            syndic_dominant,
            ROUND(part_hlm * 100, 1)                    AS part_hlm_pct,
            ROUND(indice_concentration_syndic * 100, 1) AS concentration_syndic_pct,
            score_category
        FROM communes
        WHERE score_potentiel BETWEEN ? AND ?
    """
    params = [score_min, score_max]

    if region and region != "Toutes":
        query += " AND region = ?"
        params.append(region)

    if syndic and syndic != "Tous":
        query += " AND syndic_dominant = ?"
        params.append(syndic)

    query += f" ORDER BY score_potentiel DESC LIMIT {limit}"

    df = con.execute(query, params).df()
    con.close()
    return df.to_dict(orient="records")


def get_resume_classement() -> dict:
    """
    Retourne un résumé du classement pour le storytelling.
    Utilisé par la route GET /api/classement/resume
    """
    con = get_connection()
    df = con.execute("""
        SELECT
            nom_commune,
            region,
            ROUND(score_potentiel, 2) AS score_potentiel,
            syndic_dominant,
            nb_coproprietes
        FROM communes
        ORDER BY score_potentiel DESC
        LIMIT 3
    """).df()
    con.close()

    top3 = df.to_dict(orient="records")
    return {
        "top1": top3[0] if len(top3) > 0 else None,
        "top2": top3[1] if len(top3) > 1 else None,
        "top3": top3[2] if len(top3) > 2 else None,
    }