"""
main.py — Parkshare
Serveur FastAPI — routes API + service des fichiers statiques
"""

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

from database import init_db, get_communes, get_filtres_disponibles
from carte import get_geojson_complet, get_geojson_filtre, get_stats_carte
from classement import get_top20, get_classement_filtre, get_resume_classement
from graphiques import (
    get_stats_par_region,
    get_scatter_hlm_score,
    get_concentration_syndic_top15,
    get_distribution_scores
)

# ----------------------------------------------------------------
# Initialisation
# ----------------------------------------------------------------
app = FastAPI(title="Parkshare Dashboard API")

BASE_DIR   = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")

@app.on_event("startup")
def startup():
    print("🚀 Démarrage — initialisation de la base de données...")
    init_db()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ----------------------------------------------------------------
# Pages HTML
# ----------------------------------------------------------------
@app.get("/")
def root():
    """Page storytelling — rapport"""
    return FileResponse(os.path.join(STATIC_DIR, "rapport.html"))

@app.get("/dashboard")
def dashboard():
    """Dashboard interactif"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ----------------------------------------------------------------
# ROUTE 1 — Communes avec filtres dynamiques
# ----------------------------------------------------------------
@app.get("/api/communes")
def api_communes(
    region:    str   = Query(default=None),
    score_min: float = Query(default=0),
    score_max: float = Query(default=100),
    syndic:    str   = Query(default=None)
):
    df = get_communes(
        region=region,
        score_min=score_min,
        score_max=score_max,
        syndic=syndic
    )
    return JSONResponse(content=df.to_dict(orient="records"))


# ----------------------------------------------------------------
# ROUTE 2 — GeoJSON complet pour la carte
# ----------------------------------------------------------------
@app.get("/api/geojson")
def api_geojson():
    try:
        data = get_geojson_complet()
        return JSONResponse(content=data)
    except FileNotFoundError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})


# ----------------------------------------------------------------
# ROUTE 3 — GeoJSON filtré dynamiquement
# ----------------------------------------------------------------
@app.get("/api/geojson/filtre")
def api_geojson_filtre(
    region:    str   = Query(default=None),
    score_min: float = Query(default=0),
    score_max: float = Query(default=100),
    syndic:    str   = Query(default=None)
):
    data = get_geojson_filtre(
        region=region,
        score_min=score_min,
        score_max=score_max,
        syndic=syndic
    )
    return JSONResponse(content=data)


# ----------------------------------------------------------------
# ROUTE 4 — Statistiques globales carte
# ----------------------------------------------------------------
@app.get("/api/carte/stats")
def api_carte_stats():
    return JSONResponse(content=get_stats_carte())


# ----------------------------------------------------------------
# ROUTE 5 — Top 20 zones prioritaires
# ----------------------------------------------------------------
@app.get("/api/top20")
def api_top20():
    return JSONResponse(content=get_top20())


# ----------------------------------------------------------------
# ROUTE 6 — Classement filtré dynamiquement
# ----------------------------------------------------------------
@app.get("/api/classement")
def api_classement(
    region:    str   = Query(default=None),
    score_min: float = Query(default=0),
    score_max: float = Query(default=100),
    syndic:    str   = Query(default=None),
    limit:     int   = Query(default=20)
):
    data = get_classement_filtre(
        region=region,
        score_min=score_min,
        score_max=score_max,
        syndic=syndic,
        limit=limit
    )
    return JSONResponse(content=data)


# ----------------------------------------------------------------
# ROUTE 7 — Résumé Top 3 pour le storytelling
# ----------------------------------------------------------------
@app.get("/api/classement/resume")
def api_classement_resume():
    return JSONResponse(content=get_resume_classement())


# ----------------------------------------------------------------
# ROUTE 8 — Agrégats par région
# ----------------------------------------------------------------
@app.get("/api/stats")
def api_stats():
    return JSONResponse(content=get_stats_par_region())


# ----------------------------------------------------------------
# ROUTE 9 — Scatter HLM vs Score
# ----------------------------------------------------------------
@app.get("/api/graphiques/scatter")
def api_scatter():
    return JSONResponse(content=get_scatter_hlm_score())


# ----------------------------------------------------------------
# ROUTE 10 — Concentration syndic Top 15
# ----------------------------------------------------------------
@app.get("/api/graphiques/syndic")
def api_syndic():
    return JSONResponse(content=get_concentration_syndic_top15())


# ----------------------------------------------------------------
# ROUTE 11 — Distribution des scores
# ----------------------------------------------------------------
@app.get("/api/graphiques/distribution")
def api_distribution():
    return JSONResponse(content=get_distribution_scores())


# ----------------------------------------------------------------
# ROUTE 12 — Filtres disponibles pour les dropdowns
# ----------------------------------------------------------------
@app.get("/api/filtres")
def api_filtres():
    return JSONResponse(content=get_filtres_disponibles())


# ----------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)