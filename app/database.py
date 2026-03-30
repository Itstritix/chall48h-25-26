"""
database.py — Parkshare
Connexion DuckDB + création des 3 tables + chargement des données CSV
"""

import duckdb
import os

# Chemin vers la base de données et les données
DB_PATH = os.path.join(os.path.dirname(__file__), "parkshare.duckdb")
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "communes_scored.csv")


def get_connection():
    """Retourne une connexion à la base DuckDB."""
    return duckdb.connect(DB_PATH)


def init_db():
    """
    Initialise la base de données :
    - Crée les 3 tables (brutes, transformées, KPIs)
    - Charge le CSV dans la table brute
    - Peuple les tables transformées et KPIs
    """
    con = get_connection()

   
    # TABLE 1 — Données brutes (telles que reçues de Data)
   
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_communes (
            code_commune                TEXT PRIMARY KEY,
            nom_commune                 TEXT,
            departement                 TEXT,
            region                      TEXT,
            score_potentiel             DOUBLE,
            nb_coproprietes             INTEGER,
            taille_moy_copro            DOUBLE,
            taux_motorisation           DOUBLE,
            part_appartements           DOUBLE,
            indice_concentration_syndic DOUBLE,
            part_hlm                    DOUBLE,
            syndic_dominant             TEXT,
            nb_lots_stationnement       INTEGER
        )
    """)

    # Charge le CSV dans la table brute (seulement si vide)
    count = con.execute("SELECT COUNT(*) FROM raw_communes").fetchone()[0]
    if count == 0:
        con.execute(f"""
            INSERT INTO raw_communes
            SELECT
                CAST(code_commune AS TEXT),
                nom_commune,
                departement,
                region,
                score_potentiel,
                nb_coproprietes,
                taille_moy_copro,
                taux_motorisation,
                part_appartements,
                indice_concentration_syndic,
                part_hlm,
                syndic_dominant,
                nb_lots_stationnement
            FROM read_csv_auto('{CSV_PATH}', header=True)
        """)
        print(f"✅ CSV chargé dans raw_communes")
    else:
        print(f"ℹ️  raw_communes déjà peuplée ({count} lignes)")

    
    # TABLE 2 — Données transformées (nettoyées + colonnes calculées)

    con.execute("""
        CREATE TABLE IF NOT EXISTS communes AS
        SELECT
            code_commune,
            nom_commune,
            departement,
            region,
            ROUND(score_potentiel, 2)               AS score_potentiel,
            nb_coproprietes,
            ROUND(taille_moy_copro, 1)              AS taille_moy_copro,
            ROUND(taux_motorisation, 3)             AS taux_motorisation,
            ROUND(part_appartements, 3)             AS part_appartements,
            ROUND(indice_concentration_syndic, 3)   AS indice_concentration_syndic,
            ROUND(part_hlm, 3)                      AS part_hlm,
            syndic_dominant,
            nb_lots_stationnement,

            -- Colonne calculée : catégorie du score
            CASE
                WHEN score_potentiel >= 66 THEN 'Élevé'
                WHEN score_potentiel >= 33 THEN 'Moyen'
                ELSE 'Faible'
            END AS score_category,

            -- Colonne calculée : rang national
            ROW_NUMBER() OVER (ORDER BY score_potentiel DESC) AS rang_national

        FROM raw_communes
        WHERE
            score_potentiel IS NOT NULL
            AND nom_commune IS NOT NULL
    """)
    print("✅ Table communes (transformée) créée")


    # TABLE 3a — KPI : Top 20 zones prioritaires

    con.execute("""
        CREATE TABLE IF NOT EXISTS kpi_top20 AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY score_potentiel DESC) AS rang,
            code_commune,
            nom_commune,
            region,
            ROUND(score_potentiel, 2)               AS score_potentiel,
            nb_coproprietes,
            syndic_dominant,
            ROUND(part_hlm, 3)                      AS part_hlm,
            ROUND(indice_concentration_syndic, 3)   AS indice_concentration_syndic
        FROM communes
        ORDER BY score_potentiel DESC
        LIMIT 20
    """)
    print("✅ Table kpi_top20 créée")


    # TABLE 3b — KPI : Agrégats par région
 
    con.execute("""
        CREATE TABLE IF NOT EXISTS kpi_par_region AS
        SELECT
            region,
            ROUND(AVG(score_potentiel), 2)              AS score_moyen,
            COUNT(*)                                     AS nb_communes,
            SUM(nb_coproprietes)                        AS nb_coproprietes_total,
            ROUND(AVG(part_hlm), 3)                     AS part_hlm_moyenne,
            ROUND(AVG(indice_concentration_syndic), 3)  AS indice_syndic_moyen
        FROM communes
        GROUP BY region
        ORDER BY score_moyen DESC
    """)
    print("✅ Table kpi_par_region créée")

    con.close()
    print("\n🎉 Base de données initialisée avec succès")



# Fonctions utilitaires appelées par main.py


def get_communes(region: str = None, score_min: float = 0, score_max: float = 100, syndic: str = None):
    """
    Retourne les communes avec filtres dynamiques.
    Utilisée par la route GET /api/communes
    """
    con = get_connection()

    query = """
        SELECT *
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

    query += " ORDER BY score_potentiel DESC"

    result = con.execute(query, params).df()
    con.close()
    return result


def get_top20():
    """Retourne le classement Top 20. Utilisée par GET /api/top20"""
    con = get_connection()
    result = con.execute("SELECT * FROM kpi_top20 ORDER BY rang").df()
    con.close()
    return result


def get_stats_par_region():
    """Retourne les agrégats par région. Utilisée par GET /api/stats"""
    con = get_connection()
    result = con.execute("SELECT * FROM kpi_par_region ORDER BY score_moyen DESC").df()
    con.close()
    return result


def get_filtres_disponibles():
    """Retourne les valeurs uniques pour les filtres du dashboard."""
    con = get_connection()
    regions = con.execute("SELECT DISTINCT region FROM communes ORDER BY region").df()["region"].tolist()
    syndics = con.execute("SELECT DISTINCT syndic_dominant FROM communes WHERE syndic_dominant IS NOT NULL ORDER BY syndic_dominant").df()["syndic_dominant"].tolist()
    con.close()
    return {"regions": regions, "syndics": syndics}



# Point d'entrée — test rapide

if __name__ == "__main__":
    init_db()
    con = get_connection()
    print("\n📊 Aperçu raw_communes :")
    print(con.execute("SELECT * FROM raw_communes LIMIT 3").df())
    print("\n📊 Aperçu kpi_top20 :")
    print(con.execute("SELECT * FROM kpi_top20").df())
    print("\n📊 Aperçu kpi_par_region :")
    print(con.execute("SELECT * FROM kpi_par_region").df())
    con.close()