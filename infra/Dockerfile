# Dockerfile pour chall48h-25-26 (Python + Uvicorn)
FROM python:3.12-slim

# Dossier de travail dans le container
WORKDIR /usr/src/app

# Copier le contenu du dossier app
COPY app/ .

# Installer les dépendances si requirements.txt existe
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Expose le port utilisé par uvicorn
EXPOSE 8000

# Lancer main.py via uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
